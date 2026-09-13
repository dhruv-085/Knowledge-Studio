# Engineering Decisions

## Use Python 3.13 for the first environment

Python 3.13 is installed locally and provides a conservative compatibility target for the small dependency set. The choice can be revisited when model or document libraries are introduced.

## Use a `src/` package layout

Application code lives under `src/rag_assistant/`, separate from tests and data. The Phase 0 commands set `PYTHONPATH=src` explicitly; a later packaging step can replace that setup when it provides a clear benefit.

## Keep Phase 0 dependencies minimal

Only `pytest` is installed because the first executable lesson is configuration plus testing. Embedding, parsing, vector-search, and LLM libraries will be added when their corresponding problems appear.
