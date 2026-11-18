"""Build an evidence context from retrieved passages."""

from dataclasses import dataclass
from typing import Sequence

from .keyword_search import SearchResult
from .hybrid_search import HybridSearchResult
from .vector_search import VectorSearchResult


@dataclass(frozen=True)
class Evidence:
    """One retrieved passage that may support an answer."""

    passage_id: int
    text: str
    score: float
    score_name: str = "similarity"
    document_id: str = "single-document"
    document_name: str = "Unknown document"
    source_path: str | None = None
    page_number: int | None = None
    section: str | None = None


@dataclass(frozen=True)
class Citation:
    """Traceable source information for one piece of evidence."""

    document_id: str
    document_name: str
    source_path: str | None
    page_number: int | None
    section: str | None
    passage_id: int


@dataclass(frozen=True)
class RetrievalContext:
    """Evidence selected for answer generation."""

    evidence: tuple[Evidence, ...]

    @property
    def is_empty(self) -> bool:
        """Return True when no evidence was retrieved."""

        return not self.evidence

    def as_text(self) -> str:
        """Format evidence for an answer generator."""

        if self.is_empty:
            return "(No supporting evidence was retrieved.)"

        sections: list[str] = []

        for item in self.evidence:
            sections.append(
                f"[Passage {item.passage_id} | "
                f"{item.score_name}={item.score:.3f}]\n"
                f"{item.text}"
            )

        return "\n\n".join(sections)


def build_context(
    results: Sequence[VectorSearchResult],
    max_passages: int = 3,
) -> RetrievalContext:
    """Convert search results into a small evidence context."""

    if max_passages <= 0:
        raise ValueError("max_passages must be greater than zero")

    evidence = tuple(
        Evidence(
            passage_id=result.record.record_id,
            text=result.record.text,
            score=result.score,
            document_id=result.record.document_id,
            document_name=result.record.document_name,
            source_path=result.record.source_path,
            page_number=result.record.page_number,
            section=result.record.section,
        )
        for result in results[:max_passages]
    )

    return RetrievalContext(evidence=evidence)


def build_keyword_context(
    results: Sequence[SearchResult],
    max_passages: int = 3,
) -> RetrievalContext:
    """Convert keyword-search results into answer evidence."""

    if max_passages <= 0:
        raise ValueError("max_passages must be greater than zero")

    evidence = tuple(
        Evidence(
            passage_id=result.passage.passage_id,
            text=result.passage.text,
            score=float(result.score),
            score_name="term_score",
            document_id=result.passage.document_id,
            document_name=result.passage.document_name,
            source_path=result.passage.source_path,
            page_number=result.passage.page_number,
            section=result.passage.section,
        )
        for result in results[:max_passages]
    )

    return RetrievalContext(evidence=evidence)


def build_hybrid_context(
    results: Sequence[HybridSearchResult],
    max_passages: int = 3,
) -> RetrievalContext:
    """Convert fused retrieval results into answer evidence."""

    if max_passages <= 0:
        raise ValueError("max_passages must be greater than zero")

    evidence = tuple(
        Evidence(
            passage_id=result.passage.passage_id,
            text=result.passage.text,
            score=result.score,
            score_name="rrf_score",
            document_id=result.passage.document_id,
            document_name=result.passage.document_name,
            source_path=result.passage.source_path,
            page_number=result.passage.page_number,
            section=result.passage.section,
        )
        for result in results[:max_passages]
    )

    return RetrievalContext(evidence=evidence)
