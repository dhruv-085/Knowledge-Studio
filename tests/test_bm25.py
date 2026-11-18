import pytest

from rag_assistant.bm25 import BM25Index, BM25Parameters
from rag_assistant.keyword_search import Passage


def test_bm25_prefers_a_rare_query_term() -> None:
    passages = [
        Passage(1, "retry retry retry service"),
        Passage(2, "MAX_RETRIES controls retry attempts"),
        Passage(3, "service availability information"),
    ]

    results = BM25Index(passages).search("MAX_RETRIES retry", limit=3)

    assert results[0].passage.passage_id == 2
    assert results[0].score > results[1].score
    assert results[0].matched_terms == ("max_retries", "retry")


def test_bm25_reuses_lexical_guardrails() -> None:
    passages = [Passage(1, "the system and service")]

    assert BM25Index(passages).search("what is the system service") == []


def test_bm25_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        BM25Index([], BM25Parameters(k1=-1))

    with pytest.raises(ValueError):
        BM25Index([], BM25Parameters(b=1.1))


def test_bm25_returns_empty_for_nonpositive_limit() -> None:
    index = BM25Index([Passage(1, "technical evidence")])

    assert index.search("technical", limit=0) == []
