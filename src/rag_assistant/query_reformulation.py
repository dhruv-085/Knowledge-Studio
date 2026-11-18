"""Reformulate conversational questions into standalone search queries."""

import re
from collections.abc import Sequence

from .conversation import ConversationMessage


_FOLLOW_UP_WORDS = frozenset(
    {
        "it",
        "its",
        "they",
        "their",
        "them",
        "this",
        "that",
        "these",
        "those",
    }
)


def reformulate_query(
    messages: Sequence[ConversationMessage],
    question: str,
) -> str:
    """Make a follow-up question more explicit using the previous user topic."""

    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError("question must not be empty")

    if not _contains_follow_up_reference(cleaned_question):
        return cleaned_question

    previous_user_questions = [
        message.text
        for message in messages[:-1]
        if message.role == "user"
    ]

    if not previous_user_questions:
        return cleaned_question

    previous_topic = _extract_topic(previous_user_questions[-1])

    if not previous_topic:
        return cleaned_question

    topic_with_possessive = f"{previous_topic}'s"
    reformulated = re.sub(
        r"\bits\b",
        topic_with_possessive,
        cleaned_question,
        flags=re.IGNORECASE,
    )
    reformulated = re.sub(
        r"\bit\b",
        previous_topic,
        reformulated,
        flags=re.IGNORECASE,
    )

    return reformulated


def _contains_follow_up_reference(question: str) -> bool:
    words = set(re.findall(r"\b[a-zA-Z]+\b", question.lower()))
    return bool(words & _FOLLOW_UP_WORDS)


def _extract_topic(previous_question: str) -> str:
    """Extract a simple topic from common question forms."""

    question = previous_question.strip().rstrip("?.!")

    patterns = (
        r"^(?:what|who)\s+is\s+(.+)$",
        r"^(?:what|who)\s+are\s+(.+)$",
        r"^what\s+does\s+(.+?)\s+(?:do|control|mean|stand for|affect)(?:\s+.*)?$",
        r"^how\s+does\s+(.+?)\s+(?:work|help|affect|handle)(?:\s+.*)?$",
        r"^how\s+do\s+i\s+use\s+(.+)$",
        r"^(?:explain|define)\s+(.+)$",
        r"^tell me about\s+(.+)$",
    )

    for pattern in patterns:
        match = re.match(pattern, question, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return question
