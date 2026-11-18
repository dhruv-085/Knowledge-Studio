from rag_assistant.context_builder import Evidence, RetrievalContext
from rag_assistant.generator import (
    GROUNDING_INSTRUCTIONS,
    INSUFFICIENT_EVIDENCE,
    GroundedGenerator,
)


class RecordingProvider:
    def __init__(self) -> None:
        self.prompt = None

    def generate(self, prompt):
        self.prompt = prompt
        return "provider answer"


def test_generator_answers_from_retrieved_evidence() -> None:
    context = RetrievalContext(
        evidence=(
            Evidence(
                passage_id=2,
                text="Sessions expire after 30 minutes.",
                score=0.95,
            ),
        )
    )

    result = GroundedGenerator().generate(
        "How long can a session remain inactive?",
        context,
    )

    assert not result.refused
    assert "Sessions expire after 30 minutes." in result.text
    assert result.passage_ids == (2,)
    assert len(result.citations) == 1
    assert result.citations[0].passage_id == 2


def test_local_generator_returns_matching_sentence_with_its_source() -> None:
    context = RetrievalContext(
        evidence=(
            Evidence(
                passage_id=2,
                text=(
                    "Questions to try: What is the maximum supported upload size? "
                    "The assistant retrieves three passages by default."
                ),
                score=1 / 61,
                score_name="rrf_score",
                document_name="rag_sample_guide.pdf",
                page_number=2,
            ),
            Evidence(
                passage_id=1,
                text=(
                    "The service accepts text-based PDF, TXT, and Markdown files "
                    "up to 20 MiB. The parser extracts text one page at a time."
                ),
                score=1 / 62,
                score_name="rrf_score",
                document_name="rag_sample_guide.pdf",
                page_number=1,
            ),
        )
    )

    result = GroundedGenerator().generate(
        "How large can an uploaded document be?",
        context,
    )

    assert "files up to 20 MiB." in result.text
    assert "one page at a time" not in result.text
    assert "page 1" in result.text


def test_generator_refuses_when_evidence_is_missing() -> None:
    result = GroundedGenerator().generate(
        "What is quantum computing?",
        RetrievalContext(evidence=()),
    )

    assert result.refused
    assert result.text == INSUFFICIENT_EVIDENCE
    assert result.passage_ids == ()
    assert result.citations == ()


def test_generator_refuses_when_evidence_score_is_too_low() -> None:
    context = RetrievalContext(
        evidence=(
            Evidence(
                passage_id=3,
                text="Unrelated passage.",
                score=0.02,
            ),
        )
    )

    result = GroundedGenerator().generate(
        "What is RAG?",
        context,
    )

    assert result.refused
    assert result.passage_ids == ()
    assert result.citations == ()


def test_generator_accepts_positive_fused_retrieval_score() -> None:
    context = RetrievalContext(
        evidence=(Evidence(1, "Fused evidence", 1 / 61, "rrf_score"),)
    )

    result = GroundedGenerator(minimum_score=0.1).generate(
        "What is supported?",
        context,
    )

    assert not result.refused


def test_generator_returns_traceable_citation() -> None:
    context = RetrievalContext(
        evidence=(
            Evidence(
                passage_id=7,
                text="Embeddings represent text as vectors.",
                score=0.9,
                document_id="embeddings-guide",
                document_name="Embeddings Guide",
                source_path="data/raw/embeddings.md",
                page_number=2,
                section="Vector representations",
            ),
        )
    )

    result = GroundedGenerator().generate(
        "What do embeddings represent?",
        context,
    )

    assert result.citations[0].document_id == "embeddings-guide"
    assert result.citations[0].page_number == 2
    assert result.citations[0].section == "Vector representations"
    assert "Embeddings Guide" in result.text
    assert "page 2" in result.text
    assert "Vector representations" in result.text


def test_generator_separates_question_instructions_and_evidence() -> None:
    provider = RecordingProvider()
    context = RetrievalContext(
        evidence=(
            Evidence(
                passage_id=7,
                text="Embeddings represent text as vectors.",
                score=0.9,
            ),
        )
    )

    result = GroundedGenerator(provider=provider).generate(
        "What do embeddings represent?",
        context,
    )

    assert result.text == "provider answer"
    assert provider.prompt is not None
    assert provider.prompt.instructions == GROUNDING_INSTRUCTIONS
    assert provider.prompt.question == "What do embeddings represent?"
    assert provider.prompt.evidence[0].passage_id == 7
    assert "INSTRUCTIONS" in provider.prompt.as_text()
    assert "QUESTION" in provider.prompt.as_text()
    assert "EVIDENCE" in provider.prompt.as_text()
    assert "Embeddings represent text as vectors." in provider.prompt.as_text()
