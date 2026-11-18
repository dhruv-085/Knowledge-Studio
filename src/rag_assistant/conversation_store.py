"""SQLite storage for conversations and their messages."""

import sqlite3
import json
from pathlib import Path


class SQLiteConversationStore:
    """Persist conversations and retrieve their messages in order."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations (conversation_id)
                        ON DELETE CASCADE
                )
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(messages)").fetchall()
            }
            if "metadata_json" not in columns:
                connection.execute(
                    "ALTER TABLE messages ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'"
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_documents (
                    conversation_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    PRIMARY KEY (conversation_id, document_id),
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations (conversation_id)
                        ON DELETE CASCADE
                )
                """
            )

    def create_conversation(self, conversation_id: str) -> None:
        """Create a conversation unless that ID already exists."""
        if not conversation_id.strip():
            raise ValueError("conversation_id must not be empty")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversations (conversation_id)
                VALUES (?)
                """,
                (conversation_id,),
            )

    def conversation_exists(self, conversation_id: str) -> bool:
        """Return whether a conversation with this ID is stored."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()

        return row is not None

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages and document links."""
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )
            return cursor.rowcount > 0

    def count_recent_user_messages(self, conversation_id: str, seconds: int = 60) -> int:
        """Count user messages in the recent rolling time window."""
        with self._connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) AS message_count FROM messages
                   WHERE conversation_id = ? AND role = 'user'
                     AND created_at >= datetime('now', ?)""",
                (conversation_id, f"-{seconds} seconds"),
            ).fetchone()
        return int(row["message_count"])

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> int:
        """Save one message and return its database ID."""
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        if not content.strip():
            raise ValueError("content must not be empty")

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO messages (conversation_id, role, content, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, role, content, json.dumps(metadata or {})),
            )
            return int(cursor.lastrowid)

    def list_messages(self, conversation_id: str) -> list[dict[str, object]]:
        """Return a conversation's messages in the order they were saved."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT message_id, conversation_id, role, content, created_at, metadata_json
                FROM messages
                WHERE conversation_id = ?
                ORDER BY message_id
                """,
                (conversation_id,),
            ).fetchall()

        messages = []
        for row in rows:
            message = dict(row)
            metadata = json.loads(str(message.pop("metadata_json", "{}")))
            message.update(metadata)
            messages.append(message)
        return messages

    def attach_document(self, conversation_id: str, document_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO conversation_documents (conversation_id, document_id) VALUES (?, ?)",
                (conversation_id, document_id),
            )

    def list_document_ids(self, conversation_id: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT document_id FROM conversation_documents WHERE conversation_id = ? ORDER BY rowid",
                (conversation_id,),
            ).fetchall()
        return [str(row["document_id"]) for row in rows]

    def list_conversations(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT c.conversation_id, c.created_at,
                          (SELECT content FROM messages m WHERE m.conversation_id = c.conversation_id
                           AND m.role = 'user' ORDER BY m.message_id LIMIT 1) AS first_message
                   FROM conversations c ORDER BY c.created_at DESC, c.rowid DESC"""
            ).fetchall()
        return [dict(row) for row in rows]
