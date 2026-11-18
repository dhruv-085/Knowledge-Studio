from rag_assistant.multi_document_rag import (
    DocumentInput,
    MultiDocumentRagPipeline,
)
from rag_assistant.embeddings import TeachingEmbedder


DOCUMENTS = (
    DocumentInput(
        document_id="auth-guide-v1",
        document_name="Authentication Guide v1",
        source_path="data/raw/authentication-v1.md",
        text=(
            "The system terminates inactive sessions after 30 minutes.\n\n"
            "Users must sign in again after a session expires."
        ),
    ),
    DocumentInput(
        document_id="auth-guide-v2",
        document_name="Authentication Guide v2",
        source_path="data/raw/authentication-v2.md",
        text=(
            "The service ends idle sessions after 30 minutes.\n\n"
            "Administrators can configure the session warning."
        ),
    ),
)


def test_similar_passages_keep_distinct_document_citations() -> None:
    response = MultiDocumentRagPipeline(max_passages=2).answer(
        DOCUMENTS,
        "How long can I remain logged in without activity?",
    )

    assert not response.answer.refused
    assert "30 minutes" in response.answer.text

    citations = response.answer.citations

    assert len(citations) == 2
    assert {citation.document_id for citation in citations} == {
        "auth-guide-v1",
        "auth-guide-v2",
    }
    assert {citation.document_name for citation in citations} == {
        "Authentication Guide v1",
        "Authentication Guide v2",
    }
    assert {citation.source_path for citation in citations} == {
        "data/raw/authentication-v1.md",
        "data/raw/authentication-v2.md",
    }
    assert len({citation.passage_id for citation in citations}) == 2


def test_multi_document_context_preserves_source_metadata() -> None:
    response = MultiDocumentRagPipeline(max_passages=1).answer(
        DOCUMENTS,
        "How long can I remain logged in without activity?",
    )

    evidence = response.context.evidence[0]

    assert evidence.document_id in {"auth-guide-v1", "auth-guide-v2"}
    assert evidence.document_name.startswith("Authentication Guide")
    assert evidence.source_path.endswith(".md")
    assert evidence.text


def test_zero_similarity_passages_are_not_added_to_context() -> None:
    document = DocumentInput(
        document_id="small-guide",
        document_name="Small Guide",
        text=(
            "The system terminates inactive sessions after 30 minutes.\n\n"
            "Python uses indentation to define code blocks."
        ),
    )

    response = MultiDocumentRagPipeline(
        max_passages=3,
        embedder=TeachingEmbedder(),
    ).answer(
        (document,),
        "How long can I remain logged in without activity?",
    )

    assert [evidence.passage_id for evidence in response.context.evidence] == [1]


def test_multi_document_pipeline_rejects_missing_input() -> None:
    pipeline = MultiDocumentRagPipeline()

    try:
        pipeline.answer((), "What is RAG?")
    except ValueError as error:
        assert str(error) == "documents must not be empty"
    else:
        raise AssertionError("empty documents should be rejected")


def test_pipeline_uses_keyword_fallback_for_exact_identifiers() -> None:
    documents = (
        DocumentInput(
            document_id="retry-guide",
            document_name="Retry Guide",
            text="MAX_RETRIES controls how many times a failed request may be attempted.",
        ),
    )

    response = MultiDocumentRagPipeline().answer(
        documents,
        "What does MAX_RETRIES control?",
    )

    assert not response.answer.refused
    assert response.context.evidence[0].score_name == "rrf_score"
    assert response.context.evidence[0].passage_id == 1
    assert "MAX_RETRIES" in response.answer.text


def test_pipeline_does_not_answer_from_a_generic_keyword_match() -> None:
    response = MultiDocumentRagPipeline().answer(
        DOCUMENTS,
        "What embedding model does this system use?",
    )

    assert response.answer.refused
