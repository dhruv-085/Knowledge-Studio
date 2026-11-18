"""Bounded conversation memory for the local assistant."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationMessage:
    role: str
    text: str


class ConversationSession:
    """Store a bounded sequence of user and assistant messages."""

    def __init__(self, *, max_turns: int = 3) -> None:
        if max_turns <= 0:
            raise ValueError("max_turns must be greater than zero")

        self.max_turns = max_turns
        self._messages: list[ConversationMessage] = []

    @property
    def messages(self) -> tuple[ConversationMessage, ...]:
        """Return the current history without exposing mutable state."""
        return tuple(self._messages)

    def add_user_message(self, text: str) -> None:
        self._add_message("user", text)

    def add_assistant_message(self, text: str) -> None:
        self._add_message("assistant", text)

    def clear(self) -> None:
        """Remove all conversation history."""
        self._messages.clear()

    def _add_message(self, role: str, text: str) -> None:
        if not text.strip():
            raise ValueError("message text must not be empty")

        self._messages.append(
            ConversationMessage(
                role=role,
                text=text,
            )
        )

        maximum_messages = self.max_turns * 2
        self._messages = self._messages[-maximum_messages:]
