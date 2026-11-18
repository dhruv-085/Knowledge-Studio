"""A small, inspectable teaching embedder."""

from collections.abc import Sequence
from typing import Protocol

from sentence_transformers import SentenceTransformer

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


class PretrainedSentenceEncoder:
    """Create semantic vectors with a pretrained sentence-transformer model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
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
