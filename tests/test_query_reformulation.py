from rag_assistant.conversation import ConversationSession
from rag_assistant.query_reformulation import reformulate_query


def test_reformulates_its_reference() -> None:
    session = ConversationSession()
    session.add_user_message("What is RAG?")
    session.add_user_message("What are its limitations?")

    result = reformulate_query(session.messages, "What are its limitations?")

    assert result == "What are RAG's limitations?"


def test_leaves_standalone_question_unchanged() -> None:
    session = ConversationSession()
    session.add_user_message("What is RAG?")
    session.add_user_message("How does keyword search work?")

    result = reformulate_query(session.messages, "How does keyword search work?")

    assert result == "How does keyword search work?"


def test_does_not_reformulate_without_previous_user_question() -> None:
    session = ConversationSession()
    session.add_user_message("What are its limitations?")

    result = reformulate_query(session.messages, "What are its limitations?")

    assert result == "What are its limitations?"
