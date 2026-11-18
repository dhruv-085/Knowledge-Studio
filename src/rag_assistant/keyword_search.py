"""Simple keyword-based search over text passages."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Sequence


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")

# These words are useful for forming a sentence but are weak evidence that a
# passage answers a technical question.  Identifiers are intentionally not in
# this set, so exact configuration keys remain searchable.
LEXICAL_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "can",
        "does",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "the",
        "this",
        "to",
        "what",
        "when",
        "which",
        "without",
        "system",
        "service",
    }
)


@dataclass(frozen=True)
class Passage:
    """A searchable piece of document text."""

    passage_id: int
    text: str
    document_id: str = "single-document"
    document_name: str = "Unknown document"
    source_path: str | None = None
    page_number: int | None = None
    section: str | None = None


@dataclass(frozen=True)
class SearchResult:
    """A passage returned by a search."""

    passage: Passage
    score: int
    matched_terms: tuple[str, ...]


def tokenize(text: str) -> list[str]:
    """Convert text into lowercase searchable terms."""

    return TOKEN_PATTERN.findall(text.lower())


def split_into_passages(text: str) -> list[Passage]:
    """Split a document into passages separated by blank lines."""

    raw_passages = re.split(r"\n\s*\n", text.strip())
    passages: list[Passage] = []

    for passage_id, raw_passage in enumerate(raw_passages, start=1):
        passage_text = raw_passage.strip()

        if passage_text:
            passages.append(
                Passage(
                    passage_id=passage_id,
                    text=passage_text,
                )
            )

    return passages


def load_text_file(path: str | Path) -> str:
    """Read a UTF-8 text file and return its contents."""

    return Path(path).read_text(encoding="utf-8")


class KeywordIndex:
    """An in-memory inverted index for keyword search."""

    def __init__(self, passages: Iterable[Passage]) -> None:
        self.passages = tuple(passages)
        self.passages_by_id = {
            passage.passage_id: passage
            for passage in self.passages
        }

        self.inverted_index: dict[str, set[int]] = defaultdict(set)

        for passage in self.passages:
            passage_terms = set(tokenize(passage.text))

            for term in passage_terms:
                self.inverted_index[term].add(passage.passage_id)

    @classmethod
    def from_text(cls, text: str) -> "KeywordIndex":
        """Create an index directly from document text."""

        passages = split_into_passages(text)
        return cls(passages)

    @classmethod
    def from_file(cls, path: str | Path) -> "KeywordIndex":
        """Create an index from a UTF-8 text file."""

        return cls.from_text(load_text_file(path))

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Return passages containing the most query terms."""

        if limit <= 0:
            return []

        query_terms = [
            term
            for term in tokenize(query)
            if term not in LEXICAL_STOPWORDS
        ]

        # Remove duplicate query terms while preserving their order.
        unique_query_terms = tuple(dict.fromkeys(query_terms))

        scores: dict[int, int] = {}
        matched_terms: dict[int, list[str]] = defaultdict(list)

        for term in unique_query_terms:
            matching_passage_ids = self.inverted_index.get(term, set())

            for passage_id in matching_passage_ids:
                scores[passage_id] = scores.get(passage_id, 0) + 1
                matched_terms[passage_id].append(term)

        ranked_passage_ids = sorted(
            scores,
            key=lambda passage_id: (
                -scores[passage_id],
                passage_id,
            ),
        )

        results: list[SearchResult] = []

        for passage_id in ranked_passage_ids[:limit]:
            results.append(
                SearchResult(
                    passage=self.passages_by_id[passage_id],
                    score=scores[passage_id],
                    matched_terms=tuple(matched_terms[passage_id]),
                )
            )

        return results


def build_argument_parser():
    """Build the command-line argument parser."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Search a UTF-8 text file using keyword matching."
    )
    parser.add_argument("file", type=Path, help="path to the text file")
    parser.add_argument(
        "query",
        nargs="+",
        help="one or more words to search for",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="maximum number of results to display (default: 5)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the keyword-search command-line program."""

    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    if arguments.limit <= 0:
        parser.error("--limit must be greater than zero")

    try:
        index = KeywordIndex.from_file(arguments.file)
    except FileNotFoundError:
        parser.error(f"file not found: {arguments.file}")
    except UnicodeDecodeError:
        parser.error(f"file is not valid UTF-8 text: {arguments.file}")

    query = " ".join(arguments.query)
    results = index.search(query, limit=arguments.limit)

    if not results:
        print("No matching passages found.")
        return 0

    for result in results:
        terms = ", ".join(result.matched_terms)
        print(
            f"[passage {result.passage.passage_id}] "
            f"score={result.score} matched_terms={terms}"
        )
        print(result.passage.text)
        print()

    return 0
