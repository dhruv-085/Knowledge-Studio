"""Load source files into provenance-aware document inputs."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .keyword_search import load_text_file
from .multi_document_rag import DocumentInput


SUPPORTED_DOCUMENT_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".pdf"})


def load_document(
    path: str | Path,
    *,
    document_id: str,
    document_name: str | None = None,
) -> DocumentInput:
    """Read one supported text or PDF document and attach its metadata."""

    source = Path(path)

    if not document_id.strip():
        raise ValueError("document_id must not be empty")

    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))
        raise ValueError(
            f"unsupported document format: {suffix or '<none>'}; "
            f"supported formats: {supported}"
        )

    if suffix == ".pdf":
        return load_pdf_document(
            source.name,
            source.read_bytes(),
            document_id=document_id,
            document_name=document_name or source.name,
            source_path=str(source),
        )

    return DocumentInput(
        document_id=document_id,
        document_name=document_name or source.name,
        source_path=str(source),
        text=load_text_file(source),
    )


def load_pdf_document(
    filename: str,
    content: bytes,
    *,
    document_id: str,
    document_name: str | None = None,
    source_path: str | None = None,
) -> DocumentInput:
    """Extract searchable text from a PDF while retaining 1-based page numbers."""

    if not document_id.strip():
        raise ValueError("document_id must not be empty")
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise ValueError("encrypted PDFs are not supported")
        page_texts = tuple(
            (page_number, page.extract_text() or "")
            for page_number, page in enumerate(reader.pages, start=1)
        )
    except PdfReadError as error:
        raise ValueError(f"could not read PDF: {error}") from error

    if not any(text.strip() for _, text in page_texts):
        raise ValueError(
            "PDF contains no extractable text; scanned PDFs need OCR, which is not supported yet"
        )

    return DocumentInput(
        document_id=document_id,
        document_name=document_name or filename,
        text="\n\n".join(text for _, text in page_texts),
        source_path=source_path or filename,
        page_texts=page_texts,
    )
