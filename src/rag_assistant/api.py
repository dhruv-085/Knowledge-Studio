"""Stateless HTTP API for parsing documents and answering grounded questions."""

from collections import defaultdict, deque
from dataclasses import dataclass
import logging
from ipaddress import ip_address
from pathlib import Path
from threading import Lock
from time import monotonic
from uuid import uuid4
import os

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.responses import JSONResponse

from .document_loader import load_document, load_pdf_document
from .embeddings import PretrainedSentenceEncoder
from .multi_document_rag import DocumentInput, MultiDocumentRagPipeline
from .conversation import ConversationMessage
from .query_reformulation import reformulate_query
from .generator import ExtractiveProvider
from .gemini_provider import GeminiProvider


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = MAX_UPLOAD_BYTES + 1_000_000
MAX_DOCUMENTS = 10
MAX_DOCUMENT_CHARS = 800_000
MAX_TOTAL_DOCUMENT_CHARS = 800_000
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CHARS = 20_000
MAX_QUESTIONS_PER_MINUTE = 10
MAX_REQUEST_BYTES = 8_000_000
SHORT_TECHNICAL_TERMS = {"ai", "ml", "rag", "api", "sql", "pdf", "llm"}
logger = logging.getLogger(__name__)


def looks_like_accidental_input(question: str) -> bool:
    words = [word.lower() for word in question.split() if any(char.isalnum() for char in word)]
    if not words or len(question) > 4000:
        return True
    if all(len(word) <= 2 and word not in SHORT_TECHNICAL_TERMS for word in words):
        return True
    return len(words) > 1 and len(set(words)) == 1


class PageText(BaseModel):
    page_number: int = Field(ge=1)
    text: str = Field(max_length=MAX_DOCUMENT_CHARS)


class DocumentPayload(BaseModel):
    document_id: str = Field(min_length=1, max_length=100)
    document_name: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=MAX_DOCUMENT_CHARS)
    page_texts: list[PageText] = Field(default_factory=list, max_length=2000)

    @model_validator(mode="after")
    def bounded_page_text(self) -> "DocumentPayload":
        if sum(len(page.text) for page in self.page_texts) > MAX_DOCUMENT_CHARS:
            raise ValueError("a document's combined PDF page text exceeds the 800,000 character limit")
        return self


class HistoryMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str) -> str:
        if value not in {"user", "assistant"}:
            raise ValueError("history role must be user or assistant")
        return value


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=3, ge=1, le=20)
    conversation_id: str = Field(default_factory=lambda: str(uuid4()), max_length=100)
    documents: list[DocumentPayload] = Field(min_length=1, max_length=MAX_DOCUMENTS)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)

    @model_validator(mode="after")
    def bounded_content(self) -> "ChatRequest":
        if sum(len(document.text) for document in self.documents) > MAX_TOTAL_DOCUMENT_CHARS:
            raise ValueError("combined document text exceeds the 800,000 character limit")
        if sum(len(page.text) for document in self.documents for page in document.page_texts) > MAX_TOTAL_DOCUMENT_CHARS:
            raise ValueError("combined PDF page text exceeds the 800,000 character limit")
        if sum(len(message.content) for message in self.history) > MAX_HISTORY_CHARS:
            raise ValueError("recent conversation history exceeds the 20,000 character limit")
        return self


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
    status: str = "ready"
    page_count: int | None
    text: str
    page_texts: list[PageText]


@dataclass
class _RateLimiter:
    """Small in-process IP window; it stores no document or conversation data."""
    requests: dict[str, deque[float]]
    lock: Lock

    def allow(self, key: str) -> bool:
        now = monotonic()
        with self.lock:
            if len(self.requests) > 10_000:
                for address, bucket in list(self.requests.items()):
                    while bucket and now - bucket[0] >= 60:
                        bucket.popleft()
                    if not bucket:
                        del self.requests[address]
            recent = self.requests.setdefault(key, deque())
            while recent and now - recent[0] >= 60:
                recent.popleft()
            if len(recent) >= MAX_QUESTIONS_PER_MINUTE:
                return False
            recent.append(now)
            return True


def _document_input(payload: DocumentPayload) -> DocumentInput:
    return DocumentInput(
        document_id=payload.document_id,
        document_name=payload.document_name,
        text=payload.text,
        page_texts=tuple((page.page_number, page.text) for page in payload.page_texts),
    )


def create_app(document_path: Path | None = None, *, database_path: Path | None = None) -> FastAPI:
    """Create the stateless API. Legacy arguments are accepted but never persisted."""
    del database_path  # Kept temporarily so older local callers fail neither import nor startup.
    app = FastAPI(title="Technical Knowledge Assistant", version="1.0.0")
    origins = [origin.strip() for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.state.rate_limiter = _RateLimiter(defaultdict(deque), Lock())
    app.state.encoder = None
    app.state.encoder_lock = Lock()
    if document_path is not None and document_path.is_file():
        # Development convenience only; the source is returned to clients via /sample.
        app.state.sample_document = load_document(document_path, document_id=document_path.stem)
    else:
        app.state.sample_document = None

    @app.middleware("http")
    async def bound_request_size(request: Request, call_next):
        length = request.headers.get("content-length")
        if length:
            try:
                content_length = int(length)
            except ValueError:
                return JSONResponse({"detail": "invalid Content-Length header"}, status_code=400)
            if request.url.path == "/chat" and content_length > MAX_REQUEST_BYTES:
                return JSONResponse({"detail": "chat request exceeds the 8 MB limit"}, status_code=413)
            if request.url.path == "/documents" and content_length > MAX_UPLOAD_REQUEST_BYTES:
                return JSONResponse({"detail": "upload request exceeds the 21 MiB limit"}, status_code=413)
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/documents", response_model=DocumentResponse, status_code=201)
    async def parse_document(file: UploadFile = File(...)) -> DocumentResponse:
        filename = Path(file.filename or "").name
        suffix = Path(filename).suffix.lower()
        if suffix not in {".txt", ".md", ".markdown", ".pdf"}:
            raise HTTPException(status_code=415, detail="supported file types are PDF, TXT, MD, and MARKDOWN")
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="file exceeds the 20 MiB upload limit")
        document_id = str(uuid4())
        try:
            if suffix == ".pdf":
                document = load_pdf_document(filename, content, document_id=document_id)
            else:
                text = content.decode("utf-8")
                if not text.strip():
                    raise ValueError("document text must not be empty")
                document = DocumentInput(document_id=document_id, document_name=filename, text=text)
        except (UnicodeDecodeError, OSError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if len(document.text) > MAX_DOCUMENT_CHARS:
            raise HTTPException(status_code=413, detail="extracted text exceeds the 800,000 character limit")
        if sum(len(text) for _, text in document.page_texts) > MAX_DOCUMENT_CHARS:
            raise HTTPException(status_code=413, detail="combined PDF page text exceeds the 800,000 character limit")
        pages = [PageText(page_number=number, text=text) for number, text in document.page_texts]
        return DocumentResponse(
            document_id=document.document_id,
            filename=filename,
            file_type=suffix.lstrip("."),
            page_count=len(pages) if pages else None,
            text=document.text,
            page_texts=pages,
        )

    @app.get("/sample")
    def sample_document() -> dict[str, object]:
        document = app.state.sample_document
        if document is None:
            raise HTTPException(status_code=404, detail="no sample document configured")
        return {"document_id": document.document_id, "document_name": document.document_name,
                "text": document.text, "page_texts": document.page_texts}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
        question = request.question.strip()
        if looks_like_accidental_input(question):
            raise HTTPException(status_code=422, detail="That message looks incomplete. Please enter a question with a little more detail.")
        client_host = http_request.client.host if http_request.client else "unknown"
        forwarded_ip = http_request.headers.get("cf-connecting-ip")
        if forwarded_ip:
            try:
                client_host = ip_address(forwarded_ip.strip()).compressed
            except ValueError:
                pass
        if not app.state.rate_limiter.allow(client_host):
            raise HTTPException(status_code=429, detail="This service has reached 10 questions in one minute. Please wait before trying again.")
        documents = [_document_input(item) for item in request.documents]
        history = tuple((item.role, item.content) for item in request.history)
        conversation_messages = tuple(ConversationMessage(role=item.role, text=item.content)
                                      for item in request.history) + (ConversationMessage(role="user", text=question),)
        retrieval_query = reformulate_query(conversation_messages, question)
        try:
            if app.state.encoder is None:
                with app.state.encoder_lock:
                    if app.state.encoder is None:
                        app.state.encoder = PretrainedSentenceEncoder()
            try:
                provider = GeminiProvider()
            except ValueError:
                provider = ExtractiveProvider()
            response = MultiDocumentRagPipeline(
                max_passages=request.limit,
                embedder=app.state.encoder,
                provider=provider,
            ).answer(documents, question, retrieval_query=retrieval_query, conversation_history=history)
        except Exception as error:
            logger.error("RAG request failed (%s)", type(error).__name__)
            raise HTTPException(status_code=503, detail="The assistant could not process this request. Please try again shortly.") from error
        return ChatResponse(
            conversation_id=request.conversation_id,
            question=question,
            answer=response.answer.text,
            refused=response.answer.refused,
            passage_ids=list(response.answer.passage_ids),
            citations=[CitationResponse(**citation.__dict__) for citation in response.answer.citations],
            retrieved_evidence=[{
                "passage_id": item.passage_id, "text": item.text, "score": item.score,
                "score_name": item.score_name, "document_id": item.document_id,
                "document_name": item.document_name, "source_path": item.source_path,
                "page_number": item.page_number, "section": item.section,
            } for item in response.context.evidence],
        )

    return app


app = create_app()
