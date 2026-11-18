from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)

from rag_assistant.api import create_app


def make_text_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    page[NameObject("/Resources")] = writer._add_object(resources)
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_returns_answer_and_citations() -> None:
    client = TestClient(create_app(Path("data/phase-1-example.txt")))

    response = client.post(
        "/chat",
        json={"question": "What does MAX_RETRIES control?", "limit": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "What does MAX_RETRIES control?"
    assert body["passage_ids"]
    assert body["citations"]
    assert len(body["retrieved_evidence"]) == 1


def test_pdf_upload_is_listed_and_keeps_page_number() -> None:
    client = TestClient(create_app(document_path=None))

    response = client.post(
        "/documents",
        files={"file": ("guide.pdf", make_text_pdf("MAX_RETRIES controls retry count."), "application/pdf")},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["file_type"] == "pdf"
    assert document["status"] == "ready"
    assert document["page_count"] == 1

    listed = client.get("/documents")
    assert listed.status_code == 200
    assert listed.json()[0]["document_id"] == document["document_id"]

    stored = client.get(f"/documents/{document['document_id']}")
    assert stored.status_code == 200
    assert stored.json()["filename"] == "guide.pdf"

    chat = client.post(
        "/chat",
        json={"question": "What does MAX_RETRIES control?", "limit": 1},
    )
    assert chat.status_code == 200
    assert chat.json()["citations"][0]["page_number"] == 1


def test_upload_rejects_image_only_pdf_with_clear_message() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    client = TestClient(create_app(document_path=None))

    response = client.post(
        "/documents",
        files={"file": ("scan.pdf", output.getvalue(), "application/pdf")},
    )

    assert response.status_code == 400
    assert "OCR" in response.json()["detail"]


def test_upload_rejects_unsupported_file_type() -> None:
    client = TestClient(create_app(document_path=None))

    response = client.post(
        "/documents",
        files={"file": ("notes.docx", b"not supported yet", "application/octet-stream")},
    )

    assert response.status_code == 415
