from io import BytesIO
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from rag_assistant import api
from rag_assistant.api import create_app


class FixedEncoder:
    def embed(self, text: str, **kwargs) -> tuple[float, float]:
        return (1.0, 0.0)

    def embed_many(self, texts: list[str], **kwargs) -> list[tuple[float, float]]:
        return [(1.0, 0.0) for _ in texts]


def no_gemini():
    raise ValueError("test uses the local extractive provider")


def make_text_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = writer._add_object(DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    ))
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def client_with_encoder() -> TestClient:
    app = create_app()
    app.state.encoder = FixedEncoder()
    return TestClient(app)


def test_health_endpoint() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_returns_extracted_text_without_server_document_routes() -> None:
    client = TestClient(create_app())
    response = client.post("/documents", files={"file": ("guide.txt", b"MAX_RETRIES controls retries.", "text/plain")})
    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "MAX_RETRIES controls retries."
    assert body["document_id"]
    assert client.get("/documents").status_code == 405


def test_pdf_upload_returns_page_text_for_browser_storage() -> None:
    response = TestClient(create_app()).post(
        "/documents", files={"file": ("guide.pdf", make_text_pdf("MAX_RETRIES controls retries."), "application/pdf")}
    )
    assert response.status_code == 201
    assert response.json()["page_count"] == 1
    assert response.json()["page_texts"][0]["page_number"] == 1


def test_chat_accepts_browser_documents_and_returns_citations(monkeypatch) -> None:
    monkeypatch.setattr(api, "GeminiEmbeddingProvider", FixedEncoder)
    monkeypatch.setattr(api, "PretrainedSentenceEncoder", FixedEncoder)
    monkeypatch.setattr(api, "GeminiProvider", no_gemini)
    client = TestClient(create_app())
    response = client.post("/chat", json={
        "question": "What does MAX_RETRIES control?", "limit": 1,
        "conversation_id": "browser-chat-1",
        "documents": [{"document_id": "doc-1", "document_name": "guide.txt",
                       "text": "MAX_RETRIES controls how many attempts the client makes."}],
        "history": [],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == "browser-chat-1"
    assert body["citations"][0]["document_id"] == "doc-1"
    assert body["retrieved_evidence"]


def test_chat_rejects_missing_documents_and_oversized_history() -> None:
    client = TestClient(create_app())
    missing = client.post("/chat", json={"question": "What is RAG?", "documents": []})
    assert missing.status_code == 422
    too_much_history = client.post("/chat", json={
        "question": "What is RAG?", "documents": [{"document_id": "d", "document_name": "d.txt", "text": "RAG retrieves evidence."}],
        "history": [{"role": "user", "content": "x" * 2000}] * 11,
    })
    assert too_much_history.status_code == 422


def test_upload_rejects_image_only_pdf() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    response = TestClient(create_app()).post("/documents", files={"file": ("scan.pdf", output.getvalue(), "application/pdf")})
    assert response.status_code == 400
    assert "OCR" in response.json()["detail"]


def test_upload_rejects_unsupported_file_type() -> None:
    response = TestClient(create_app()).post("/documents", files={"file": ("notes.docx", b"not supported", "application/octet-stream")})
    assert response.status_code == 415
