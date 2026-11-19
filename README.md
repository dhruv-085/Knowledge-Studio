# Technical Knowledge Assistant (Leo)

An intelligent, privacy-first Retrieval-Augmented Generation (RAG) assistant designed for natural-language question answering over technical documentation and research papers (PDF, Markdown, Plain Text).

Built with a **stateless, ultra-low memory backend (<50 MB RSS)**, **hybrid retrieval (Dense Semantic + Lexical BM25)**, **verifiable page-level citations**, and **client-side conversation persistence via IndexedDB**.

---

## Architecture Overview

```text
User Documents (PDF, MD, TXT)
            ↓ (Upload)
FastAPI Stateless Parser (pypdf page-level extraction)
            ↓
Browser IndexedDB Storage (Private, client-owned document & chat store)
            ↓ (Query + Selected Documents + Recent History)
FastAPI Backend Retrieval Pipeline
  ├── Query Reformulation (Conversational follow-up resolution)
  ├── Dense Semantic Retrieval (Gemini API embeddings: 768-dim)
  └── Lexical Retrieval (BM25 with tokenization & guardrails)
            ↓
Reciprocal Rank Fusion (RRF) & Optional Reranking
            ↓
Grounding & Refusal Gate (Minimum score thresholding)
            ├── Insufficient Evidence → Explicit Refusal ("I don't know")
            └── Sufficient Evidence   → Bounded Grounded Prompt Construction
                                              ↓
Generation Provider
  ├── Google Gemini (gemini-3.5-flash-lite / configurable)
  └── Extractive Provider (100% offline, deterministic fallback)
                                              ↓
Answer with Traceable Provenance (Document ID, Page Number, Passage ID)
```

---

## Key Features

- **Multi-Format Ingestion with Page Provenance:**
  Extracts text page-by-page from PDFs, as well as Markdown (`.md`) and plain text (`.txt`). Citations retain exact 1-based source page numbers.
- **Hybrid Retrieval (Dense + Sparse Fusion):**
  Combines high-dimensional semantic vector search via Google's `gemini-embedding-001` (with asymmetric `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` task types) and sparse lexical search via BM25, fused using Reciprocal Rank Fusion (RRF).
- **Grounded Generation & Anti-Hallucination Gate:**
  Enforces a strict confidence/evidence threshold. If uploaded documents lack relevant information, the system explicitly refuses to answer rather than hallucinating.
- **Verifiable Provenance & Citations:**
  Every generated claim is backed by inspectable citations linking directly to the document name, source path, page number, and passage ID.
- **Conversational Context & Query Reformulation:**
  Maintains conversational context (up to 12 recent turns) and deterministically reformulates ambiguous pronoun references (e.g., *"What are its advantages?"* → *"What are the advantages of RAG?"*) before retrieval.
- **Privacy-First, Zero-Server-Storage Architecture:**
  Documents, chat history, and citations are stored locally in the user's browser using IndexedDB. The backend is completely stateless, storing zero user data on disk. Features full JSON export and import for data backup and cross-browser portability.
- **Ultra-Lightweight Backend (<50 MB RAM):**
  Uses remote Gemini batch embedding and stateless processing to keep memory consumption under 50 MB RSS—running comfortably within memory-constrained environments like Render's 512 MiB free tier.
- **Dual Generation Mode:**
  Runs in production using Google Gemini or runs 100% offline without API keys using the built-in deterministic extractive generation provider.

---

## Tech Stack

- **Backend:** Python 3.13, FastAPI, Uvicorn, Pydantic, PyPDF, Google GenAI SDK.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, IndexedDB.
- **Retrieval Engine:** Custom in-memory Cosine Vector Index, BM25 Lexical Index with guardrails, Reciprocal Rank Fusion, Cross-Encoder Reranker.
- **Testing:** Pytest (113 automated unit, component, and integration tests).
- **Deployment:** Render (FastAPI web service) + Cloudflare Pages (React SPA).

---

## Repository Structure

```text
├── src/rag_assistant/          # Core backend application
│   ├── api.py                  # FastAPI endpoints (/health, /documents, /chat)
│   ├── bm25.py                 # BM25 lexical search implementation
│   ├── embeddings.py           # Gemini remote & teaching vector embedders
│   ├── generator.py            # Grounded generation & refusal logic
│   ├── gemini_provider.py      # Google GenAI LLM adapter
│   ├── hybrid_search.py        # Reciprocal Rank Fusion (RRF)
│   ├── multi_document_rag.py   # Multi-document provenance & pipeline
│   ├── query_reformulation.py  # Conversational query rewrite logic
│   ├── reranker.py             # Cross-encoder & inspectable rerankers
│   └── vector_search.py        # In-memory cosine similarity vector index
├── frontend/                   # React/TypeScript single-page application
│   ├── src/                    # UI components, IndexedDB storage, API client
│   └── public/                 # Static assets and SPA routing rules (_redirects)
├── tests/                      # Automated test suite (113 passing tests)
├── data/                       # Sample documentation and evaluation fixtures
├── experiments/                # Retrieval, chunking, and limit benchmark results
├── learning/                   # Educational notes, architecture decisions, and roadmap
├── render.yaml                 # Infrastructure-as-code for Render deployment
└── requirements.txt            # Minimal, lightweight Python dependencies
```

---

## Getting Started

### 1. Prerequisites
- Python 3.13+
- Node.js 18+ and npm
- (Optional) Google Gemini API Key for LLM generation and remote embeddings.

---

### 2. Backend Setup

From the project root:

```powershell
# Create and activate virtual environment
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
```

Edit `.env` to configure your Gemini API key (optional for local extractive mode):
```text
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
RAG_LLM_PROVIDER=gemini
```

Run tests to verify the installation:
```powershell
python -m pytest
```

Start the FastAPI backend service:
```powershell
$env:PYTHONPATH = "src"
uvicorn rag_assistant.api:app --reload --port 8000
```
API documentation is available at `http://127.0.0.1:8000/docs`.

---

### 3. Frontend Setup

In a second terminal window:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL printed in your terminal (typically `http://localhost:5173`).

---

### 4. Command-Line (CLI) Tools

The repository also includes standalone CLI tools for inspecting retrieval behavior:

- **End-to-end RAG with evidence display:**
  ```powershell
  $env:PYTHONPATH = "src"
  python -m rag_assistant.rag_cli data/phase-1-example.txt "How long can I remain logged in without activity?"
  ```
- **Semantic vs Keyword search comparison:**
  ```powershell
  $env:PYTHONPATH = "src"
  python -m rag_assistant.semantic_search data/phase-1-example.txt "How long can I remain logged in without activity?" --compare-keyword
  ```

---

## API Reference

### `GET /health`
Returns service status, version, and generation provider mode.

### `POST /documents`
Accepts a multipart file upload (`.pdf`, `.md`, `.txt` up to 20 MiB).
- Returns extracted document text, metadata, and page-by-page text.
- Rejects scanned/image-only PDFs with an explicit OCR notice.

### `POST /chat`
Accepts a JSON payload containing:
- `question`: The user query string.
- `documents`: List of active documents with extracted text and page provenance.
- `history`: Up to 12 recent messages for conversation context.

Returns:
- `answer`: Grounded response or explicit refusal.
- `citations`: List of citations (`document_id`, `document_name`, `page_number`, `passage_id`).
- `retrieved_evidence`: Inspectable passages used during grounding.

---

## Production Deployment

The project is preconfigured for deployment:
- **Backend on Render:** Connect the repository and deploy using `render.yaml`. Set `GEMINI_API_KEY` and `ALLOWED_ORIGINS` (pointing to your Cloudflare Pages domain).
- **Frontend on Cloudflare Pages:** Connect the repository, set root directory to `frontend`, build command to `npm ci && npm run build`, output directory to `dist`, and environment variable `VITE_API_URL` to your Render backend URL.

---

## Honest Limitations

- **Scanned PDFs:** Requires text-layer PDFs; scanned/image PDFs require an OCR pipeline (not included).
- **Rate Limiting:** Built-in rate limiting (10 queries/min/IP) is in-memory and per-process; distributed clusters require external Redis or API gateway throttling.
- **Cross-Device Sync:** Data is private to the browser profile in IndexedDB. Use the built-in JSON Export/Import buttons to migrate data across devices.
