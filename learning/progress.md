# Project Progress

- Current stage: Phase 11 — FastAPI document upload and grounded chat workflow.
- Completed: the searchable passage model, tokenizer, in-memory inverted index, UTF-8 text-file loader, command-line search program, automated tests, and Phase 1 learning documentation.
- Verified: the project-local `.venv` has Python 3.13.5 and pytest 8.4.2; the complete test suite passes.
- Completed in Phase 2: cosine similarity, an in-memory vector index, and a deterministic teaching embedder.
- Completed in the latest step: an end-to-end semantic-search CLI with optional keyword comparison.
- Completed in Phase 3: retrieved-context construction, grounded prompt construction, provider abstraction, deterministic extractive generation, refusal behavior, and end-to-end RAG tests.
- Phase 4 started: passages and vector records now preserve document provenance metadata.
- Completed in Phase 4 so far: provenance survives context construction, supported answers expose structured citations, and multiple text documents can be indexed together.
- Added a small text-document loading boundary that converts a real UTF-8 source file into a provenance-aware `DocumentInput`.
- Verified: two similar session-expiration passages produce distinct document IDs, names, source paths, and globally unique passage IDs in the retrieved citations; all 42 tests pass.
- Completed in Phase 5: bounded conversation history, interactive clearing, and deterministic reformulation of common `it`/`its` follow-up references.
- Completed in Phase 6 so far: a common loader contract accepts UTF-8 TXT and Markdown-family files while rejecting unsupported formats before parsing.
- Completed the first chunking experiment: fixed-size, overlapping, and paragraph-aware strategies now have a runnable comparison and focused tests.
- Observed: fixed-size splitting can cut words and identifiers; overlap adds continuity but duplicates text; paragraph-aware splitting preserves blank-line units but is not yet heading-aware and can produce oversized chunks.
- Added a Markdown-aware strategy that attaches headings to following content and bounds long blocks; later subchunks of a long block do not yet repeat the heading.
- Added a first retrieval comparison across keyword, semantic, and reciprocal-rank-fusion hybrid search.
- Expanded the retrieval evaluation set from 3 to 9 manually reviewed questions.
- Added repeatable Recall@5, Precision@5, and MRR calculations with focused tests.
- Observed: hybrid matched the best Recall@5 (0.889) and achieved the best MRR (0.833) on the expanded fixture; the retry-limit paraphrase still failed because the teaching embedder does not understand that vocabulary.
- Verified: the full project-local test suite passes with 71 tests.
- Added an inspectable second-stage reranker over hybrid candidates.
- Verified: the full project-local test suite passes with 74 tests.
- Measured: reranking improved MRR from 0.833 to 0.889, while Recall@5
  remained 0.889 and Precision@5 remained 0.178 on the nine-question fixture.
- Learned: reranking changes candidate ordering, while first-stage retrieval
  determines whether relevant evidence is available to rerank.
- Not implemented: page-aware source opening, PDF/DOCX parsing, full heading-path metadata, a real external LLM provider, and broader conversational query reformulation.
- Next discovery: evaluate reranking at smaller output depths and compare the
  transparent reranker with a pretrained cross-encoder on a larger candidate
  set.
- Completed the next reranking discovery: added a pretrained
  `cross-encoder/ms-marco-MiniLM-L6-v2` comparison and Precision@1/@2
  reporting.
- Measured on the nine-question, three-passage fixture: hybrid Precision@1
  0.778; both rerankers Precision@1 0.889. At Precision@2, all strategies
  scored 0.444. MRR was 0.833 for hybrid and 0.889 for both rerankers.
- Measured average reranking latency: 0.13 ms/query for the teaching
  reranker and 43.44 ms/query for the cross-encoder on the local run.
- Learned: the pretrained model did not improve this small fixture, but it
  jointly reads the query and passage and is therefore a more capable,
  higher-cost second-stage scorer in principle.
- Expanded the reranking evaluation set from 9 to 18 questions with harder
  paraphrases, three new cases per source passage.
- Re-ran the comparison: hybrid remained at Recall@1 0.778 / MRR 0.833,
  while both rerankers remained at Recall@1 0.889 / MRR 0.889. At depth 2,
  all strategies remained at Recall 0.889 and Precision 0.444.
- Measured average reranking latency at 0.06 ms/query for the teaching
  reranker and 24.96 ms/query for the cross-encoder on this local run.
- Learned: harder paraphrases alone did not reveal a cross-encoder advantage
  on this three-passage fixture; one paraphrase failed before reranking because
  first-stage retrieval produced no candidates.
- Broadened retrieval so lexical search runs for every query and is fused with
  semantic results, rather than serving only as an exact-identifier fallback.
- Added lexical guardrails for generic terms such as `system` and `service`
  while preserving identifiers such as `MAX_RETRIES`.
- Measured on the 18-question fixture: hybrid Recall@1 improved from 0.778 to
  0.889 and MRR from 0.833 to 0.889; Recall@2 and Recall@5 remained 0.889.
- Learned: reciprocal-rank-fusion scores are ranking scores, not cosine
  confidence scores, so the grounding threshold must not reject a positive
  fused result merely because its numeric value is small.
- Added a provider-neutral Gemini generation adapter without changing the
  deterministic local provider.
- Added CLI selection with `--provider local|gemini` and optional `--model`.
- Added a focused no-network test proving the grounded prompt reaches the
  Gemini adapter.
- Not implemented: API-call evaluation, streaming, retries, token/cost
  accounting, and provider-specific structured citations.
- Added an explicit BM25 lexical index using the same tokenizer and lexical
  guardrails as the original matcher. The guarded matcher remains available as
  the control for a fair comparison.
- Measured BM25 on the 18-question, three-passage fixture: BM25 tied guarded
  lexical search at Recall@1 0.833, MRR 0.833, and Recall@5 0.833. BM25 hybrid
  tied guarded hybrid at Recall@1 0.889 and MRR 0.889.
- Learned: BM25 cannot solve zero-overlap paraphrases; its extra scoring
  signals need competing partial matches and a larger corpus to affect order.
- Added a real pretrained bi-encoder, `all-MiniLM-L6-v2`, while keeping the
  teaching embedder available for comparison.
- Added comparison paths for pretrained semantic retrieval and BM25 plus
  pretrained semantic retrieval using the existing reciprocal-rank fusion.
- Measured on the 18-question, three-passage fixture: BM25 reached Recall@1
  0.833 / MRR 0.833; pretrained semantic retrieval reached Recall@1 1.000 /
  MRR 1.000; BM25 plus pretrained hybrid also reached 1.000 / 1.000.
- Learned: a pretrained encoder understands paraphrases beyond the manually
  defined teaching vocabulary, while BM25 remains valuable for exact
  identifiers. The hybrid tie is encouraging but not conclusive because the
  corpus is very small.
- Updated the Gemini provider to use the current Google GenAI Interactions API
  while keeping `gemini-3.5-flash-lite` as the project default model.
- Verified: the full project-local test suite passes with 89 tests.
- Completed the retrieval-limit experiment across all 18 reviewed questions at limits 1, 2, and 3 using the pretrained hybrid pipeline.
- Measured: answer correctness was 1.000 at all three limits; average irrelevant passages were 0.000, 1.000, and 1.333; citation correctness was 1.000, 0.000, and 0.000.
- Learned: larger context did not improve the first extractive answer on this fixture but did add citation noise because the generator cites every usable retrieved passage.
- Added a first FastAPI boundary with `/health` and `/chat`, reusing the existing RAG service and exposing evidence plus structured citations.
- Verified: the complete project-local test suite passes with 94 tests.
- Next discovery: decide whether citations should include only evidence used in the answer, then expand the API toward document ingestion and conversation endpoints.
- Expanded Phase 11 with multipart upload, document listing/details, in-memory readiness state, and chat over the uploaded collection.
- Added PDF text extraction with per-page provenance; image-only/scanned PDFs return an explicit OCR limitation.
- Upload accepts PDF/TXT/Markdown up to 20 MiB. Uploaded content is currently in memory and is cleared by a service restart.
- Added API coverage for PDF upload, document state, page citation provenance, blank/scanned PDFs, and unsupported formats.
- Verified: 11 focused API and multi-document tests pass.
- Next discovery: make document and conversation state durable before building the frontend in Phase 13.
- Added SQLite persistence for uploaded document text and source metadata; the API reloads documents after restart and keeps PDF page provenance for citations.
- Updated the API demo instructions and learning notes to explain local persistence and the persistent-disk requirement for deployment.
- Added conversation-scoped document links, so files uploaded in one chat do not become sources in a different chat.
- Connected recent saved turns to retrieval reformulation and the grounded Gemini prompt; saved answer citations/evidence now restore with conversation history.
- Added a React/TypeScript interface for chat selection, source upload, grounded answers, and expandable citations. No frontend or API test suite was run during this implementation.
- Updated the chat experience: empty new chats stay as drafts, the first user message becomes the stable title, and user messages appear before answer generation completes.
- Added chat deletion, a collapsible workspace panel, explicit UTC-to-Asia/Kolkata timestamp handling, and renamed the assistant to Leo.
- Added backend checks for obvious accidental input and a limit of 10 questions per chat per minute before generation.
