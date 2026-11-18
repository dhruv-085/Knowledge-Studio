"""Small SQLite store for uploaded document text and provenance."""

import json
import sqlite3
from pathlib import Path

from .multi_document_rag import DocumentInput


class SQLiteDocumentStore:
    """Persist source documents so the API can reload them after a restart."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source_path TEXT,
                    page_texts_json TEXT NOT NULL,
                    page_count INTEGER
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def save(
        self,
        document: DocumentInput,
        *,
        filename: str,
        file_type: str,
        page_count: int | None,
    ) -> None:
        page_texts_json = json.dumps(document.page_texts)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id, filename, file_type, document_name, text,
                    source_path, page_texts_json, page_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    filename = excluded.filename,
                    file_type = excluded.file_type,
                    document_name = excluded.document_name,
                    text = excluded.text,
                    source_path = excluded.source_path,
                    page_texts_json = excluded.page_texts_json,
                    page_count = excluded.page_count
                """,
                (
                    document.document_id,
                    filename,
                    file_type,
                    document.document_name,
                    document.text,
                    document.source_path,
                    page_texts_json,
                    page_count,
                ),
            )

    def list_documents(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY rowid"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (document_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def load_inputs(self) -> list[DocumentInput]:
        documents: list[DocumentInput] = []
        for row in self.list_documents():
            documents.append(
                DocumentInput(
                    document_id=str(row["document_id"]),
                    document_name=str(row["document_name"]),
                    text=str(row["text"]),
                    source_path=(
                        str(row["source_path"])
                        if row["source_path"] is not None
                        else None
                    ),
                    page_texts=tuple(
                        (int(page_number), str(text))
                        for page_number, text in json.loads(
                            str(row["page_texts_json"])
                        )
                    ),
                )
            )
        return documents

    def load_inputs_by_ids(self, document_ids: list[str]) -> list[DocumentInput]:
        if not document_ids:
            return []
        placeholders = ",".join("?" for _ in document_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM documents WHERE document_id IN ({placeholders}) ORDER BY rowid",
                document_ids,
            ).fetchall()
        return [
            DocumentInput(
                document_id=str(row["document_id"]),
                document_name=str(row["document_name"]),
                text=str(row["text"]),
                source_path=str(row["source_path"]) if row["source_path"] is not None else None,
                page_texts=tuple(
                    (int(page_number), str(text))
                    for page_number, text in json.loads(str(row["page_texts_json"]))
                ),
            )
            for row in rows
        ]

    def list_documents_by_ids(self, document_ids: list[str]) -> list[dict[str, object]]:
        if not document_ids:
            return []
        placeholders = ",".join("?" for _ in document_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM documents WHERE document_id IN ({placeholders}) ORDER BY rowid",
                document_ids,
            ).fetchall()
        return [dict(row) for row in rows]
