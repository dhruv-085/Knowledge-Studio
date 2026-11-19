from types import SimpleNamespace
from typing import Any

import pytest

from rag_assistant.embeddings import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_GEMINI_EMBEDDING_MODEL,
    GeminiEmbeddingProvider,
)


class RecordingModels:
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> None:
        self.model: str | None = None
        self.contents: Any = None
        self.config: Any = None
        self.dimension = dimension

    def embed_content(self, *, model: str, contents: Any, config: Any) -> SimpleNamespace:
        self.model = model
        self.contents = contents
        self.config = config

        if isinstance(contents, list):
            embeddings = [
                SimpleNamespace(values=[float(i + idx * 0.1) for i in range(self.dimension)])
                for idx in range(len(contents))
            ]
        else:
            embeddings = [
                SimpleNamespace(values=[float(i) for i in range(self.dimension)])
            ]
        return SimpleNamespace(embeddings=embeddings)


def test_gemini_embedding_provider_embed_single() -> None:
    models = RecordingModels()
    client = SimpleNamespace(models=models)
    provider = GeminiEmbeddingProvider(client=client)

    vector = provider.embed("What is retrieval augmented generation?")

    assert len(vector) == DEFAULT_EMBEDDING_DIMENSION
    assert vector[0] == 0.0
    assert vector[1] == 1.0
    assert models.model == DEFAULT_GEMINI_EMBEDDING_MODEL
    assert models.contents == "What is retrieval augmented generation?"
    assert models.config.task_type == "RETRIEVAL_QUERY"
    assert models.config.output_dimensionality == DEFAULT_EMBEDDING_DIMENSION


def test_gemini_embedding_provider_embed_many_batch() -> None:
    models = RecordingModels()
    client = SimpleNamespace(models=models)
    provider = GeminiEmbeddingProvider(client=client)

    passages = [
        "First technical document passage.",
        "Second passage explaining vector indices.",
    ]
    vectors = provider.embed_many(passages)

    assert len(vectors) == 2
    assert len(vectors[0]) == DEFAULT_EMBEDDING_DIMENSION
    assert len(vectors[1]) == DEFAULT_EMBEDDING_DIMENSION
    assert vectors[0][0] == 0.0
    assert vectors[1][0] == 0.1
    assert models.contents == passages
    assert models.config.task_type == "RETRIEVAL_DOCUMENT"


def test_gemini_embedding_provider_embed_empty_text_raises() -> None:
    provider = GeminiEmbeddingProvider(client=SimpleNamespace())

    with pytest.raises(ValueError, match="text must not be empty"):
        provider.embed("   ")


def test_gemini_embedding_provider_embed_many_empty_returns_empty_list() -> None:
    provider = GeminiEmbeddingProvider(client=SimpleNamespace())

    assert provider.embed_many([]) == []


def test_gemini_embedding_provider_embed_many_blank_item_raises() -> None:
    provider = GeminiEmbeddingProvider(client=SimpleNamespace())

    with pytest.raises(ValueError, match="text at index 1 must not be empty"):
        provider.embed_many(["Valid text", "  ", "Another valid text"])


def test_gemini_embedding_provider_requires_key_without_injected_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        GeminiEmbeddingProvider()


def test_gemini_embedding_provider_custom_dimension_and_model() -> None:
    models = RecordingModels(dimension=256)
    client = SimpleNamespace(models=models)
    provider = GeminiEmbeddingProvider(
        model="custom-embedding-model",
        dimension=256,
        client=client,
    )

    vector = provider.embed("Testing custom config")

    assert len(vector) == 256
    assert models.model == "custom-embedding-model"
    assert models.config.output_dimensionality == 256
