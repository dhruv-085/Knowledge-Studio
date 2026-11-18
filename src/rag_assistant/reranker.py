"""A small, inspectable second-stage passage reranker."""

from dataclasses import dataclass
import re
from typing import Sequence

from .hybrid_search import HybridSearchResult
from .keyword_search import Passage


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "can",
        "does",
        "for",
        "how",
        "in",
        "is",
        "it",
        "may",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "when",
        "which",
        "without",
    }
)


@dataclass(frozen=True)
class RerankedResult:
    """A candidate passage with its second-stage relevance score."""

    passage: Passage
    reranker_score: float
    first_stage_score: float
    methods: tuple[str, ...]
    matched_terms: tuple[str, ...]


def _content_terms(text: str) -> tuple[str, ...]:
    """Return unique non-stopword terms while preserving input order."""

    terms = [
        term
        for term in TOKEN_PATTERN.findall(text.lower())
        if term not in STOP_WORDS
    ]
    return tuple(dict.fromkeys(terms))


def reranker_score(query: str, passage: str) -> tuple[float, tuple[str, ...]]:
    """Score a query-passage pair using transparent lexical evidence.

    The score is not a probability. It is only useful for ordering the
    already-retrieved candidates.
    """

    query_terms = set(_content_terms(query))
    passage_terms = set(_content_terms(passage))
    matched_terms = tuple(sorted(query_terms.intersection(passage_terms)))

    if not query_terms:
        return 0.0, matched_terms

    overlap_score = len(matched_terms) / len(query_terms)
    exact_identifier_bonus = sum(
        0.25
        for term in matched_terms
        if "_" in term or any(character.isdigit() for character in term)
    )

    return overlap_score + exact_identifier_bonus, matched_terms


def rerank(
    query: str,
    candidates: Sequence[HybridSearchResult],
    limit: int = 5,
) -> list[RerankedResult]:
    """Rerank only the supplied first-stage candidates."""

    if limit <= 0:
        return []

    scored_candidates = []

    for candidate in candidates:
        score, matched_terms = reranker_score(query, candidate.passage.text)
        scored_candidates.append(
            RerankedResult(
                passage=candidate.passage,
                reranker_score=score,
                first_stage_score=candidate.score,
                methods=candidate.methods,
                matched_terms=matched_terms,
            )
        )

    scored_candidates.sort(
        key=lambda result: (
            -result.reranker_score,
            -result.first_stage_score,
            result.passage.passage_id,
        )
    )
    return scored_candidates[:limit]
