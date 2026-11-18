"""Small, inspectable vector-similarity search."""

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


Vector = tuple[float, ...]


@dataclass(frozen=True)
class VectorRecord:
    """A piece of text and the vector representing it."""

    record_id: int
    text: str
    vector: Vector
    document_id: str = "single-document"
    document_name: str = "Unknown document"
    source_path: str | None = None
    page_number: int | None = None
    section: str | None = None


@dataclass(frozen=True)
class VectorSearchResult:
    """A vector record returned by similarity search."""

    record: VectorRecord
    score: float


def cosine_similarity(first: Sequence[float], second: Sequence[float]) -> float:
    """Return the cosine similarity between two vectors."""

    if len(first) != len(second):
        raise ValueError("vectors must have the same dimension")

    first_length = math.sqrt(sum(value * value for value in first))
    second_length = math.sqrt(sum(value * value for value in second))

    if first_length == 0 or second_length == 0:
        raise ValueError("cosine similarity is undefined for a zero vector")

    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(first, second)
    )

    return dot_product / (first_length * second_length)


class VectorIndex:
    """An in-memory index that ranks records by cosine similarity."""

    def __init__(self, records: Iterable[VectorRecord]) -> None:
        self.records = tuple(records)

        if not self.records:
            self.dimension = None
            return

        self.dimension = len(self.records[0].vector)

        if self.dimension == 0:
            raise ValueError("vectors must contain at least one value")

        for record in self.records:
            if len(record.vector) != self.dimension:
                raise ValueError("all indexed vectors must have the same dimension")

    def search(
        self,
        query_vector: Sequence[float],
        limit: int = 5,
        minimum_similarity: float | None = None,
    ) -> list[VectorSearchResult]:
        """Return the records most similar to a query vector."""

        if limit <= 0 or not self.records:
            return []

        if self.dimension is None:
            return []

        if len(query_vector) != self.dimension:
            raise ValueError("query vector has the wrong dimension")

        scored_records = [
            VectorSearchResult(
                record=record,
                score=cosine_similarity(query_vector, record.vector),
            )
            for record in self.records
        ]

        if minimum_similarity is not None:
            scored_records = [
                result
                for result in scored_records
                if result.score > minimum_similarity
            ]

        scored_records.sort(
            key=lambda result: (-result.score, result.record.record_id)
        )

        return scored_records[:limit]
