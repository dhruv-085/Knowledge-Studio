# Technical Knowledge Assistant — Learning-First Build Plan

## 1. Purpose of this plan

This project will be built as a sequence of small, understandable systems rather than as one large application assembled all at once.

The goal is not only to produce a working RAG application. The goal is that, by the end, I can explain:

- what every major component does;
- why it exists;
- what problem it solves;
- what alternatives were considered;
- how I tested it;
- what its limitations are; and
- how the design would change at larger scale.

The project destination is a production-oriented technical knowledge assistant. The first milestone is intentionally much smaller:

```text
One document
    ↓
Extract text
    ↓
Split text into chunks
    ↓
Create embeddings
    ↓
Search similar chunks
    ↓
Generate an answer from retrieved context
```

The system will be improved only after the current stage is executable, tested, and explainable.

## 2. Product direction

The assistant will specialize in technical knowledge: AI and machine-learning papers, software documentation, API documentation, database documentation, and related engineering notes.

This is a better learning domain than a generic “chat with PDFs” application because it gives us realistic questions involving:

- concepts, where semantic search should help;
- exact identifiers such as `MAX_RETRIES`, where keyword search matters;
- multiple documents that need comparison;
- citations that can be checked by a reader; and
- follow-up questions that require conversation context.

The final user experience is expected to support:

1. Uploading PDF, TXT, Markdown, and DOCX files.
2. Extracting and cleaning their text.
3. Splitting the text while preserving useful metadata.
4. Searching semantically and lexically.
5. Reranking candidate passages.
6. Answering only from adequate retrieved evidence.
7. Showing citations that point to documents, pages, and chunks.
8. Asking follow-up questions using conversation context.
9. Measuring retrieval and answer quality with a real evaluation set.

The final feature list is a destination, not the starting scope.

## 3. Learning rules for the build

These rules keep the project educational instead of turning it into opaque framework assembly.

### Rule 1: Each milestone must run by itself

At the end of each milestone there must be a command that a new developer can run and a visible result they can inspect.

### Rule 2: Understand the plain version before using an abstraction

We will first write small Python modules ourselves. Libraries are welcome when they solve a real problem, but we will not hide the entire pipeline behind a framework before understanding the pipeline.

### Rule 3: Keep decisions reversible

The first implementation should use local, inexpensive components where possible. A later vector database, embedding provider, or LLM provider can be added behind a small interface instead of forcing an early infrastructure commitment.

### Rule 4: Measure before claiming improvement

If chunking, hybrid search, reranking, or a prompt change is described as better, we will create an experiment or test that supports the claim.

### Rule 5: Treat “I don’t know” as a feature

The assistant must be able to say that the uploaded documents do not contain enough evidence. RAG does not automatically prevent hallucination.

### Rule 6: Keep a decision and experiment record

Important design choices, failed approaches, and measured results will be recorded in `docs/decisions/` and `experiments/` as the project grows. These records will later become interview-ready evidence.

## 4. Working method for every milestone

For each part, we will follow the same loop:

1. **Explain the concept** in plain language.
2. **Inspect the inputs and outputs** with tiny examples.
3. **Create or update the smallest folder structure** needed for the lesson.
4. **Implement the feature** in simple Python.
5. **Run it manually** on a known example.
6. **Add automated tests** for the behavior we now understand.
7. **Discuss failure cases and trade-offs.**
8. **Write a short learning note** before moving on.

The phrase “done” means all eight steps are complete for that milestone.

## 5. Roadmap at a glance

| Phase | Working result | Main concepts |
|---|---|---|
| 0 | A clean Python project skeleton | environments, packages, configuration, testing, Git |
| 1 | A one-document keyword search tool | parsing, normalization, indexing, limitations of keyword search |
| 2 | A tiny semantic search engine | embeddings, vectors, cosine similarity, top-k search |
| 3 | Basic RAG over one document | context construction, prompting, grounded answers |
| 4 | Multi-document RAG with citations | metadata, page/chunk provenance, source display |
| 5 | A usable local CLI assistant | conversation flow, history, refusal behavior |
| 6 | Better ingestion and chunking | PDF/TXT/Markdown/DOCX, structure-aware splitting |
| 7 | Hybrid retrieval | BM25, dense retrieval, score fusion, metadata filters |
| 8 | Reranking and query reformulation | first-stage retrieval, cross-encoder reranking, conversational queries |
| 9 | Evaluation and experiments | recall, precision, faithfulness, citation accuracy, latency |
| 10 | A maintainable application core | interfaces, services, error handling, logging |
| 11 | FastAPI service | REST design, validation, uploads, API tests |
| 12 | Persistence and application data | PostgreSQL, documents, users, conversations, migrations |
| 13 | Frontend | React/TypeScript chat and document workflow |
| 14 | Production concerns | Docker, security, rate limiting, observability, deployment |
| 15 | Optional tools and extensions | web search, calculator, SQL, agentic workflows |

Phases 0–5 are the core learning path. Phases 6–9 make the system technically interesting and measurable. Phases 10–14 turn it into a resume-ready web application. Phase 15 is optional and should not distract from the RAG foundation.

## 6. Detailed build plan

### Phase 0 — Project foundation

**Outcome:** A normal, readable Python project with a repeatable development environment.

**We will learn:**

- why a virtual environment is used;
- how Python packages are organized;
- the difference between application code, tests, data, and configuration;
- why secrets belong in environment variables and not in source code;
- how dependency files make setup repeatable;
- how to run tests and format/check code; and
- how Git helps us inspect progress.

**Initial structure:**

```text
rag-technical-assistant/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   └── rag_assistant/
│       ├── __init__.py
│       └── settings.py
├── tests/
│   └── test_settings.py
├── data/
│   ├── raw/.gitkeep
│   └── processed/.gitkeep
└── docs/
    └── learning-notes/
```

The exact dependency list will be created when this phase begins, based on the first executable lesson. We will avoid installing the complete future stack at the start.

**Definition of done:**

- A fresh environment can install the dependencies.
- A sample command runs successfully.
- A sample test passes.
- `.env.example` documents required configuration without containing secrets.
- The README explains how to start the project.

### Phase 1 — Baseline: keyword search

**Outcome:** A small command-line program searches extracted text using words and returns matching passages.

**Why this phase exists:** It gives us a baseline to compare against. We should understand the problem before introducing embeddings.

**We will learn:** text extraction, normalization, tokenization, simple inverted indexes, matching, ranking, and why keyword search misses paraphrases.

**Example experiment:** A document says “The system terminates inactive sessions after 30 minutes.” The query “How long can I remain logged in without doing anything?” should expose the limitation of exact word matching.

**Definition of done:**

- A known text file can be indexed.
- A query returns matching passages with scores.
- Tests cover a match, no match, punctuation, and case differences.
- A learning note explains the baseline’s strengths and weaknesses.

### Phase 2 — Semantic search from first principles

**Outcome:** A command-line program embeds text and retrieves the most semantically similar chunks.

**We will learn:**

- what an embedding represents;
- why related meanings can be close even when words differ;
- vector dimensions and numerical representation;
- cosine similarity and distance metrics;
- top-k retrieval; and
- the difference between a similarity calculation and a vector index.

We will begin with a small in-memory implementation so the similarity calculation is visible. We can then use a local vector-search library when the number of chunks makes a real index useful.

**Definition of done:**

- A sample document is split into chunks.
- Every chunk receives an embedding and retains its original text.
- A query receives an embedding.
- The system returns top-k chunks and similarity scores.
- We can explain why the result was retrieved.
- Tests verify vector shapes, deterministic behavior where appropriate, and ranking on a small fixture.

This is the first major milestone: “I can explain and implement embeddings, vector similarity search, and the retrieval part of basic RAG.”

### Phase 3 — Basic RAG over one document

**Outcome:** The system retrieves relevant chunks and asks an LLM to answer using only those chunks.

**We will learn:**

- retrieval versus generation;
- how context is assembled;
- prompt instructions and their limits;
- why the LLM should not receive the whole document by default;
- how unsupported questions should be handled; and
- what groundedness means.

The first answer format will be intentionally simple: answer text plus the chunk identifiers used as evidence.

**Definition of done:**

- The retrieved context is visible before generation.
- The prompt clearly separates the question, evidence, and instructions.
- An in-scope question produces an answer supported by the document.
- An out-of-scope question produces an explicit insufficient-evidence response.
- Tests cover context formatting and refusal behavior.

The LLM provider will be kept behind a small interface so the retrieval system is not tied to one vendor.

### Phase 4 — Multi-document ingestion and citations

**Outcome:** Multiple documents can be indexed, searched, and cited.

**We will learn:**

- document identity;
- metadata as part of the retrieval result;
- source provenance;
- page and section information;
- why citations must be attached during ingestion rather than reconstructed later; and
- how duplicate or repeated content affects search.

Each chunk should carry, at minimum:

```text
document_id
document_name
source_path
page_number (when available)
section (when available)
chunk_id
chunk_text
```

**Definition of done:**

- More than one document can be indexed.
- Results show the document and chunk that produced them.
- Generated answers include citations tied to retrieved evidence.
- A reader can inspect the exact source passage.
- Tests confirm that metadata remains attached through retrieval and answer formatting.

### Phase 5 — Local conversational assistant

**Outcome:** A user can ask questions repeatedly through a simple CLI session.

**We will learn:** conversation history, the difference between chat history and retrieval context, follow-up questions, query reformulation, and prompt length management.

Example:

```text
User: What is RAG?
Assistant: ...
User: What are its limitations?
Assistant: ...
```

The system should reformulate “its” into a standalone search query when necessary, while still answering from retrieved documents.

**Definition of done:**

- The CLI accepts repeated questions.
- The system preserves a bounded conversation history.
- Follow-up questions retrieve the correct topic.
- A conversation can be cleared or restarted.
- The implementation documents the difference between memory used for understanding and evidence used for answering.

### Phase 6 — Robust ingestion and chunking experiments

**Outcome:** PDF, TXT, Markdown, and DOCX files can be ingested through a common document interface.

**We will learn:** file parsing, extraction failures, page boundaries, Unicode, headings, paragraphs, tables, chunk size, overlap, and structure-aware splitting.

We will compare at least:

1. fixed-size character chunks;
2. fixed-size chunks with overlap;
3. paragraph-aware chunks; and
4. heading/section-aware chunks where the source format allows it.

We will not assume that the largest chunk or the most overlap is best. The evaluation phase will provide evidence.

**Definition of done:**

- Each supported file type has a parser or a clearly documented limitation.
- Parsing errors are reported usefully.
- Chunks preserve source metadata.
- Chunking strategies can be selected through configuration.
- A small experiment compares strategies on the same questions.

### Phase 7 — Hybrid retrieval

**Outcome:** Semantic retrieval and lexical retrieval are combined.

**Why this matters:** Semantic search is useful for concepts. Lexical search is often better for exact identifiers, names, version numbers, and configuration keys.

**We will learn:** BM25 or another lexical ranking method, dense versus sparse retrieval, candidate merging, score normalization, reciprocal rank fusion, and metadata filtering.

The retrieval flow becomes:

```text
Query
 ├── dense/vector search
 └── lexical/BM25 search
          ↓
      merge/rank
          ↓
      top candidates
```

**Definition of done:**

- The same query can run through both retrieval methods.
- Results show which method found each candidate.
- A documented fusion method combines the candidate lists.
- Exact-identifier and paraphrase examples demonstrate the trade-off.
- Retrieval evaluation shows whether hybrid search actually helped.

### Phase 8 — Reranking and query reformulation

**Outcome:** The system retrieves a larger candidate set, reranks it, and reformulates conversational queries when needed.

**We will learn:** first-stage retrieval versus second-stage reranking, cross-encoder intuition, latency/quality trade-offs, query rewriting, and when reformulation can introduce errors.

The flow becomes:

```text
Conversation + current question
              ↓
        standalone query
              ↓
     dense + lexical retrieval
              ↓
       candidate set, e.g. 20
              ↓
           reranker
              ↓
       context set, e.g. 5
```

**Definition of done:**

- Reranking is optional and measurable.
- Latency is recorded separately for retrieval and reranking.
- Reformulated queries can be inspected for debugging.
- The final context is smaller and more relevant than the raw candidate list on the evaluation set.

### Phase 9 — Evaluation and experiments

**Outcome:** We can measure whether the system works and whether a change improved it.

**We will learn:** test datasets, ground-truth sources, retrieval recall, precision, context relevance, answer faithfulness, citation accuracy, latency, and cost/tokens.

The first evaluation dataset will be small and manually reviewed. It should include:

```text
Question                         Expected source/evidence
----------------------------------------------------------
What is RAG?                     RAG document, relevant section
Why use embeddings?              Embeddings document
What is overfitting?             ML document
What is attention?               Transformers document
What is not covered?             No adequate source
```

We will deliberately test failures:

- irrelevant questions;
- ambiguous questions;
- exact configuration identifiers;
- questions requiring multiple documents;
- missing evidence;
- bad extraction; and
- misleading or contradictory passages.

**Definition of done:**

- The evaluation questions and expected evidence are stored in version-controlled data.
- Metrics are calculated by a repeatable command.
- Results are saved with the configuration used.
- At least one experiment compares chunk sizes, top-k values, and retrieval strategies.
- Claims in the README or resume are based on measured results only.

### Phase 10 — Maintainable application core

**Outcome:** The working prototype is reorganized into clear modules without hiding the behavior.

**We will learn:** separation of concerns, dependency injection at a practical level, interfaces, domain models, service boundaries, configuration, logging, and error handling.

Likely application boundaries:

```text
document_loader      read and parse files
text_cleaner         normalize extracted text
chunker              create chunks and metadata
embedder             create embeddings
vector_store         store/search dense vectors
lexical_store        store/search lexical terms
retriever            combine and rank candidates
reranker             refine candidates
context_builder      format evidence for the LLM
generator            produce grounded answers
citation_formatter   expose source references
```

**Definition of done:**

- Each boundary has a small, readable responsibility.
- Provider-specific code is isolated.
- Unit tests cover each important boundary.
- Integration tests cover the complete local pipeline.
- Failures produce useful logs without exposing secrets.

### Phase 11 — FastAPI service

**Outcome:** The local assistant becomes an HTTP API.

**We will learn:** REST endpoints, request/response models, validation, file uploads, status codes, API testing, and service startup.

Initial endpoints may include:

```text
POST /documents
GET  /documents
POST /documents/{document_id}/index
POST /chat
GET  /conversations/{conversation_id}
```

The exact API will be chosen after the local application core is stable.

**Definition of done:**

- The API can accept a document and report its ingestion state.
- A chat request returns an answer and citations.
- Invalid requests receive useful validation errors.
- API tests cover success and failure paths.
- The CLI and API use the same application services.

### Phase 12 — Persistence and application data

**Outcome:** Documents, chunks, users, and conversations have durable storage.

**We will learn:** relational modeling, identifiers, relationships, migrations, transaction boundaries, and the difference between application metadata and vector-search data.

PostgreSQL will eventually store entities such as:

- users;
- documents;
- ingestion jobs/status;
- conversations;
- messages; and
- citation references.

The vector index may remain a separate local or dedicated store depending on the deployment decision. The reason for that choice will be documented rather than assumed.

**Definition of done:**

- The schema is represented by migrations.
- Data survives a restart.
- Conversations and document records can be queried.
- Error handling covers partial ingestion and retryable failures.
- Tests use an isolated database strategy.

### Phase 13 — Frontend

**Status:** The React/TypeScript vertical slice is implemented. Conversation,
document, message, citation, and evidence records are stored in browser
IndexedDB. The stateless API parses uploads and receives selected documents
and recent history with each chat request. See `README.md` and
`learning/deployment_plan.md` for local and deployment setup.

**Outcome:** A React/TypeScript interface supports document upload, chat, source inspection, and conversation selection. Implement the first useful vertical slice directly against the FastAPI service; keep polish and scope focused on a single user and local development.

**We will learn:** API integration, loading and error states, citations as a user interface, streaming versus non-streaming answers, and accessible interaction design.

The first frontend should remain intentionally small and usable:

- document list and upload;
- chat history;
- question input;
- answer display;
- expandable source citations; and
- clear feedback when evidence is insufficient.

The API contract for this deployment is:

- `POST /documents` parses an upload and returns extracted text, metadata, and PDF page text;
- `POST /chat` receives the active conversation ID, selected documents, and recent history, then returns an answer with citations and retrieved evidence;
- `GET /health` supports service health checks.

Browser storage is the source of conversation persistence for this deployment.
The earlier Phase 12 proposal for server-side PostgreSQL persistence is
deferred; revisit it if the product adds accounts, cross-device sync, or
shared/team data.

Fast-track rule: ship the working experience in small vertical slices. Keep learning notes to a concise state/decision update at meaningful milestones. Do not add accounts, streaming, a separate design system, or deployment infrastructure in this phase. The user has authorized autonomous file changes, so implementation can proceed without presenting each patch for approval.

### Phase 14 — Production concerns

**Status:** Deployment preparation has begun. The API is stateless for user
data, requests are bounded, process-local encoder reuse and rate limiting are
implemented, and Render/Pages settings are documented. External dashboard
configuration and deployed-flow verification remain outstanding. Track them
in `learning/deployment_plan.md`.

**Outcome:** The application is packaged and operated more like a real service.

**We will learn:** Docker, environment-specific configuration, secret handling, structured logging, health checks, rate limiting, authentication, background ingestion, retries, observability, and deployment.

These items will be added only after the local behavior and evaluation are trustworthy. Infrastructure should support the product rather than hide an unmeasured retrieval system.

**Definition of done:**

- The service can be started from documented instructions.
- Secrets are not committed.
- Health and readiness behavior is defined.
- Logs make ingestion and query failures diagnosable.
- Basic abuse and rate-limit controls exist.
- Deployment limitations and costs are documented.

### Phase 15 — Optional agentic extensions

Only after the RAG system is evaluated should we consider adding tools such as web search, a calculator, SQL access, or other actions.

Each tool would require a separate safety and evaluation discussion. Tool calling is not a substitute for understanding retrieval, grounding, or citations.

## 7. Proposed final repository structure

This is the likely destination. It will grow gradually; we will not create every folder on day one.

```text
rag-technical-assistant/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml                 # added when tooling is stable enough
├── docker-compose.yml             # added in the production phase
├── src/
│   └── rag_assistant/
│       ├── __init__.py
│       ├── settings.py
│       ├── domain/
│       │   ├── models.py
│       │   └── interfaces.py
│       ├── ingestion/
│       │   ├── loaders.py
│       │   ├── cleaning.py
│       │   └── chunking.py
│       ├── retrieval/
│       │   ├── embeddings.py
│       │   ├── vector_store.py
│       │   ├── lexical_store.py
│       │   ├── hybrid.py
│       │   └── reranking.py
│       ├── generation/
│       │   ├── prompts.py
│       │   ├── context.py
│       │   └── answerer.py
│       ├── application/
│       │   ├── ingest_documents.py
│       │   └── answer_questions.py
│       └── api/
│           ├── app.py
│           ├── schemas.py
│           └── routes/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
├── experiments/
│   ├── README.md
│   └── results/
├── docs/
│   ├── learning-notes/
│   ├── decisions/
│   └── architecture/
└── frontend/                      # added after the API is useful
```

The structure may change if the implementation teaches us that another boundary is clearer. The reason for a change should be recorded.

## 8. Technology strategy

We will start with the smallest useful set of tools:

- Python for the core implementation;
- a virtual environment for isolation;
- plain modules and the standard library where practical;
- a pretrained local embedding model or a clearly isolated embedding provider;
- an in-memory index first, then FAISS when a real local vector index is useful;
- one LLM provider behind a small interface;
- pytest for automated tests; and
- a command-line interface before a web interface.

Later choices will be made when the problem requires them:

- a document parser per file format;
- BM25 or another lexical retrieval implementation;
- a reranker;
- Qdrant or another persistent vector database if scale/persistence requires it;
- PostgreSQL for application records;
- FastAPI for the service layer;
- React/TypeScript for the frontend; and
- Docker for reproducible deployment.

We will avoid adding LangChain, LangGraph, a hosted vector database, a queue, Redis, Kubernetes, and multiple model providers merely because they are common in example projects. An abstraction can be added after the underlying behavior is understood and the abstraction provides a clear benefit.

## 9. Configuration and environment-variable policy

Configuration will be explicit and centralized. The project will distinguish:

- safe defaults, such as local data directories;
- required secrets, such as an LLM API key;
- provider selection; and
- experiment settings, such as chunk size and top-k.

The repository will contain `.env.example`, never real credentials. The application will validate configuration at startup and produce a clear message when a required value is missing.

No secret will be placed in source code, notebooks, test fixtures, screenshots, or Git history.

## 10. Testing strategy

Testing will grow with the project:

1. **Unit tests:** one function or class at a time, such as cleaning text or calculating similarity.
2. **Component tests:** a parser, chunker, retriever, or prompt builder with fixed fixtures.
3. **Integration tests:** ingestion through retrieval, and retrieval through answer formatting.
4. **API tests:** request validation, status codes, and response shapes.
5. **Evaluation tests:** quality metrics on a fixed question/evidence dataset.
6. **Manual exploratory tests:** questions designed to expose missing evidence, bad citations, and retrieval failures.

Tests should not depend on a live paid model unless explicitly marked as an optional integration test. Deterministic local fixtures will cover the normal test suite.

## 11. Safety and quality principles

The assistant is document-grounded, not automatically truthful. The application must communicate uncertainty and preserve evidence.

Important safeguards include:

- never presenting retrieved text as proof without showing its source;
- refusing or qualifying answers when evidence is inadequate;
- separating document facts from general model reasoning;
- preventing prompt-injection text inside documents from silently overriding system instructions;
- limiting uploaded file size and type;
- treating uploaded files as untrusted input;
- logging failures without logging secrets; and
- making it possible to inspect the retrieved context during debugging.

These safeguards will be implemented incrementally and tested explicitly.

## 12. What I should be able to explain at the end

By completion, I should be able to explain the whole path:

```text
Upload
  ↓
Parse and clean
  ↓
Chunk with metadata
  ↓
Embed and index
  ↓
Understand/reformulate query
  ↓
Dense + lexical retrieval
  ↓
Rerank candidates
  ↓
Build bounded evidence context
  ↓
Generate grounded answer
  ↓
Attach verifiable citations
  ↓
Measure quality and latency
```

I should also be able to answer common interview questions:

- Why not send the entire document to the LLM?
- What problem do embeddings solve?
- What is the difference between a vector store and an embedding model?
- Why is keyword search still useful?
- Why retrieve 20 passages and then rerank to 5?
- How do chunk size and overlap affect retrieval?
- How do you know an answer is grounded?
- What happens when the answer is not in the documents?
- How are citations preserved from ingestion to the final response?
- What would change at millions of documents?
- Which design decisions are measured, and which are currently assumptions?

## 13. First implementation session

The next practical step is **Phase 0 only**:

1. Confirm the project name and create the initial Python structure.
2. Create the virtual environment.
3. Add the first minimal dependency file.
4. Add `.env.example` and `.gitignore`.
5. Add a tiny settings module.
6. Add one test and a README with setup instructions.
7. Run the test and a sample command.
8. Review every file and explain why it exists.

We will not add React, Docker, a database, a vector database, or a large framework in this first session.

## 14. Progress checklist

- [ ] I can set up the project from the README.
- [ ] I understand the initial folder structure.
- [ ] I can explain the keyword-search baseline.
- [ ] I can explain embeddings and cosine similarity.
- [ ] I can inspect retrieved chunks before generation.
- [ ] I can explain why a generated answer is or is not grounded.
- [ ] I can trace a citation to its source chunk.
- [ ] I can explain the effect of chunking choices.
- [ ] I can compare dense, lexical, hybrid, and reranked retrieval.
- [ ] I have a repeatable evaluation dataset and measured results.
- [ ] I can run the local assistant through the CLI.
- [ ] I can run the same application through the API.
- [ ] I understand the persistence model.
- [ ] I can use the frontend to upload, chat, and inspect citations.
- [ ] I can describe the production limitations and next steps honestly.

## 15. Important expectation

The project is allowed to be incomplete for a while. A small system that I understand deeply is more valuable than a large system whose behavior I cannot explain.

The build should therefore proceed in this order:

```text
Understand → implement → test → inspect failure → document → extend
```

