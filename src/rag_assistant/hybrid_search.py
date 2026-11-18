"""Combine keyword and semantic rankings with reciprocal rank fusion."""

from dataclasses import dataclass
from typing import Sequence

from .keyword_search import Passage, SearchResult
from .vector_search import VectorSearchResult


@dataclass(frozen=True)
class HybridSearchResult:
    """A passage ranked by one or both retrieval methods."""

    passage: Passage
    score: float
    methods: tuple[str, ...]


def reciprocal_rank_fusion(
    keyword_results: Sequence[SearchResult],
    semantic_results: Sequence[VectorSearchResult],
    limit: int = 5,
    rank_constant: int = 60,
) -> list[HybridSearchResult]:
    """Fuse two ranked lists using reciprocal rank fusion.

    A result at rank r contributes 1 / (rank_constant + r). Ranks start at 1.
    """

    if limit <= 0:
        return []
    if rank_constant < 0:
        raise ValueError("rank_constant must not be negative")

    passages: dict[int, Passage] = {}
    scores: dict[int, float] = {}
    methods: dict[int, list[str]] = {}

    for rank, result in enumerate(keyword_results, start=1):
        passage_id = result.passage.passage_id
        passages[passage_id] = result.passage
        scores[passage_id] = scores.get(passage_id, 0.0) + 1 / (
            rank_constant + rank
        )
        methods.setdefault(passage_id, []).append("keyword")

    for rank, result in enumerate(semantic_results, start=1):
        passage_id = result.record.record_id
        passage = Passage(
            passage_id=passage_id,
            text=result.record.text,
            document_id=result.record.document_id,
            document_name=result.record.document_name,
            source_path=result.record.source_path,
            page_number=result.record.page_number,
            section=result.record.section,
        )
        passages[passage_id] = passage
        scores[passage_id] = scores.get(passage_id, 0.0) + 1 / (
            rank_constant + rank
        )
        methods.setdefault(passage_id, []).append("semantic")

    ranked_ids = sorted(
        scores,
        key=lambda passage_id: (-scores[passage_id], passage_id),
    )

    return [
        HybridSearchResult(
            passage=passages[passage_id],
            score=scores[passage_id],
            methods=tuple(methods[passage_id]),
        )
        for passage_id in ranked_ids[:limit]
    ]
