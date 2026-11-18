from pytest import approx

from rag_assistant.embeddings import TeachingEmbedder
from rag_assistant.keyword_search import Passage
from rag_assistant.semantic_search import build_semantic_index


def test_semantic_index_retrieves_related_passage() -> None:
    passages = [
        Passage(
            1,
            "The system terminates inactive sessions after 30 minutes.",
        ),
        Passage(2, "Python uses indentation to define code blocks."),
    ]
    embedder = TeachingEmbedder()
    index, skipped_ids = build_semantic_index(passages, embedder)

    query_vector = embedder.embed(
        "How long can I remain logged in without activity?"
    )
    results = index.search(query_vector, limit=1)

    assert skipped_ids == ()
    assert results[0].record.record_id == 1
    assert results[0].score == approx(0.9486832980505138)


def test_semantic_index_reports_passages_without_known_concepts() -> None:
    passages = [Passage(1, "A completely unfamiliar sentence.")]

    index, skipped_ids = build_semantic_index(passages, TeachingEmbedder())

    assert index.search((1.0, 0.0, 0.0, 0.0, 0.0)) == []
    assert skipped_ids == (1,)


def test_semantic_index_preserves_source_metadata() -> None:
    passage = Passage(
        passage_id=1,
        text="The system terminates inactive sessions after 30 minutes.",
        document_id="auth-guide",
        document_name="Authentication Guide",
        source_path="data/raw/authentication.md",
        page_number=4,
        section="Session expiration",
    )

    embedder = TeachingEmbedder()
    index, skipped_ids = build_semantic_index([passage], embedder)
    results = index.search(
        embedder.embed("How long can a session remain inactive?"),
        limit=1,
    )

    assert skipped_ids == ()
    record = results[0].record
    assert record.record_id == 1
    assert record.document_id == "auth-guide"
    assert record.document_name == "Authentication Guide"
    assert record.source_path == "data/raw/authentication.md"
    assert record.page_number == 4
    assert record.section == "Session expiration"


class FakeEncoder:
    """A deterministic encoder used to test the encoder boundary."""

    def embed(self, text: str) -> tuple[float, ...]:
        if "session" in text.lower():
            return (1.0, 0.0)
        return (0.0, 1.0)


def test_semantic_index_accepts_an_encoder_other_than_the_teaching_embedder() -> None:
    passages = [
        Passage(1, "Session expiration evidence."),
        Passage(2, "Python evidence."),
    ]

    index, skipped_ids = build_semantic_index(passages, FakeEncoder())
    results = index.search(FakeEncoder().embed("session duration"), limit=1)

    assert skipped_ids == ()
    assert results[0].record.record_id == 1
