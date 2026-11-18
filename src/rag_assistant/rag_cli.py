"""Command-line demonstration of the grounded RAG pipeline."""

import argparse
from pathlib import Path
from typing import Sequence

from .conversation import ConversationSession
from .document_loader import load_document
from .embeddings import PretrainedSentenceEncoder, TeachingEmbedder
from .gemini_provider import GeminiProvider
from .multi_document_rag import DocumentInput, MultiDocumentRagPipeline
from .query_reformulation import reformulate_query


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Answer a question from a local text document.",
    )
    parser.add_argument("file", type=Path)
    parser.add_argument("question", nargs="*")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="start a repeated-question conversation",
    )
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument(
        "--provider",
        choices=("local", "gemini"),
        default="local",
        help="answer provider (default: local)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Gemini model name; used only with --provider gemini",
    )
    parser.add_argument(
        "--encoder",
        choices=("pretrained", "teaching"),
        default="pretrained",
        help=(
            "embedding encoder to use: pretrained uses all-MiniLM-L6-v2; "
            "teaching uses the transparent learning encoder"
        ),
    )
    return parser


def run_interactive_session(
    documents: Sequence[DocumentInput],
    *,
    max_passages: int,
    max_turns: int,
    embedder,
    provider=None,
) -> int:
    """Run a bounded local conversation over one document."""
    session = ConversationSession(max_turns=max_turns)
    pipeline = MultiDocumentRagPipeline(
        max_passages=max_passages,
        embedder=embedder,
        provider=provider,
    )

    print("Interactive mode. Type /clear to reset or /exit to quit.")

    while True:
        question = input("User: ").strip()

        if question == "/exit":
            return 0

        if question == "/clear":
            session.clear()
            print("Conversation cleared.")
            continue

        if not question:
            print("Please enter a question.")
            continue

        session.add_user_message(question)
        search_query = reformulate_query(session.messages, question)
        response = pipeline.answer(documents, search_query)
        session.add_assistant_message(response.answer.text)

        print("Assistant:")
        print(response.answer.text)
        print(f"Conversation messages kept: {len(session.messages)}")
        print()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    if arguments.limit <= 0:
        parser.error("--limit must be greater than zero")

    if arguments.max_turns <= 0:
        parser.error("--max-turns must be greater than zero")

    if not arguments.interactive and not arguments.question:
        parser.error("a question is required unless --interactive is used")

    try:
        document = load_document(
            arguments.file,
            document_id=arguments.file.stem,
        )
    except FileNotFoundError:
        parser.error(f"file not found: {arguments.file}")
    except UnicodeDecodeError:
        parser.error(f"file is not valid UTF-8 text: {arguments.file}")

    try:
        provider = (
            GeminiProvider(model=arguments.model)
            if arguments.provider == "gemini"
            else None
        )
    except (RuntimeError, ValueError) as error:
        parser.error(str(error))

    try:
        embedder = (
            PretrainedSentenceEncoder()
            if arguments.encoder == "pretrained"
            else TeachingEmbedder()
        )
    except (RuntimeError, ValueError) as error:
        parser.error(str(error))

    if arguments.interactive:
        return run_interactive_session(
            (document,),
            max_passages=arguments.limit,
            max_turns=arguments.max_turns,
            embedder=embedder,
            provider=provider,
        )

    question = " ".join(arguments.question)

    try:
        response = MultiDocumentRagPipeline(
            max_passages=arguments.limit,
            embedder=embedder,
            provider=provider,
        ).answer((document,), question)
    except ValueError as error:
        parser.error(str(error))

    print("Retrieved evidence")
    print("===================")
    print(response.context.as_text())
    print()
    print("Answer")
    print("======")
    print(response.answer.text)
    print()
    print(f"Citations: {response.answer.passage_ids}")

    if response.skipped_passage_ids:
        print(
            "Skipped passages: "
            f"{response.skipped_passage_ids}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
