"""Command-line semantic search using the teaching embedder."""

import argparse
from pathlib import Path
from typing import Sequence

from .embeddings import TextEncoder, TeachingEmbedder
from .keyword_search import KeywordIndex, Passage, load_text_file, split_into_passages
from .vector_search import VectorIndex, VectorRecord


def build_semantic_index(
    passages: Sequence[Passage],
    embedder: TextEncoder,
) -> tuple[VectorIndex, tuple[int, ...]]:
    """Embed supported passages and return the index plus skipped IDs."""

    records: list[VectorRecord] = []
    skipped_passage_ids: list[int] = []

    for passage in passages:
        try:
            vector = embedder.embed(passage.text)
        except ValueError:
            skipped_passage_ids.append(passage.passage_id)
            continue

        records.append(
            VectorRecord(
                record_id=passage.passage_id,
                text=passage.text,
                vector=vector,
                document_id=passage.document_id,
                document_name=passage.document_name,
                source_path=passage.source_path,
                page_number=passage.page_number,
                section=passage.section,
            )
        )

    return VectorIndex(records), tuple(skipped_passage_ids)


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the semantic-search command-line parser."""

    parser = argparse.ArgumentParser(
        description="Search a UTF-8 text file using semantic similarity."
    )
    parser.add_argument("file", type=Path, help="path to the text file")
    parser.add_argument("query", nargs="+", help="question or search text")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="maximum number of results to display",
    )
    parser.add_argument(
        "--compare-keyword",
        action="store_true",
        help="also display keyword-search results",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the semantic-search command-line program."""

    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    if arguments.limit <= 0:
        parser.error("--limit must be greater than zero")

    try:
        document_text = load_text_file(arguments.file)
    except FileNotFoundError:
        parser.error(f"file not found: {arguments.file}")
    except UnicodeDecodeError:
        parser.error(f"file is not valid UTF-8 text: {arguments.file}")

    query = " ".join(arguments.query)
    passages = split_into_passages(document_text)
    embedder = TeachingEmbedder()

    try:
        query_vector = embedder.embed(query)
    except ValueError as error:
        parser.error(f"query cannot be embedded: {error}")

    index, skipped_passage_ids = build_semantic_index(passages, embedder)
    results = index.search(query_vector, limit=arguments.limit)

    print("Semantic search results")
    print("=======================")

    if not results:
        print("No semantically searchable passages found.")
    else:
        for result in results:
            print(
                f"[passage {result.record.record_id}] "
                f"cosine_similarity={result.score:.3f}"
            )
            print(result.record.text)
            print()

    if skipped_passage_ids:
        skipped = ", ".join(str(value) for value in skipped_passage_ids)
        print(
            "Teaching-embedder limitation: "
            f"skipped passages {skipped} because they contained no known concepts."
        )

    if arguments.compare_keyword:
        keyword_results = KeywordIndex(passages).search(
            query,
            limit=arguments.limit,
        )

        print()
        print("Keyword search results")
        print("======================")

        if not keyword_results:
            print("No matching passages found.")
        else:
            for result in keyword_results:
                terms = ", ".join(result.matched_terms)
                print(
                    f"[passage {result.passage.passage_id}] "
                    f"term_score={result.score} "
                    f"matched_terms={terms}"
                )
                print(result.passage.text)
                print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
