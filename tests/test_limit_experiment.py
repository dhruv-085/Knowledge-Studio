from rag_assistant.limit_experiment import run_experiment


def test_limit_experiment_records_each_limit_and_case() -> None:
    result = run_experiment(limits=(1, 2))

    assert result["limits"] == [1, 2]
    assert result["evaluation_questions"] == 18
    assert len(result["cases"]) == 36
    assert set(result["summary"]) == {"1", "2"}
    assert all("citations_correct" in case for case in result["cases"])
