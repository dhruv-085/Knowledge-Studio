from pytest import approx

from rag_assistant.hybrid_search import reciprocal_rank_fusion
from rag_assistant.keyword_search import Passage, SearchResult
from rag_assistant.vector_search import VectorSearchResult, VectorRecord


def test_reciprocal_rank_fusion_rewards_results_found_by_both_methods() -> None:
    shared = Passage(1, "shared evidence")
    keyword_only = Passage(2, "keyword evidence")

    keyword_results = [SearchResult(shared, 1, ("shared",)), SearchResult(keyword_only, 1, ("keyword",))]
    semantic_results = [
        VectorSearchResult(VectorRecord(1, "shared evidence", (1.0,)), 1.0)
    ]

    results = reciprocal_rank_fusion(keyword_results, semantic_results, limit=2)

    assert [result.passage.passage_id for result in results] == [1, 2]
    assert results[0].methods == ("keyword", "semantic")
    assert results[0].score == approx(2 / 61)


def test_reciprocal_rank_fusion_can_limit_results() -> None:
    results = reciprocal_rank_fusion(
        [SearchResult(Passage(1, "one"), 1, ("one",))],
        [],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].methods == ("keyword",)
