"""Explicit BM25 lexical search over searchable passages."""

from collections import Counter
from dataclasses import dataclass
from math import log
from typing import Iterable

from .keyword_search import (
    LEXICAL_STOPWORDS,
    Passage,
    SearchResult,
    tokenize,
)


@dataclass(frozen=True)
class BM25Parameters:
    """The two tunable BM25 parameters."""

    k1: float = 1.5
    b: float = 0.75


class BM25Index:
    """In-memory BM25 index using the project's guarded lexical vocabulary."""

    def __init__(
        self,
        passages: Iterable[Passage],
        parameters: BM25Parameters = BM25Parameters(),
    ) -> None:
        if parameters.k1 < 0:
            raise ValueError("k1 must not be negative")
        if not 0 <= parameters.b <= 1:
            raise ValueError("b must be between 0 and 1")

        self.passages = tuple(passages)
        self.passages_by_id = {
            passage.passage_id: passage for passage in self.passages
        }
        self.parameters = parameters
        self.term_counts: dict[int, Counter[str]] = {}
        self.document_frequency: Counter[str] = Counter()
        self.document_lengths: dict[int, int] = {}

        for passage in self.passages:
            terms = self._content_terms(passage.text)
            counts = Counter(terms)
            self.term_counts[passage.passage_id] = counts
            self.document_lengths[passage.passage_id] = len(terms)
            self.document_frequency.update(counts.keys())

        total_length = sum(self.document_lengths.values())
        self.average_document_length = (
            total_length / len(self.passages) if self.passages else 0.0
        )

    @staticmethod
    def _content_terms(text: str) -> list[str]:
        return [term for term in tokenize(text) if term not in LEXICAL_STOPWORDS]

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Return the highest-scoring passages for a guarded lexical query."""

        if limit <= 0:
            return []

        query_terms = tuple(
            dict.fromkeys(self._content_terms(query))
        )
        if not query_terms or not self.passages:
            return []

        number_of_documents = len(self.passages)
        scores: dict[int, float] = {}
        matched_terms: dict[int, list[str]] = {}

        for passage_id, counts in self.term_counts.items():
            document_length = self.document_lengths[passage_id]
            score = 0.0
            matched: list[str] = []

            for term in query_terms:
                term_frequency = counts.get(term, 0)
                if term_frequency == 0:
                    continue

                matched.append(term)
                document_frequency = self.document_frequency[term]
                inverse_document_frequency = log(
                    1
                    + (number_of_documents - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )

                length_factor = (
                    1
                    - self.parameters.b
                    + self.parameters.b
                    * document_length
                    / self.average_document_length
                )
                term_frequency_factor = (
                    term_frequency * (self.parameters.k1 + 1)
                    / (term_frequency + self.parameters.k1 * length_factor)
                )
                score += inverse_document_frequency * term_frequency_factor

            if matched:
                scores[passage_id] = score
                matched_terms[passage_id] = matched

        ranked_ids = sorted(
            scores,
            key=lambda passage_id: (-scores[passage_id], passage_id),
        )

        return [
            SearchResult(
                passage=self.passages_by_id[passage_id],
                score=scores[passage_id],
                matched_terms=tuple(matched_terms[passage_id]),
            )
            for passage_id in ranked_ids[:limit]
        ]
