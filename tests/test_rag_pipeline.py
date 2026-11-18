import pytest

from rag_assistant.generator import INSUFFICIENT_EVIDENCE
from rag_assistant.rag_pipeline import RagPipeline


DOCUMENT = """
The system terminates inactive sessions after 30 minutes.
Users must sign in again after a session expires.

Python uses indentation to define code blocks.
"""


def test_pipeline_answers_from_retrieved_evidence() -> None:
    response = RagPipeline().answer(
        DOCUMENT,
        "How long can I remain logged in without activity?",
    )

    assert not response.answer.refused
    assert "30 minutes" in response.answer.text
    assert response.answer.passage_ids == (1,)
    assert response.context.evidence[0].passage_id == 1


def test_pipeline_refuses_when_query_has_no_supported_evidence() -> None:
    response = RagPipeline().answer(
        DOCUMENT,
        "What is quantum computing?",
    )

    assert response.answer.refused
    assert response.answer.text == INSUFFICIENT_EVIDENCE
    assert response.answer.passage_ids == ()


def test_pipeline_rejects_empty_inputs() -> None:
    pipeline = RagPipeline()

    with pytest.raises(ValueError, match="document_text must not be empty"):
        pipeline.answer("", "What is RAG?")

    with pytest.raises(ValueError, match="question must not be empty"):
        pipeline.answer(DOCUMENT, " ")
