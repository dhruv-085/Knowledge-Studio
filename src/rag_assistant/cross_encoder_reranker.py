"""Pretrained cross-encoder reranking for already-retrieved candidates."""

from typing import Any, Sequence

from .hybrid_search import HybridSearchResult
from .reranker import RerankedResult


DEFAULT_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"


def load_cross_encoder(model_name: str = DEFAULT_MODEL_NAME) -> Any:
    """Load a Sentence Transformers cross-encoder model.

    The import is local so the teaching reranker and its tests remain usable
    without loading a machine-learning model.
    """

    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


def rerank_with_cross_encoder(
    query: str,
    candidates: Sequence[HybridSearchResult],
    model: Any,
    limit: int = 5,
) -> list[RerankedResult]:
    """Score query-passage pairs with a pretrained cross-encoder."""

    if limit <= 0 or not candidates:
        return []

    pairs = [(query, candidate.passage.text) for candidate in candidates]
    scores = model.predict(pairs, show_progress_bar=False)

    scored_candidates = [
        RerankedResult(
            passage=candidate.passage,
            first_stage_score=candidate.score,
            methods=candidate.methods,
            reranker_score=float(score),
            matched_terms=(),
        )
        for candidate, score in zip(candidates, scores, strict=True)
    ]

    scored_candidates.sort(
        key=lambda result: (
            -result.reranker_score,
            -result.first_stage_score,
            result.passage.passage_id,
        )
    )
    return scored_candidates[:limit]
