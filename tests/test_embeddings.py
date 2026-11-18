import pytest

from rag_assistant.embeddings import TeachingEmbedder


def test_embed_returns_a_fixed_dimension_vector() -> None:
    embedder = TeachingEmbedder()

    vector = embedder.embed("Users can remain logged in for 30 minutes.")

    assert len(vector) == embedder.dimension
    assert all(isinstance(value, float) for value in vector)


def test_embedding_is_deterministic() -> None:
    embedder = TeachingEmbedder()

    first_vector = embedder.embed("Database queries use tables.")
    second_vector = embedder.embed("Database queries use tables.")

    assert first_vector == second_vector


def test_related_wording_has_a_shared_representation() -> None:
    embedder = TeachingEmbedder()

    document_vector = embedder.embed(
        "The system terminates inactive sessions after 30 minutes."
    )
    query_vector = embedder.embed(
        "How long can I remain logged in without activity?"
    )

    assert document_vector[0] > 0
    assert query_vector[0] > 0
    assert document_vector[1] > 0
    assert query_vector[1] > 0


def test_unknown_text_is_rejected() -> None:
    embedder = TeachingEmbedder()

    with pytest.raises(ValueError, match="does not contain"):
        embedder.embed("A completely unrelated sentence.")
