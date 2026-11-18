from types import SimpleNamespace

import pytest

from rag_assistant.gemini_provider import GeminiProvider
from rag_assistant.generator import GenerationPrompt


class RecordingInteractions:
    def __init__(self) -> None:
        self.model = None
        self.input = None

    def create(self, *, model, input):
        self.model = model
        self.input = input
        return SimpleNamespace(output_text="  Gemini answer  ")


def test_gemini_provider_forwards_the_grounded_prompt() -> None:
    interactions = RecordingInteractions()
    provider = GeminiProvider(
        model="test-model",
        client=SimpleNamespace(interactions=interactions),
    )
    prompt = GenerationPrompt(
        instructions="Use only the evidence.",
        question="What is RAG?",
        evidence=(),
    )

    assert provider.generate(prompt) == "Gemini answer"
    assert interactions.model == "test-model"
    assert "What is RAG?" in interactions.input
    assert "Use only the evidence." in interactions.input


def test_gemini_provider_requires_a_key_without_an_injected_client(
    monkeypatch,
) -> None:
    # An empty value prevents python-dotenv from filling the test with the
    # developer's real key from the project-root .env file.
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiProvider()
