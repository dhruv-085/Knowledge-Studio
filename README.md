# Technical Knowledge Assistant

This project is a learning-first implementation of a technical knowledge assistant. It will grow from a small, inspectable retrieval prototype into a measured RAG system.

## Phase 0: project foundation

The current milestone establishes:

- an isolated Python environment;
- a `src/` package layout;
- explicit environment-based settings;
- a minimal test suite; and
- separate locations for raw and processed data.

## Setup on Windows PowerShell

Run these commands from the project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the test:

```powershell
python -m pytest
```

Run the small settings sample:

```powershell
$env:PYTHONPATH = "src"
python -m rag_assistant.settings
```

The settings module currently reads operating-system environment variables and safe defaults. The `.env` file is documentation for local configuration at this stage; automatic `.env` loading will be introduced only if a later feature needs it.

## Current architecture

```text
configuration → settings module → application code
                         └──────→ tests
```

Document ingestion, chunking, embeddings, vector search, generation, and citations are not implemented yet.
