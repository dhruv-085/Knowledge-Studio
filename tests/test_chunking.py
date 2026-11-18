from rag_assistant.chunking import (
    fixed_size_chunks,
    markdown_aware_chunks,
    overlapping_chunks,
    paragraph_aware_chunks,
)


def test_fixed_size_chunks_are_consecutive() -> None:
    chunks = fixed_size_chunks("abcdefghij", size=4)

    assert [chunk.text for chunk in chunks] == [
        "abcd",
        "efgh",
        "ij",
    ]


def test_overlapping_chunks_repeat_boundary_text() -> None:
    chunks = overlapping_chunks("abcdefghij", size=6, overlap=2)

    assert [chunk.text for chunk in chunks] == [
        "abcdef",
        "efghij",
    ]


def test_paragraph_aware_chunks_keep_paragraphs_together() -> None:
    text = (
        "Heading\n\n"
        "The first paragraph explains the problem.\n\n"
        "The second paragraph explains the solution."
    )

    chunks = paragraph_aware_chunks(text, max_size=60)

    assert [chunk.text for chunk in chunks] == [
        "Heading\n\nThe first paragraph explains the problem.",
        "The second paragraph explains the solution.",
    ]


def test_invalid_overlap_is_rejected() -> None:
    try:
        overlapping_chunks("abcdef", size=4, overlap=4)
    except ValueError as error:
        assert "smaller than size" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_markdown_aware_chunks_keep_heading_with_content() -> None:
    text = (
        "# Authentication\n\n"
        "The service creates a session after successful authentication."
    )

    chunks = markdown_aware_chunks(text, max_size=100)

    assert len(chunks) == 1
    assert chunks[0].text.startswith("# Authentication\n\n")


def test_markdown_aware_chunks_bound_long_paragraphs() -> None:
    text = "# Notes\n\n" + ("A long explanation. " * 20)

    chunks = markdown_aware_chunks(text, max_size=50)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 50 for chunk in chunks)
