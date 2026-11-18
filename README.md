# Technical Knowledge Assistant

This project is a learning-first implementation of a technical knowledge assistant. It will grow from a small, inspectable retrieval prototype into a measured RAG system.

## Phase 1: keyword-search baseline

The current milestone searches one UTF-8 text file using:

1. passage splitting at blank lines;
2. lowercase tokenization with punctuation removed;
3. an in-memory inverted index; and
4. ranking by the number of distinct query terms found in each passage.

This is not semantic search. It is a deliberately simple baseline that helps us see why embeddings will be useful later.

## Setup on Windows PowerShell

Run these commands from the project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the tests:

```powershell
python -m pytest
```

If the environment is not activated, use the project-local interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Run keyword search

Set `PYTHONPATH` in the current PowerShell session and search the example document:

```powershell
$env:PYTHONPATH = "src"
python -m rag_assistant data/phase-1-example.txt "inactive sessions"
```

The command prints the matching passage, its simple term-match score, and the terms that matched.

Try the limitation:

```powershell
python -m rag_assistant data/phase-1-example.txt "How long can I remain logged in?"
```

This returns no match even though the question is conceptually related to the document. The wording does not share enough exact terms with the passage. This is the motivation for Phase 2 semantic search.

## Phase 2: teaching embeddings and vector similarity

The first Phase 2 step is now implemented. `TeachingEmbedder` converts text into a fixed-size vector with five visible concept dimensions. The existing `VectorIndex` then ranks records with cosine similarity.

This is intentionally a teaching implementation. It demonstrates the data flow without pretending that a small hand-written vocabulary is a production language model. A later step will replace it with a pretrained embedding model.

The current flow is:

```text
text → teaching embedder → vector → cosine similarity → top-k records
```

The paraphrased question below can now retrieve the session passage through shared concept dimensions:

```text
How long can I remain logged in without activity?
```

The teaching embedder is available from Python, for example:

```python
from rag_assistant.embeddings import TeachingEmbedder

embedder = TeachingEmbedder()
vector = embedder.embed("The system terminates inactive sessions.")
print(vector)
```

Limit the number of results with `--limit`:

```powershell
python -m rag_assistant data/phase-1-example.txt python --limit 2
```

## Current architecture

```text
UTF-8 text file
       ↓
passage splitting
       ↓
tokenization
       ↓
inverted index
       ↓
keyword query
       ↓
matching passages and scores
```

The current Phase 2 extension is:

```text
text passages
       ↓
teaching embeddings
       ↓
cosine-similarity vector index
       ↓
top-k vector results
```

Run the semantic-search command and compare it with keyword search:

```powershell
$env:PYTHONPATH = "src"
python -m rag_assistant.semantic_search `
    data/phase-1-example.txt `
    "How long can I remain logged in without activity?" `
    --compare-keyword
```

The semantic command embeds the passages and query, then ranks passages by cosine similarity. The comparison shows the same query through both retrieval methods. The teaching embedder may skip passages that contain none of its known concept words; this is an intentional limitation of the transparent teaching model, not a production embedding behavior.

## Phase 3: basic RAG over one document

The first RAG pipeline is now implemented. It retrieves passages, formats them as a structured prompt, and sends that prompt to a replaceable generation provider.

Run it with:

```powershell
$env:PYTHONPATH = "src"
python -m rag_assistant.rag_cli data/phase-1-example.txt "How long can I remain logged in without activity?"
```

The command displays the retrieved evidence before the answer. The default provider is a deterministic local extractive provider, so no API key is required yet. Questions without sufficiently relevant evidence produce an explicit insufficient-evidence response.

The current Phase 3 architecture is:

```text
document → passages → embeddings → vector search → evidence
                                                   ↓
                              instructions + question + evidence
                                                   ↓
                                      generation provider → answer
```

Pretrained embeddings, original-source opening, and conversation memory are not implemented yet.

## Gemini generation provider

The local provider remains the default. To use Gemini, put your key in the
project-root `.env` file:

```text
GEMINI_API_KEY=your-key-here
```

Then run from PowerShell at the project root:

```powershell
$env:PYTHONPATH = "src"
python -m rag_assistant.rag_cli `
    data/phase-1-example.txt `
    "How long can I remain logged in without activity?" `
    --provider gemini
```

The CLI still retrieves and filters evidence locally. Only the final grounded
prompt is sent to Gemini. Use `--provider local` to stay fully offline.

## Phase 4: multi-document citations

The pipeline can now index multiple text documents in one request. Each
document supplies a stable ID, display name, optional source path, and text.
Passages receive globally unique IDs while retaining their document metadata.

The key experiment uses two documents with nearly identical session-expiration
passages:

```python
from rag_assistant.multi_document_rag import (
    DocumentInput,
    MultiDocumentRagPipeline,
)

documents = (
    DocumentInput(
        document_id="auth-guide-v1",
        document_name="Authentication Guide v1",
        text="The system terminates inactive sessions after 30 minutes.",
        source_path="data/raw/authentication-v1.md",
    ),
    DocumentInput(
        document_id="auth-guide-v2",
        document_name="Authentication Guide v2",
        text="The service ends idle sessions after 30 minutes.",
        source_path="data/raw/authentication-v2.md",
    ),
)

response = MultiDocumentRagPipeline(max_passages=2).answer(
    documents,
    "How long can I remain logged in without activity?",
)

for citation in response.answer.citations:
    print(citation.document_id, citation.document_name, citation.passage_id)
```

This proves that similar wording does not collapse provenance: the retrieved
passages remain tied to their original documents. The current extractive
provider displays the highest-ranked passage as the answer while the structured
answer retains citations for all retrieved evidence.

## Retrieval-limit experiment

Run the comparison for limits 1, 2, and 3:

```text
python -m rag_assistant.limit_experiment
```

Measurements are saved to `experiments/results/limit-comparison.json`, with a
readable summary in `experiments/results/limit-comparison.md`.

## FastAPI service

From the project root, start the local API:

```text
$env:PYTHONPATH = "src"
uvicorn rag_assistant.api:app --reload
```

The API stores uploaded documents in `data/assistant.sqlite3`. The collection
survives API restarts on this machine. TXT, Markdown, and text-based PDFs are
accepted (up to 20 MiB):

```powershell
curl.exe -F "file=@data/phase-1-example.txt" http://127.0.0.1:8000/documents
curl.exe http://127.0.0.1:8000/documents
curl.exe -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"question":"What does MAX_RETRIES control?","limit":1}'
```

`GET /documents/{document_id}` reports one document's ingestion state. The
chat response includes the answer, refusal state, retrieved evidence, and
structured citations. PDF citations retain the original 1-based page number.
The database stores extracted text and provenance, including page text for PDF
citations. It does not store the original uploaded file. Keep the SQLite file
when moving the demo to another machine. A deployed backend needs persistent
disk storage for this file; temporary hosting storage can be cleared on restart.
Image-only scanned PDFs need OCR, which is not included yet.

## Web interface

The React/TypeScript interface lives in `frontend/`. Run the API and UI in two
PowerShell windows from the project root:

```powershell
# Window 1: API
$env:PYTHONPATH = "src"
uvicorn rag_assistant.api:app --reload

# Window 2: frontend
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The UI
creates isolated conversations, attaches each uploaded document to the active
conversation, restores saved message/source history, and sends recent turns
along with retrieved evidence to Gemini when `GEMINI_API_KEY` is configured.
Without a key, the local extractive provider remains available. Set
`VITE_API_URL` in a frontend `.env` file if the API is not at
`http://127.0.0.1:8000`.
