"""HTTP API for uploading technical documents and asking grounded questions."""

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .document_loader import load_document, load_pdf_document
from .embeddings import PretrainedSentenceEncoder
from .conversation_store import SQLiteConversationStore
from .document_store import SQLiteDocumentStore
from .multi_document_rag import DocumentInput, MultiDocumentRagPipeline
from .conversation import ConversationMessage
from .query_reformulation import reformulate_query
from .generator import ExtractiveProvider
from .gemini_provider import GeminiProvider


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_QUESTIONS_PER_MINUTE = 10
SHORT_TECHNICAL_TERMS = {"ai", "ml", "rag", "api", "sql", "pdf", "llm"}


def looks_like_accidental_input(question: str) -> bool:
    """Reject empty/no-signal text locally while allowing terse technical queries."""
    words = [word.lower() for word in question.split() if any(char.isalnum() for char in word)]
    if not words or len(question) > 4000:
        return True
    if all(len(word) <= 2 and word not in SHORT_TECHNICAL_TERMS for word in words):
        return True
    return len(words) > 1 and len(set(words)) == 1


def utc_timestamp(value: str) -> str:
    """Mark SQLite's UTC timestamp as ISO UTC for unambiguous browser parsing."""
    return value.replace(" ", "T", 1) + "Z" if "T" not in value else value


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=20)
    conversation_id: str | None = None


class CitationResponse(BaseModel):
    document_id: str
    document_name: str
    source_path: str | None
    page_number: int | None
    section: str | None
    passage_id: int


class ChatResponse(BaseModel):
    conversation_id: str
    question: str
    answer: str
    refused: bool
    passage_ids: list[int]
    citations: list[CitationResponse]
    retrieved_evidence: list[dict[str, object]]


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    page_count: int | None


class ConversationResponse(BaseModel):
    conversation_id: str
    created_at: str | None = None
    first_message: str | None = None


class MessageResponse(BaseModel):
    message_id: int
    conversation_id: str
    role: str
    content: str
    created_at: str
    citations: list[dict[str, object]] = Field(default_factory=list)
    retrieved_evidence: list[dict[str, object]] = Field(default_factory=list)
    refused: bool = False


@dataclass(frozen=True)
class StoredDocument:
    document: DocumentInput
    filename: str
    file_type: str
    page_count: int | None

    def response(self) -> DocumentResponse:
        return DocumentResponse(
            document_id=self.document.document_id,
            filename=self.filename,
            file_type=self.file_type,
            status="ready",
            page_count=self.page_count,
        )


def create_app(
    document_path: Path | None = None,
    *,
    database_path: Path | None = None,
) -> FastAPI:
    """Create an API backed by a local SQLite document collection."""

    app = FastAPI(title="Technical Knowledge Assistant")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if database_path is None:
        database_path = Path("data/assistant.sqlite3")
    store = SQLiteDocumentStore(database_path)
    conversation_store = SQLiteConversationStore(database_path)
    app.state.document_store = store
    app.state.conversation_store = conversation_store

    if document_path is not None and document_path.is_file():
        sample = load_document(document_path, document_id=document_path.stem)
        store.save(
            sample,
            filename=document_path.name,
            file_type=document_path.suffix.lower().lstrip("."),
            page_count=None,
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/conversations", response_model=ConversationResponse, status_code=201)
    def create_conversation() -> ConversationResponse:
        conversation_id = str(uuid4())
        conversation_store.create_conversation(conversation_id)
        return ConversationResponse(conversation_id=conversation_id)

    @app.get(
        "/conversations/{conversation_id}/messages",
        response_model=list[MessageResponse],
    )
    def list_conversation_messages(conversation_id: str) -> list[MessageResponse]:
        if not conversation_store.conversation_exists(conversation_id):
            raise HTTPException(status_code=404, detail="conversation not found")
        return [MessageResponse(**{**message, "created_at": utc_timestamp(str(message["created_at"]))})
                for message in conversation_store.list_messages(conversation_id)]

    @app.get("/conversations", response_model=list[ConversationResponse])
    def list_conversations() -> list[ConversationResponse]:
        return [ConversationResponse(**{**item, "created_at": utc_timestamp(str(item["created_at"]))})
                for item in conversation_store.list_conversations()]

    @app.delete("/conversations/{conversation_id}", status_code=204)
    def delete_conversation(conversation_id: str) -> Response:
        if not conversation_store.delete_conversation(conversation_id):
            raise HTTPException(status_code=404, detail="conversation not found")
        return Response(status_code=204)

    @app.post("/documents", response_model=DocumentResponse, status_code=201)
    async def upload_document(
        file: UploadFile = File(...),
        conversation_id: str | None = Query(default=None),
    ) -> DocumentResponse:
        if conversation_id and not conversation_store.conversation_exists(conversation_id):
            raise HTTPException(status_code=404, detail="conversation not found")
        filename = Path(file.filename or "").name
        suffix = Path(filename).suffix.lower()
        if suffix not in {".txt", ".md", ".markdown", ".pdf"}:
            raise HTTPException(
                status_code=415,
                detail="supported file types are PDF, TXT, MD, and MARKDOWN",
            )

        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="file exceeds the 20 MiB upload limit")

        document_id = str(uuid4())
        source_path = f"/documents/{document_id}"
        try:
            if suffix == ".pdf":
                document = load_pdf_document(
                    filename,
                    content,
                    document_id=document_id,
                    source_path=source_path,
                )
                page_count = len(document.page_texts)
            else:
                text = content.decode("utf-8")
                if not text.strip():
                    raise ValueError("document text must not be empty")
                document = DocumentInput(
                    document_id=document_id,
                    document_name=filename,
                    text=text,
                    source_path=source_path,
                )
                page_count = None
        except (UnicodeDecodeError, OSError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        stored = StoredDocument(
            document=document,
            filename=filename,
            file_type=suffix.lstrip("."),
            page_count=page_count,
        )
        store.save(
            stored.document,
            filename=stored.filename,
            file_type=stored.file_type,
            page_count=stored.page_count,
        )
        if conversation_id:
            conversation_store.attach_document(conversation_id, stored.document.document_id)
        return stored.response()

    @app.get("/documents", response_model=list[DocumentResponse])
    def list_documents(conversation_id: str | None = None) -> list[DocumentResponse]:
        if conversation_id:
            if not conversation_store.conversation_exists(conversation_id):
                raise HTTPException(status_code=404, detail="conversation not found")
            rows = store.list_documents_by_ids(conversation_store.list_document_ids(conversation_id))
        else:
            rows = store.list_documents()
        return [
            DocumentResponse(
                document_id=str(row["document_id"]),
                filename=str(row["filename"]),
                file_type=str(row["file_type"]),
                status="ready",
                page_count=(
                    int(row["page_count"])
                    if row["page_count"] is not None
                    else None
                ),
            )
            for row in rows
        ]

    @app.get("/documents/{document_id}", response_model=DocumentResponse)
    def get_document(document_id: str) -> DocumentResponse:
        row = store.get_document(document_id)
        if row is None:
            raise HTTPException(status_code=404, detail="document not found")
        return DocumentResponse(
            document_id=str(row["document_id"]),
            filename=str(row["filename"]),
            file_type=str(row["file_type"]),
            status="ready",
            page_count=(
                int(row["page_count"]) if row["page_count"] is not None else None
            ),
        )

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        question = request.question.strip()
        if looks_like_accidental_input(question):
            raise HTTPException(status_code=422, detail="That message looks incomplete. Please enter a question with a little more detail.")
        conversation_id = request.conversation_id or str(uuid4())
        if request.conversation_id and not conversation_store.conversation_exists(
            conversation_id
        ):
            raise HTTPException(status_code=404, detail="conversation not found")

        if not request.conversation_id:
            conversation_store.create_conversation(conversation_id)
            documents = store.load_inputs()
            for document in documents:
                conversation_store.attach_document(conversation_id, document.document_id)
        else:
            document_ids = conversation_store.list_document_ids(conversation_id)
            documents = store.load_inputs_by_ids(document_ids)
        if not documents:
            raise HTTPException(status_code=409, detail="upload a document to this conversation before asking a question")

        if conversation_store.count_recent_user_messages(conversation_id) >= MAX_QUESTIONS_PER_MINUTE:
            raise HTTPException(status_code=429, detail="This chat has reached 10 questions in one minute. Please wait a moment before trying again.")

        saved_messages = conversation_store.list_messages(conversation_id)
        history_rows = saved_messages[-12:]
        history = tuple((str(row["role"]), str(row["content"])) for row in history_rows)
        conversation_messages = tuple(
            ConversationMessage(role=str(row["role"]), text=str(row["content"]))
            for row in history_rows
        ) + (ConversationMessage(role="user", text=question),)
        search_query = reformulate_query(conversation_messages, question)
        conversation_store.add_message(conversation_id, "user", question)

        try:
            try:
                provider = GeminiProvider()
            except ValueError:
                provider = ExtractiveProvider()
            response = MultiDocumentRagPipeline(
                max_passages=request.limit,
                embedder=PretrainedSentenceEncoder(),
                provider=provider,
            ).answer(
                documents,
                question,
                retrieval_query=search_query,
                conversation_history=history,
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        conversation_store.add_message(
            conversation_id,
            "assistant",
            response.answer.text,
            metadata={
                "refused": response.answer.refused,
                "citations": [citation.__dict__ for citation in response.answer.citations],
                "retrieved_evidence": [
                    {
                        "passage_id": item.passage_id,
                        "text": item.text,
                        "score": item.score,
                        "score_name": item.score_name,
                        "document_id": item.document_id,
                        "document_name": item.document_name,
                        "source_path": item.source_path,
                        "page_number": item.page_number,
                        "section": item.section,
                    }
                    for item in response.context.evidence
                ],
            },
        )

        return ChatResponse(
            conversation_id=conversation_id,
            question=question,
            answer=response.answer.text,
            refused=response.answer.refused,
            passage_ids=list(response.answer.passage_ids),
            citations=[CitationResponse(**citation.__dict__) for citation in response.answer.citations],
            retrieved_evidence=[
                {
                    "passage_id": item.passage_id,
                    "text": item.text,
                    "score": item.score,
                    "score_name": item.score_name,
                    "document_id": item.document_id,
                    "document_name": item.document_name,
                    "source_path": item.source_path,
                    "page_number": item.page_number,
                    "section": item.section,
                }
                for item in response.context.evidence
            ],
        )

    return app


app = create_app()
