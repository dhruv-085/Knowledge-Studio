# Phase 1 learning note: keyword search

## Problem

Before using embeddings, we need a baseline that answers a simpler question:

> Which passages contain the same words as the query?

The baseline lets us observe matching, ranking, and failure cases directly.

## How the implementation works

1. `load_text_file()` reads a UTF-8 document.
2. `split_into_passages()` separates the document at blank lines.
3. `tokenize()` lowercases text and extracts words, numbers, and underscore-based identifiers such as `MAX_RETRIES`.
4. `KeywordIndex` builds an inverted index from each term to the passage IDs containing it.
5. `search()` looks up each distinct query term and gives a passage one point per matched term.
6. The CLI prints the passage, score, and matched terms.

The inverted index avoids scanning every passage for every query term. Conceptually, it changes the lookup from:

```text
check every passage → check every word
```

to:

```text
query term → passage IDs containing that term
```

## What the score means

The score is not probability or relevance confidence. A score of `2` means that two distinct normalized query terms occurred in the passage. Ties are resolved by the original passage order.

## Strengths

- simple and fast for a small collection;
- easy to inspect and test;
- good for exact identifiers, names, and configuration keys;
- deterministic behavior; and
- no model or external service is required.

## Weaknesses

Keyword search depends on word overlap. It can miss a relevant passage when the question uses different wording. For example, the document says “terminates inactive sessions after 30 minutes,” while the query asks “How long can I remain logged in?” The meanings are related, but the exact terms overlap poorly.

It also does not understand synonyms, context, word importance, or whether a passage answers the whole question. These limitations motivate semantic search and later lexical-ranking improvements such as BM25.

## Current project state

Implemented:

- one-document UTF-8 text loading;
- passage splitting;
- normalization and tokenization;
- in-memory inverted indexing;
- ranked keyword results;
- no-match behavior;
- command-line usage; and
- automated tests.

Not implemented yet:

- embeddings;
- cosine similarity;
- vector search;
- generated answers;
- citations; and
- evaluation metrics beyond behavior tests.

## Next discovery

Phase 2 will test whether an embedding can represent related meanings even when the exact words differ.
