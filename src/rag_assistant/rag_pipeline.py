"""End-to-end grounded retrieval and answer pipeline."""

from dataclasses import dataclass

from .context_builder import RetrievalContext, build_context
from .embeddings import TeachingEmbedder
from .generator import GeneratedAnswer, GenerationProvider, GroundedGenerator
from .keyword_search import Passage, split_into_passages
from .semantic_search import build_semantic_index


@dataclass(frozen=True)
class RagResponse:
    """The observable result of one RAG request."""

    question: str
    context: RetrievalContext
    answer: GeneratedAnswer
    skipped_passage_ids: tuple[int, ...]


class RagPipeline:
    """Connect passage splitting, retrieval, context, and generation."""

    def __init__(
        self,
        *,
        max_passages: int = 3,
        minimum_score: float = 0.1,
        provider: GenerationProvider | None = None,
    ) -> None:
        if max_passages <= 0:
            raise ValueError("max_passages must be greater than zero")

        self.max_passages = max_passages
        self.embedder = TeachingEmbedder()
        self.generator = GroundedGenerator(
            minimum_score=minimum_score,
            provider=provider,
        )

    def answer(self, document_text: str, question: str) -> RagResponse:
        """Retrieve evidence and produce a grounded response."""

        if not document_text.strip():
            raise ValueError("document_text must not be empty")
        if not question.strip():
            raise ValueError("question must not be empty")

        passages: list[Passage] = split_into_passages(document_text)

        # An unknown query cannot be meaningfully compared by the teaching
        # embedder. Treat it as missing evidence so the generator can apply
        # the normal refusal behavior instead of crashing.
        try:
            query_vector = self.embedder.embed(question)
        except ValueError:
            empty_context = build_context(
                [],
                max_passages=self.max_passages,
            )
            return RagResponse(
                question=question,
                context=empty_context,
                answer=self.generator.generate(question, empty_context),
                skipped_passage_ids=tuple(
                    passage.passage_id for passage in passages
                ),
            )

        index, skipped_ids = build_semantic_index(
            passages,
            self.embedder,
        )

        search_results = index.search(
            query_vector,
            limit=self.max_passages,
        )
        context = build_context(
            search_results,
            max_passages=self.max_passages,
        )
        answer = self.generator.generate(question, context)

        return RagResponse(
            question=question,
            context=context,
            answer=answer,
            skipped_passage_ids=skipped_ids,
        )
