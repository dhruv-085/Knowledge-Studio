# Phase 0 learning note: project foundation

## What exists

The project uses a `src` layout so application code is separate from tests and
project files. `Settings.from_environment()` is the first configuration
boundary. It reads safe defaults and `RAG_*` environment variables without
printing the API key. `pytest` is the only runtime development dependency.

## Why the virtual environment matters

A virtual environment gives this project its own Python packages. That keeps
the test tool version independent from other projects on the machine and makes
the setup in `README.md` repeatable.

## What was deliberately postponed

There is no web framework, LLM client, document parser, database, or vector
index yet. Adding those now would make the first lesson harder to inspect and
would commit the project to infrastructure before the retrieval behavior is
understood.

## Known limitations

The `.env.example` file documents future configuration names, but Phase 0 does
not load `.env` files automatically. Environment variables must be supplied by
the shell or development environment. The LLM key is optional until generation
is introduced, when startup validation can make it required for that command.

