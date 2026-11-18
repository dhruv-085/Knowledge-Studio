# Engineering Decisions

## Use SQLite for the first persistent demo

The API stores extracted document text and provenance in a local SQLite file.
SQLite needs no separate database server and makes persistence visible as one
file, which suits the learning and portfolio demo. It supports a simple
single-instance deployment when the host provides persistent disk storage.
It is not a guarantee for multi-instance hosting or ephemeral filesystems; the
planned PostgreSQL deployment remains a possible later step.

## Use Python 3.13 for the first environment

Python 3.13 is installed locally and provides a conservative compatibility target for the small dependency set. The choice can be revisited when model or document libraries are introduced.

## Use a `src/` package layout

Application code lives under `src/rag_assistant/`, separate from tests and data. The Phase 0 commands set `PYTHONPATH=src` explicitly; a later packaging step can replace that setup when it provides a clear benefit.

## Keep Phase 0 dependencies minimal

Only `pytest` is installed because the first executable lesson is configuration plus testing. Embedding, parsing, vector-search, and LLM libraries will be added when their corresponding problems appear.

## Keep the Phase 1 search index in memory

The baseline uses a plain Python inverted index because the dataset is one text file and the goal is to understand matching. A persistent or specialized search engine would add setup before it solves a real problem. This choice is easy to replace when later phases require larger collections or persistence.

## Use UTF-8 text files for the first loader

UTF-8 is a common text interchange format and can be read with the standard library. PDF, Markdown, and DOCX parsing are postponed until the ingestion phase introduces a concrete need for format-specific behavior.

## Score passages by distinct query-term matches

Each passage receives one point for each distinct normalized query term it contains. This makes the ranking rule visible and deterministic, but it does not account for term rarity, word order, synonyms, or meaning. BM25 and semantic retrieval are later alternatives to compare experimentally.

## Use a teaching embedder before a pretrained model

The first Phase 2 embedder uses five hand-written concept dimensions. This keeps the transformation from text to vector visible and deterministic, so we can understand vector shapes and cosine similarity without downloading a model or hiding the mechanism behind a library.

It is not a production semantic model and does not demonstrate broad language understanding. A pretrained local model remains the next replacement once the end-to-end flow is understood.
## Phase 3 generation boundary

The generator accepts a structured prompt and delegates answer creation to a small provider interface. The default `ExtractiveProvider` is deterministic and local, so the retrieval and grounding behavior can be tested without API credentials. A real LLM provider can be added later without changing the retriever or context model.

Trade-off: the current answer is not fluent generation, but the evidence boundary is visible and reproducible. This is preferable during learning to hiding the important behavior behind a remote API.
## Phase 4: carry provenance with each passage

Source metadata is stored on the passage and copied into the vector record.
This keeps document identity and location beside the text while it is being
retrieved. Reconstructing source information later from a passage or answer
would be fragile, especially when multiple documents contain similar text.

The fields currently use simple values (`str` or optional `int`) so the data
flow remains visible. Safe defaults preserve compatibility with the earlier
single-document examples. Later ingestion code will supply real document IDs,
paths, page numbers, and sections.

## Separate structured and human-readable citations

Generated answers expose structured `Citation` objects instead of requiring a
caller to parse citation text. The local provider additionally formats a
readable source label so the behavior is visible during learning. This keeps
the application interface stable when a future API or UI needs clickable
citations.

Refused answers contain no citations because insufficient evidence should not
look like a supported answer. The current citation is still limited to the
retrieved passage metadata; opening the original file or page is a later
document-serving concern.

## Phase 4: use globally unique passage IDs across documents

`MultiDocumentRagPipeline` accepts a sequence of `DocumentInput` values. It
assigns a new passage ID across the complete collection while copying each
document's identity and source path onto the passage.

This prevents two passages with local ID `1` from becoming ambiguous in a
combined result. The document metadata remains the more meaningful citation
identity; the global passage ID makes the retrieved evidence unambiguous during
debugging and testing.

Trade-off: this first implementation indexes text already held in memory and
does not yet open the original source. A later ingestion layer will read files,
extract pages or sections, and provide the same metadata to this pipeline.

## Phase 4: keep file loading separate from retrieval

`load_document()` reads one UTF-8 text file and returns the existing
`DocumentInput` model. The loader does not split, embed, or retrieve text.
This keeps the source-format concern separate from the RAG concern and gives
future PDF, Markdown, or DOCX loaders a shared output contract.

Trade-off: the first loader supports only UTF-8 text files. That limitation is
intentional: it lets us verify source-to-citation traceability before adding
format-specific parsing and page extraction.

## Phase 6: validate formats at the loader boundary

The loader accepts `.txt`, `.md`, and `.markdown` and rejects other extensions
before attempting to read them. Markdown is kept as plain text for now because
the next experiment is about chunking structure, not rendering Markdown.

This keeps format selection separate from retrieval. A future PDF or DOCX
parser can return the same `DocumentInput` while adding page or section
metadata. The trade-off is that PDF and DOCX support is still unavailable,
but unsupported input now fails explicitly instead of being treated as UTF-8.

## Phase 7: measure candidate coverage before reranking

The retrieval experiment now evaluates nine manually reviewed questions using
Recall@5, Precision@5, and MRR. Recall is checked before reranking because a
reranker can reorder retrieved candidates but cannot recover evidence that the
first-stage retriever failed to return.

The current fixture contains only three passages, so Precision@5 is partly
limited by the small corpus: some strategies return fewer than five
candidates. We record this limitation rather than presenting the result as a
production-quality estimate.

## Phase 8: begin with an inspectable reranker

The first reranker is a local, dependency-free second stage. It scores each
question-passage pair using non-stopword term overlap and gives exact
identifiers such as `MAX_RETRIES` a small bonus. It receives only hybrid
candidates and therefore cannot recover evidence omitted by first-stage
retrieval.

This is intentionally not presented as a neural cross-encoder. The trade-off
is lower language understanding in exchange for visible scoring behavior,
fast tests, and no model download. A pretrained cross-encoder is a later
comparison once the first-stage/second-stage boundary is understood.

## Phase 8: broaden hybrid retrieval with lexical guardrails

The first multi-document pipeline used lexical search only when the teaching
embedder could not represent a query. The pipeline now runs both methods when
possible and combines their ranked lists with reciprocal rank fusion.

The lexical query removes generic function words and weak domain-generic terms
such as `system` and `service`. This prevents a query like “What embedding
model does this system use?” from receiving evidence merely because a passage
contains “system”. Identifiers such as `MAX_RETRIES` are not removed.

Trade-off: this is a small, hand-written teaching guardrail, not a complete
BM25 implementation or universal vocabulary policy. A larger system should
measure document frequency and evaluate the list on a representative corpus.
RRF scores are also not comparable to cosine similarity, so the grounding
boundary treats a positive fused result as retrieved evidence instead of
applying the old absolute similarity threshold to it.

## Phase 7: add BM25 without removing the lexical control

BM25 was implemented as a separate in-memory index that reuses the existing
tokenizer and lexical guardrails. The original matcher remains available as a
control, allowing the experiment to isolate scoring from preprocessing.

Trade-off: keeping both implementations temporarily adds a small amount of
code, but it makes the learning experiment and regression comparison explicit.
On the current three-passage fixture, BM25 tied the guarded matcher. A larger
collection with competing partial matches is required before selecting BM25 as
the production lexical ranker.

## Phase 11: accept PDF text and preserve page provenance

The API accepts PDF, TXT, and Markdown uploads. PDF text is extracted page by
page and each resulting passage keeps its 1-based source page, so citations
can identify where evidence came from. `pypdf` handles text extraction and
FastAPI's multipart upload support receives the file.

Trade-off: extraction is not OCR. Image-only scans are rejected with a clear
message because silently indexing empty text would create confusing retrieval
failures. Uploaded documents are kept in memory for this learning milestone;
they disappear on restart and will become durable in Phase 12.

# Conversation source isolation

Documents uploaded from the UI are associated with the active conversation in
SQLite. This keeps a new chat's retrieval collection empty and gives users a
clear boundary for source context. Existing unscoped document and chat API
calls remain available for the earlier local demo behavior.

# Conversation context boundary

The API passes the most recent six exchanges to grounded generation and uses
the existing lightweight query reformulator before retrieval. The original
question remains the answer question; the reformulated version is only the
retrieval query. Gemini is selected when configured; the extractive provider
remains the no-key fallback.

## Chat lifecycle and request safety

New chats stay in browser state until a user adds a source or sends a valid
question. This prevents an empty sidebar entry for every click on “New chat.”
The first user message supplies the title, because later messages should not
rename an existing conversation.

User messages render optimistically and are saved by the API before retrieval
and generation. A failed generation can therefore leave a saved user message
without an answer; that is more truthful than hiding a message the user sent.

The API rejects obvious low-signal text before provider selection and limits
each chat to ten questions per rolling minute. These are simple guardrails for
accidental use, not account-wide quota enforcement; this local application has
no user identity or distributed rate limiter.
