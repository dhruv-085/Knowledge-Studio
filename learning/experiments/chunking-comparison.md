# Chunking comparison

## Hypothesis

Fixed-size chunks will be simple but may cut through words, headings, and
configuration names. Overlap should preserve more boundary context, but it
will duplicate text and increase the number of chunks. Paragraph-aware
chunking should preserve readable units, although it will not yet understand
heading hierarchy or split very long paragraphs.

## Experiment

Input: `data/chunking-example.md`

Configuration:

- fixed chunk size: 140 characters;
- overlap: 35 characters; and
- the same 140-character target for paragraph-aware grouping.

Command:

```powershell
$env:PYTHONPATH = "src"
python -m rag_assistant.chunking data/chunking-example.md --size 140 --overlap 35
```

## Observed results

| Strategy | Chunks | Boundary behavior |
|---|---:|---|
| Fixed-size | 5 | Split words such as `inactivity`, `SESSION_TIMEOUT_MINUTES`, and `attacker`. |
| Fixed-size with overlap | 7 | Repeated boundary text, but still split words in several places. |
| Paragraph-aware | 8 | Preserved blank-line paragraphs, headings, and readable sentences. |
| Markdown-aware | 8 | Kept headings with content and bounded the long content blocks. |

The paragraph-aware strategy allowed some chunks to exceed the target because
it did not split a paragraph. It also treated headings as ordinary paragraphs;
it is not yet heading-aware.

## Conclusion

For human-readable Markdown, paragraph boundaries are more meaningful than
arbitrary character boundaries. However, paragraph-aware chunking needs a
second rule for long paragraphs and a Markdown-specific rule for headings.
Overlap is a useful continuity mechanism, but it does not by itself prevent
bad boundaries and increases storage/retrieval duplication.

These are observations from one fixture, not a claim that paragraph-aware
chunking is always best. Retrieval questions and an evaluation set are needed
before choosing a production strategy.

## Follow-up: Markdown-aware chunking

The Markdown-aware strategy attaches each heading to the following block. If a
combined heading and block exceeds the target, it splits the combined text into
bounded windows. This keeps the first window's heading context but may not
repeat the heading in every later window.

This improves on treating headings as independent chunks, but it is still
intentionally simple. A future structure-aware splitter could carry the full
heading path, such as `Session Management > Configuration`, into every chunk
as metadata rather than repeating Markdown text.
