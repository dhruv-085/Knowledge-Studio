from pytest import approx

from rag_assistant.context_builder import build_context
from rag_assistant.vector_search import VectorRecord, VectorSearchResult


def test_context_preserves_passage_ids_text_and_scores() -> None:
    results = [
        VectorSearchResult(
            record=VectorRecord(
                record_id=2,
                text="Sessions expire after inactivity.",
                vector=(1.0, 0.0),
            ),
            score=0.95,
        ),
    ]

    context = build_context(results)

    assert len(context.evidence) == 1
    assert context.evidence[0].passage_id == 2
    assert context.evidence[0].text == (
        "Sessions expire after inactivity."
    )
    assert context.evidence[0].score == approx(0.95)


def test_context_formats_evidence_for_generation() -> None:
    results = [
        VectorSearchResult(
            record=VectorRecord(
                record_id=1,
                text="Users must sign in again.",
                vector=(1.0, 0.0),
            ),
            score=0.8,
        ),
    ]

    context = build_context(results)

    assert "[Passage 1" in context.as_text()
    assert "similarity=0.800" in context.as_text()
    assert "Users must sign in again." in context.as_text()


def test_context_can_be_empty() -> None:
    context = build_context([])

    assert context.is_empty
    assert "No supporting evidence" in context.as_text()


def test_context_preserves_source_metadata() -> None:
    results = [
        VectorSearchResult(
            record=VectorRecord(
                record_id=4,
                text="Sessions expire after inactivity.",
                vector=(1.0, 0.0),
                document_id="auth-guide",
                document_name="Authentication Guide",
                source_path="data/raw/authentication.md",
                page_number=4,
                section="Session expiration",
            ),
            score=0.95,
        ),
    ]

    evidence = build_context(results).evidence[0]

    assert evidence.document_id == "auth-guide"
    assert evidence.document_name == "Authentication Guide"
    assert evidence.source_path == "data/raw/authentication.md"
    assert evidence.page_number == 4
    assert evidence.section == "Session expiration"
