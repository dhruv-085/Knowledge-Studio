"""Multi-document grounded retrieval with traceable citations."""

from dataclasses import dataclass
from typing import Sequence

from .context_builder import (
    RetrievalContext,
    build_hybrid_context,
)
from .embeddings import TeachingEmbedder, TextEncoder
from .generator import GeneratedAnswer, GenerationProvider, GroundedGenerator
from .hybrid_search import reciprocal_rank_fusion
from .keyword_search import KeywordIndex, Passage, split_into_passages
from .semantic_search import build_semantic_index


@dataclass(frozen=True)
class DocumentInput:
    """One text document supplied to the ingestion step."""

    document_id: str
    document_name: str
    text: str
    source_path: str | None = None
    page_texts: tuple[tuple[int, str], ...] = ()


@dataclass(frozen=True)
class MultiDocumentResponse:
    """The observable result of a multi-document RAG request."""

    question: str
    context: RetrievalContext
    answer: GeneratedAnswer
    skipped_passage_ids: tuple[int, ...]


class MultiDocumentRagPipeline:
    """Index multiple documents and preserve their provenance."""

    def __init__(
        self,
        *,
        max_passages: int = 3,
        minimum_score: float = 0.1,
        embedder: TextEncoder | None = None,
        minimum_similarity: float = 0.0,
        provider: GenerationProvider | None = None,
    ) -> None:
        if max_passages <= 0:
            raise ValueError("max_passages must be greater than zero")

        self.max_passages = max_passages
        self.embedder = embedder or TeachingEmbedder()
        self.minimum_similarity = minimum_similarity
        self.generator = GroundedGenerator(
            minimum_score=minimum_score,
            provider=provider,
        )

    def _build_passages(
        self,
        documents: Sequence[DocumentInput],
    ) -> list[Passage]:
        """Split documents and assign globally unique passage IDs."""

        passages: list[Passage] = []
        next_passage_id = 1

        for document in documents:
            if not document.document_id.strip():
                raise ValueError("document_id must not be empty")
            if not document.document_name.strip():
                raise ValueError("document_name must not be empty")
            if not document.text.strip():
                raise ValueError(
                    f"document text must not be empty: {document.document_id}"
                )

            if document.page_texts:
                page_passages = [
                    (page_number, local_passage.text)
                    for page_number, page_text in document.page_texts
                    for local_passage in split_into_passages(page_text)
                ]
            else:
                page_passages = [
                    (None, local_passage.text)
                    for local_passage in split_into_passages(document.text)
                ]

            for page_number, passage_text in page_passages:
                passages.append(
                    Passage(
                        passage_id=next_passage_id,
                        text=passage_text,
                        document_id=document.document_id,
                        document_name=document.document_name,
                        source_path=document.source_path,
                        page_number=page_number,
                        section=None,
                    )
                )
                next_passage_id += 1

        if not passages:
            raise ValueError("documents must contain at least one passage")

        return passages

    def answer(
        self,
        documents: Sequence[DocumentInput],
        question: str,
        *,
        retrieval_query: str | None = None,
        conversation_history: tuple[tuple[str, str], ...] = (),
    ) -> MultiDocumentResponse:
        """Retrieve evidence across documents and produce a grounded response."""

        if not documents:
            raise ValueError("documents must not be empty")
        if not question.strip():
            raise ValueError("question must not be empty")

        passages = self._build_passages(documents)

        search_question = retrieval_query or question
        keyword_results = KeywordIndex(passages).search(
            search_question,
            limit=self.max_passages,
        )

        try:
            query_vector = self.embedder.embed(search_question)
        except ValueError:
            semantic_results = []
            skipped_ids = tuple(passage.passage_id for passage in passages)
        else:
            index, skipped_ids = build_semantic_index(passages, self.embedder)
            semantic_results = index.search(
                query_vector,
                limit=self.max_passages,
                minimum_similarity=self.minimum_similarity,
            )

        hybrid_results = reciprocal_rank_fusion(
            keyword_results,
            semantic_results,
            limit=self.max_passages,
        )
        context = build_hybrid_context(
            hybrid_results,
            max_passages=self.max_passages,
        )

        return MultiDocumentResponse(
            question=question,
            context=context,
            answer=self.generator.generate(question, context, conversation_history),
            skipped_passage_ids=skipped_ids,
        )
