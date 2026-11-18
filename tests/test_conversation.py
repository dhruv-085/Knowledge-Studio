import pytest

from rag_assistant.conversation import ConversationSession


def test_session_preserves_user_and_assistant_messages() -> None:
    session = ConversationSession(max_turns=2)

    session.add_user_message("What is RAG?")
    session.add_assistant_message("RAG retrieves evidence before generation.")

    assert session.messages[0].role == "user"
    assert session.messages[0].text == "What is RAG?"
    assert session.messages[1].role == "assistant"


def test_session_keeps_only_the_configured_number_of_turns() -> None:
    session = ConversationSession(max_turns=2)

    for number in range(1, 4):
        session.add_user_message(f"Question {number}")
        session.add_assistant_message(f"Answer {number}")

    assert [message.text for message in session.messages] == [
        "Question 2",
        "Answer 2",
        "Question 3",
        "Answer 3",
    ]


def test_session_can_be_cleared() -> None:
    session = ConversationSession()
    session.add_user_message("What is RAG?")

    session.clear()

    assert session.messages == ()


def test_session_rejects_empty_messages() -> None:
    session = ConversationSession()

    with pytest.raises(ValueError, match="message text must not be empty"):
        session.add_user_message(" ")
