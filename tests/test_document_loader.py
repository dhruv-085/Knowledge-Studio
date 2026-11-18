from pathlib import Path

import pytest

from rag_assistant.document_loader import load_document


def test_loader_returns_text_with_source_metadata(tmp_path: Path) -> None:
    source = tmp_path / "authentication.md"
    source.write_text(
        "The system terminates inactive sessions after 30 minutes.",
        encoding="utf-8",
    )

    document = load_document(source, document_id="auth-v1")

    assert document.document_id == "auth-v1"
    assert document.document_name == "authentication.md"
    assert document.source_path == str(source)
    assert "30 minutes" in document.text


def test_loader_allows_a_display_name(tmp_path: Path) -> None:
    source = tmp_path / "auth.txt"
    source.write_text("Session text", encoding="utf-8")

    document = load_document(
        source,
        document_id="auth-v1",
        document_name="Authentication Guide",
    )

    assert document.document_name == "Authentication Guide"


@pytest.mark.parametrize("extension", [".txt", ".md", ".markdown"])
def test_loader_accepts_supported_text_extensions(
    tmp_path: Path,
    extension: str,
) -> None:
    source = tmp_path / f"auth{extension}"
    source.write_text("# Authentication\n\nSession text", encoding="utf-8")

    document = load_document(source, document_id="auth-v1")

    assert document.text == "# Authentication\n\nSession text"


def test_loader_rejects_unsupported_document_format(tmp_path: Path) -> None:
    source = tmp_path / "auth.pdf"
    source.write_bytes(b"not a parsed PDF")

    with pytest.raises(ValueError, match=r"unsupported document format: \.pdf"):
        load_document(source, document_id="auth-v1")


def test_loader_rejects_an_empty_document_id(tmp_path: Path) -> None:
    source = tmp_path / "auth.txt"
    source.write_text("Session text", encoding="utf-8")

    with pytest.raises(ValueError, match="document_id must not be empty"):
        load_document(source, document_id=" ")
