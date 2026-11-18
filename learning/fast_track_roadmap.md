# Fast-Track Roadmap

## Goal

Build a resume-ready Intelligent Technical Knowledge Assistant quickly while
understanding the essential AI/ML and software engineering concepts.

## Session Startup Checklist

At the beginning of every session:

1. Read `AGENTS.md`.
2. Read `plan.md`.
3. Read this file.
4. Read the relevant parts of `learning/explanation.md`.
5. Read `learning/progress.md`.
6. Inspect the actual code and tests.
7. Identify the next incomplete milestone.
8. Explain the next problem, concept, files, and expected result before editing.

## Priority Order

1. Connect retrieval to a real LLM.
2. Preserve grounded answers and insufficient-evidence behavior.
3. Add reliable citations and provenance.
4. Support PDF, TXT, and Markdown documents.
5. Add evaluation experiments and measured results.
6. Expose the assistant through FastAPI.
7. Improve README, architecture documentation, and demo workflow.
8. Add frontend, database, Docker, and deployment only after the core is stable.

## Concepts We Must Not Skip

- RAG architecture and grounding
- Text extraction and chunking
- Tokenization and context limits
- Embeddings and vector representations
- Cosine similarity and Top-K retrieval
- Keyword, semantic, and hybrid search
- Reranking and query reformulation
- Metadata, provenance, and traceable citations
- Prompt design and hallucination limitations
- “I don’t know” behavior
- Retrieval evaluation: Recall, Precision, and MRR
- Generation evaluation: faithfulness and citation correctness
- Latency, cost, accuracy, and scalability trade-offs
- Python project structure, testing, configuration, APIs, and error handling

## Learning Rule

For every meaningful change:

Problem → Prediction → Concept → Design → Small implementation →
Test → Observe → Understand → Document

Never claim a feature, metric, or capability unless it has been implemented
and verified.

## Resume-Ready Definition

The project is resume-ready when it has:

- A working end-to-end RAG pipeline
- Real LLM-generated answers
- At least TXT and Markdown ingestion
- Traceable citations
- Explicit insufficient-evidence behavior
- Retrieval evaluation results
- Automated tests
- A clear README and architecture diagram
- Honest, evidence-based project claims

## Current Focus

Connect the existing retrieval and reranking pipeline to a real LLM while
keeping the retrieved context visible and answers grounded.
