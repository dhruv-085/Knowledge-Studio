from pytest import approx
import pytest

from rag_assistant.vector_search import (
    VectorIndex,
    VectorRecord,
    cosine_similarity,
)


def test_cosine_similarity_of_identical_vectors_is_one() -> None:
    assert cosine_similarity((1.0, 2.0), (1.0, 2.0)) == approx(1.0)


def test_cosine_similarity_of_orthogonal_vectors_is_zero() -> None:
    assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == approx(0.0)


def test_cosine_similarity_rejects_different_dimensions() -> None:
    with pytest.raises(ValueError, match="same dimension"):
        cosine_similarity((1.0, 0.0), (1.0, 0.0, 0.0))


def test_vector_index_returns_most_similar_records_first() -> None:
    records = [
        VectorRecord(1, "database passage", (1.0, 0.0)),
        VectorRecord(2, "python passage", (0.0, 1.0)),
        VectorRecord(3, "mixed passage", (0.8, 0.6)),
    ]

    index = VectorIndex(records)
    results = index.search((1.0, 0.0), limit=2)

    assert [result.record.record_id for result in results] == [1, 3]
    assert results[0].score == approx(1.0)
    assert results[1].score == approx(0.8)


def test_vector_index_can_exclude_non_similar_records() -> None:
    index = VectorIndex(
        [
            VectorRecord(1, "matching passage", (1.0, 0.0)),
            VectorRecord(2, "unrelated passage", (0.0, 1.0)),
        ]
    )

    results = index.search((1.0, 0.0), minimum_similarity=0.0)

    assert [result.record.record_id for result in results] == [1]


def test_vector_index_uses_record_id_to_break_ties() -> None:
    records = [
        VectorRecord(2, "second", (1.0, 0.0)),
        VectorRecord(1, "first", (1.0, 0.0)),
    ]

    results = VectorIndex(records).search((1.0, 0.0))

    assert [result.record.record_id for result in results] == [1, 2]


def test_vector_index_rejects_mismatched_record_dimensions() -> None:
    with pytest.raises(ValueError, match="same dimension"):
        VectorIndex(
            [
                VectorRecord(1, "first", (1.0, 0.0)),
                VectorRecord(2, "second", (1.0, 0.0, 0.0)),
            ]
        )


def test_vector_index_rejects_wrong_query_dimension() -> None:
    index = VectorIndex(
        [VectorRecord(1, "only record", (1.0, 0.0))]
    )

    with pytest.raises(ValueError, match="wrong dimension"):
        index.search((1.0, 0.0, 0.0))
