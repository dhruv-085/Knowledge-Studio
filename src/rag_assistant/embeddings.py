"""A small, inspectable teaching embedder."""

from collections.abc import Sequence
from os import environ
from typing import Any, Protocol

from .vector_search import Vector


class TextEncoder(Protocol):
    """The small interface required by the semantic index."""

    def embed(self, text: str) -> Vector:
        """Convert one text value into a vector."""


CONCEPTS = (
    "authentication",
    "time",
    "database",
    "python",
    "retrieval",
)


CONCEPT_WORDS: dict[str, frozenset[str]] = {
    "authentication": frozenset(
        {"login", "logged", "session", "sessions", "user", "users"}
    ),
    "time": frozenset(
        {"time", "minutes", "minute", "duration", "long", "inactive"}
    ),
    "database": frozenset(
        {"database", "databases", "sql", "query", "table", "tables"}
    ),
    "python": frozenset(
        {"python", "function", "functions", "module", "modules"}
    ),
    "retrieval": frozenset(
        {"retrieval", "search", "searching", "documents", "document"}
    ),
}


def _tokenize(text: str) -> set[str]:
    """Return lowercase words from text."""

    cleaned_text = text.lower()

    current_word = ""
    words: set[str] = set()

    for character in cleaned_text:
        if character.isalnum() or character == "_":
            current_word += character
        elif current_word:
            words.add(current_word)
            current_word = ""

    if current_word:
        words.add(current_word)

    return words


class TeachingEmbedder:
    """Create simple concept-based vectors for learning experiments."""

    dimension = len(CONCEPTS)

    def embed(self, text: str) -> Vector:
        """Represent text by its overlap with known concepts."""

        words = _tokenize(text)

        vector = tuple(
            float(len(words.intersection(CONCEPT_WORDS[concept])))
            for concept in CONCEPTS
        )

        if not any(vector):
            raise ValueError(
                "text does not contain any words understood by the teaching embedder"
            )

        return vector

    def embed_many(self, texts: Sequence[str]) -> list[Vector]:
        """Embed several texts in input order."""

        return [self.embed(text) for text in texts]


DEFAULT_GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_EMBEDDING_DIMENSION = 768


class GeminiEmbeddingProvider:
    """Generate semantic vectors with Google's Gemini embeddings API."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        client: Any | None = None,
    ) -> None:
        try:
            from dotenv import load_dotenv
        except ImportError:
            load_dotenv = None

        if load_dotenv is not None:
            load_dotenv()

        self.model = model or environ.get(
            "GEMINI_EMBEDDING_MODEL", DEFAULT_GEMINI_EMBEDDING_MODEL
        )
        self.dimension = dimension
        configured_key = api_key or environ.get("GEMINI_API_KEY")

        if client is not None:
            self.client = client
            return

        if not configured_key:
            raise ValueError(
                "GEMINI_API_KEY is required when using the Gemini embedding provider"
            )

        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError(
                "The Gemini embedding provider requires the google-genai package. "
                "Install the project requirements first."
            ) from error

        self.client = genai.Client(api_key=configured_key)

    def embed(
        self,
        text: str,
        *,
        task_type: str = "RETRIEVAL_QUERY",
    ) -> Vector:
        """Encode one text value as a vector."""

        if not text.strip():
            raise ValueError("text must not be empty")

        from google.genai import types

        config = types.EmbedContentConfig(
            output_dimensionality=self.dimension,
            task_type=task_type,
        )
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=config,
        )
        if not response.embeddings:
            raise RuntimeError("Gemini returned no embeddings")
        return tuple(float(value) for value in response.embeddings[0].values)

    def embed_many(
        self,
        texts: Sequence[str],
        *,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[Vector]:
        """Encode several text values in input order using batch embedding."""

        if not texts:
            return []

        for index, text in enumerate(texts):
            if not text.strip():
                raise ValueError(f"text at index {index} must not be empty")

        from google.genai import types

        config = types.EmbedContentConfig(
            output_dimensionality=self.dimension,
            task_type=task_type,
        )
        response = self.client.models.embed_content(
            model=self.model,
            contents=list(texts),
            config=config,
        )
        if not response.embeddings or len(response.embeddings) != len(texts):
            raise RuntimeError(
                f"Gemini returned {len(response.embeddings) if response.embeddings else 0} "
                f"embeddings for {len(texts)} texts"
            )
        return [
            tuple(float(value) for value in item.values)
            for item in response.embeddings
        ]


class PretrainedSentenceEncoder:
    """Create semantic vectors with a pretrained sentence-transformer model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "PretrainedSentenceEncoder requires sentence-transformers and torch."
            ) from error

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        dimension = self._model.get_embedding_dimension()

        if dimension is None:
            raise ValueError("the sentence encoder did not report a dimension")

        self.dimension = dimension

    def embed(self, text: str) -> Vector:
        """Encode one text value as a normalized vector."""

        if not text.strip():
            raise ValueError("text must not be empty")

        vector = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return tuple(float(value) for value in vector)

    def embed_many(self, texts: Sequence[str]) -> list[Vector]:
        """Encode several text values in input order."""

        if not texts:
            return []

        vectors = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [
            tuple(float(value) for value in vector)
            for vector in vectors
        ]
