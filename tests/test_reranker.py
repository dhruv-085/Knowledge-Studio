from rag_assistant.hybrid_search import HybridSearchResult
from rag_assistant.keyword_search import Passage
from rag_assistant.cross_encoder_reranker import rerank_with_cross_encoder
from rag_assistant.reranker import rerank, reranker_score


def test_reranker_rewards_query_passage_term_overlap() -> None:
    score, matched_terms = reranker_score(
        "What does MAX_RETRIES control?",
        "MAX_RETRIES control failed request attempts.",
    )

    assert score > 0.0
    assert "max_retries" in matched_terms
    assert "control" in matched_terms


def test_reranker_orders_candidates_by_pairwise_relevance() -> None:
    irrelevant = HybridSearchResult(
        passage=Passage(1, "Python uses indentation for code blocks."),
        score=0.9,
        methods=("semantic",),
    )
    relevant = HybridSearchResult(
        passage=Passage(2, "Inactive sessions expire after 30 minutes."),
        score=0.1,
        methods=("keyword",),
    )

    results = rerank(
        "When does an inactive session expire?",
        [irrelevant, relevant],
        limit=2,
    )

    assert [result.passage.passage_id for result in results] == [2, 1]


def test_reranker_does_not_create_new_candidates() -> None:
    candidates = [
        HybridSearchResult(
            passage=Passage(1, "Python uses indentation."),
            score=0.5,
            methods=("semantic",),
        )
    ]

    results = rerank("What is Python?", candidates, limit=5)

    assert [result.passage.passage_id for result in results] == [1]


def test_cross_encoder_reranker_sorts_model_scores() -> None:
    class FakeCrossEncoder:
        def predict(self, pairs, show_progress_bar=False):
            assert pairs[0][0] == "What is relevant?"
            return [0.1, 0.9]

    candidates = [
        HybridSearchResult(
            passage=Passage(1, "First candidate."),
            score=0.8,
            methods=("hybrid",),
        ),
        HybridSearchResult(
            passage=Passage(2, "Second candidate."),
            score=0.7,
            methods=("hybrid",),
        ),
    ]

    results = rerank_with_cross_encoder(
        "What is relevant?",
        candidates,
        FakeCrossEncoder(),
        limit=2,
    )

    assert [result.passage.passage_id for result in results] == [2, 1]
    assert results[0].reranker_score == 0.9
