from rag_assistant.keyword_search import (
    KeywordIndex,
    load_text_file,
    main,
    split_into_passages,
    tokenize,
)


def test_tokenize_normalizes_case_and_punctuation() -> None:
    terms = tokenize("MAX_RETRIES, Python!")

    assert terms == ["max_retries", "python"]


def test_split_into_passages_uses_blank_lines() -> None:
    text = "First passage.\n\nSecond passage."

    passages = split_into_passages(text)

    assert len(passages) == 2
    assert passages[0].passage_id == 1
    assert passages[0].text == "First passage."
    assert passages[1].passage_id == 2
    assert passages[1].text == "Second passage."


def test_search_finds_matching_terms_case_insensitively() -> None:
    text = """
    Python uses indentation to define code blocks.

    JavaScript uses braces to define code blocks.
    """

    index = KeywordIndex.from_text(text)
    results = index.search("PYTHON")

    assert len(results) == 1
    assert results[0].passage.passage_id == 1
    assert results[0].score == 1
    assert results[0].matched_terms == ("python",)


def test_search_ranks_passages_by_number_of_matching_terms() -> None:
    text = """
    Python uses lists.

    Python uses lists and dictionaries.
    """

    index = KeywordIndex.from_text(text)
    results = index.search("python dictionaries")

    assert results[0].passage.passage_id == 2
    assert results[0].score == 2
    assert results[1].passage.passage_id == 1
    assert results[1].score == 1


def test_search_returns_no_results_when_terms_do_not_match() -> None:
    text = "The system terminates inactive sessions after 30 minutes."

    index = KeywordIndex.from_text(text)
    results = index.search("How long can I remain logged in?")

    assert results == []


def test_search_ignores_generic_question_words_as_evidence() -> None:
    text = (
        "The system terminates inactive sessions after 30 minutes.\n\n"
        "The model uses embeddings to represent text."
    )

    index = KeywordIndex.from_text(text)

    results = index.search("What does this system use?")

    assert results == []


def test_search_keeps_exact_identifiers_searchable() -> None:
    index = KeywordIndex.from_text(
        "MAX_RETRIES controls how many failed attempts are allowed."
    )

    results = index.search("What does MAX_RETRIES control?")

    assert results[0].matched_terms == ("max_retries",)


def test_load_text_file_reads_utf8_text(tmp_path) -> None:
    document_path = tmp_path / "document.txt"
    document_path.write_text("Python uses indentation.", encoding="utf-8")

    text = load_text_file(document_path)

    assert text == "Python uses indentation."


def test_index_can_be_created_from_a_text_file(tmp_path) -> None:
    document_path = tmp_path / "document.txt"
    document_path.write_text(
        "Python uses indentation.\n\nPython uses dictionaries.",
        encoding="utf-8",
    )

    index = KeywordIndex.from_file(document_path)

    assert [result.passage.passage_id for result in index.search("dictionaries")] == [2]


def test_cli_prints_matching_passages(tmp_path, capsys) -> None:
    document_path = tmp_path / "document.txt"
    document_path.write_text(
        "Python uses lists.\n\nPython uses lists and dictionaries.",
        encoding="utf-8",
    )

    exit_code = main([str(document_path), "python", "dictionaries"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[passage 2] score=2 matched_terms=python, dictionaries" in captured.out
    assert "Python uses lists and dictionaries." in captured.out


def test_cli_reports_no_matches(tmp_path, capsys) -> None:
    document_path = tmp_path / "document.txt"
    document_path.write_text("Python uses indentation.", encoding="utf-8")

    exit_code = main([str(document_path), "database"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "No matching passages found."
