from pathlib import Path

from rag_assistant.rag_cli import main


def test_interactive_cli_keeps_bounded_history_and_can_clear(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    source = tmp_path / "guide.txt"
    source.write_text(
        "RAG uses retrieval to find relevant documents before generating an answer.",
        encoding="utf-8",
    )

    questions = iter(
        [
            "What does retrieval do?",
            "Why retrieve evidence?",
            "What is grounding?",
            "/clear",
            "What is retrieval?",
            "/exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    exit_code = main(
        [
            str(source),
            "--interactive",
            "--max-turns",
            "2",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Interactive mode" in output
    assert "Unknown document" not in output
    assert "source:" in output
    assert "Conversation messages kept: 4" in output
    assert "Conversation cleared." in output
    assert output.rstrip().endswith("Conversation messages kept: 2")


def test_one_shot_cli_still_requires_a_question(tmp_path: Path) -> None:
    source = tmp_path / "guide.txt"
    source.write_text("RAG retrieves evidence.", encoding="utf-8")

    try:
        main([str(source)])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("one-shot mode should require a question")
