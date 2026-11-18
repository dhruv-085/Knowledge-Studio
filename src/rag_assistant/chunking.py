"""Compare simple text chunking strategies."""

from dataclasses import dataclass
from pathlib import Path
import argparse
import re


@dataclass(frozen=True)
class Chunk:
    """One chunk produced by a chunking strategy."""

    chunk_id: int
    text: str


def fixed_size_chunks(text: str, size: int) -> list[Chunk]:
    """Split text into consecutive non-overlapping character windows."""

    if size <= 0:
        raise ValueError("size must be greater than zero")

    chunks = []
    for start in range(0, len(text), size):
        chunk_text = text[start : start + size].strip()
        if chunk_text:
            chunks.append(Chunk(len(chunks) + 1, chunk_text))

    return chunks


def overlapping_chunks(
    text: str,
    size: int,
    overlap: int,
) -> list[Chunk]:
    """Split text into character windows that share an overlap."""

    if size <= 0:
        raise ValueError("size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must not be negative")
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    chunks = []
    step = size - overlap

    for start in range(0, len(text), step):
        chunk_text = text[start : start + size].strip()
        if chunk_text:
            chunks.append(Chunk(len(chunks) + 1, chunk_text))

        if start + size >= len(text):
            break

    return chunks


def paragraph_aware_chunks(text: str, max_size: int) -> list[Chunk]:
    """Group complete paragraphs without exceeding the target size when possible."""

    if max_size <= 0:
        raise ValueError("max_size must be greater than zero")

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text.strip())
        if paragraph.strip()
    ]

    chunks = []
    current: list[str] = []
    current_size = 0

    for paragraph in paragraphs:
        added_size = len(paragraph) if not current else len(paragraph) + 2

        if current and current_size + added_size > max_size:
            chunks.append(Chunk(len(chunks) + 1, "\n\n".join(current)))
            current = []
            current_size = 0

        current.append(paragraph)
        current_size += len(paragraph) if len(current) == 1 else len(paragraph) + 2

    if current:
        chunks.append(Chunk(len(chunks) + 1, "\n\n".join(current)))

    return chunks


def markdown_aware_chunks(text: str, max_size: int) -> list[Chunk]:
    """Keep headings with following content and split long blocks."""

    if max_size <= 0:
        raise ValueError("max_size must be greater than zero")

    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", text.strip())
        if block.strip()
    ]

    chunks = []
    pending_heading: str | None = None

    for block in blocks:
        if block.startswith("#"):
            pending_heading = block
            continue

        if pending_heading:
            block = f"{pending_heading}\n\n{block}"
            pending_heading = None

        if len(block) <= max_size:
            chunks.append(Chunk(len(chunks) + 1, block))
        else:
            chunks.extend(fixed_size_chunks(block, max_size))

    if pending_heading:
        chunks.append(Chunk(len(chunks) + 1, pending_heading))

    return [
        Chunk(index, chunk.text)
        for index, chunk in enumerate(chunks, start=1)
    ]


def print_chunks(name: str, chunks: list[Chunk]) -> None:
    """Print chunks in a form that makes boundaries easy to inspect."""

    print(f"\n{name}")
    print("=" * len(name))
    print(f"chunk_count={len(chunks)}")

    for chunk in chunks:
        print(f"\n[chunk {chunk.chunk_id}, characters={len(chunk.text)}]")
        print(chunk.text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare simple chunking strategies."
    )
    parser.add_argument("file", type=Path)
    parser.add_argument("--size", type=int, default=140)
    parser.add_argument("--overlap", type=int, default=35)
    arguments = parser.parse_args()

    text = arguments.file.read_text(encoding="utf-8")

    print_chunks("Fixed-size", fixed_size_chunks(text, arguments.size))
    print_chunks(
        "Fixed-size with overlap",
        overlapping_chunks(text, arguments.size, arguments.overlap),
    )
    print_chunks(
        "Paragraph-aware",
        paragraph_aware_chunks(text, arguments.size),
    )
    print_chunks(
        "Markdown-aware",
        markdown_aware_chunks(text, arguments.size),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
