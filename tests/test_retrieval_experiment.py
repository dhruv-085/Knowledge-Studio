import pytest

from rag_assistant.retrieval_experiment import (
    mean_metrics,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_mean_metrics_averages_metrics_at_requested_depth() -> None:
    metrics = mean_metrics(
        [[2, 4], [4, 2]],
        [[2], [2]],
        k=1,
    )

    assert metrics == {
        "recall": 0.5,
        "precision": 0.5,
        "mrr": 0.75,
    }


def test_mean_metrics_rejects_mismatched_case_counts() -> None:
    with pytest.raises(ValueError):
        mean_metrics([[1]], [[1], [2]], k=1)


def test_recall_at_k_measures_expected_passages_found() -> None:
    assert recall_at_k([4, 2, 5], [2, 5], k=3) == 1.0
    assert recall_at_k([4, 2, 5], [2, 6], k=2) == 0.5


def test_precision_at_k_uses_all_top_k_slots() -> None:
    assert precision_at_k([2, 4, 5, 6, 7], [2], k=5) == 0.2


def test_reciprocal_rank_rewards_earlier_relevant_results() -> None:
    assert reciprocal_rank([2, 4, 5], [2]) == 1.0
    assert reciprocal_rank([4, 2, 5], [2]) == 0.5
    assert reciprocal_rank([4, 5], [2]) == 0.0


@pytest.mark.parametrize(
    ("metric", "arguments"),
    [
        (recall_at_k, ([], [1], 0)),
        (precision_at_k, ([], [1], 0)),
        (recall_at_k, ([], [], 5)),
        (precision_at_k, ([], [], 5)),
        (reciprocal_rank, ([], [])),
    ],
)
def test_metrics_reject_invalid_inputs(metric, arguments) -> None:
    with pytest.raises(ValueError):
        metric(*arguments)
