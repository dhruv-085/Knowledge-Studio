### data class simple example with class a DataType 

from dataclasses import dataclass

# 1. Define the Passage type
@dataclass(frozen=True)
class Passage:
    passage_id: int
    text: str

# 2. Define the SearchResult type (which nests a Passage inside it)
@dataclass(frozen=True)
class SearchResult:
    passage: Passage  # <-- Using our custom class as a data type!
    score: int
    matched_terms: tuple[str, ...]

# --- HOW TO USE IT ---

# Step A: Create an instance of a Passage
my_passage = Passage(
    passage_id=101, 
    text="Python dataclasses make code cleaner and faster to write."
)

# Step B: Pass that Passage object directly into the SearchResult
result = SearchResult(
    passage=my_passage,  # Plugs right in
    score=95,
    matched_terms=("dataclasses", "cleaner")
)

# Step C: Access the nested data using dots
print(result.score)          # Outputs: 95
print(result.passage.text)   # Outputs: "Python dataclasses make code cleaner..."


###


Phase 0: What We Built
Phase 0 is not the RAG system yet. It is the foundation that makes the future RAG system easy to build, test, and recreate.
The current project contains:
RAG based intelligent assistant/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   └── rag_assistant/
│       ├── __init__.py
│       └── settings.py
├── tests/
│   ├── conftest.py
│   └── test_settings.py
├── data/
│   ├── raw/.gitkeep
│   └── processed/.gitkeep
└── learning/
    ├── explanation.md
    ├── progress.md
    └── decisions.md
The .venv, .pytest_cache, and .git folders are generated tools or Git data, not application code.
A traditional creation order
This is not the actual Git history. It is a sensible order in which a Python developer might create the project.
1. Create the project folder
The project needs one root folder. Everything belongs inside it.
2. Create .gitignore
Usually, Git-related configuration is created very early so temporary files are not accidentally tracked.
The first line is:
__pycache__/
Python creates __pycache__ folders when it runs code. They contain temporary compiled bytecode and are not useful to commit.
3. Create a virtual environment
py -3.13 -m venv .venv
A virtual environment creates a private Python installation for this project.
Without it, packages installed for one project can interfere with another project.
4. Create requirements.txt
The first line is:
pytest>=8.3,<9
This says:
- install pytest;
- version must be at least 8.3;
- version must be lower than 9.
Pytest is the only dependency currently needed because Phase 0 is about settings and testing.
5. Create the Python package
The package directory is:
src/rag_assistant/
Then we create:
__init__.py
settings.py
6. Create the test files
The project needs tests early, not only at the end.
tests/conftest.py
tests/test_settings.py
7. Create configuration and data placeholders
These files describe configuration:
.env.example
These empty files preserve data directories in Git:
data/raw/.gitkeep
data/processed/.gitkeep
8. Create documentation and learning notes
Finally, we document how to run the project and what we learned:
README.md
learning/explanation.md
learning/progress.md
learning/decisions.md
1. src/rag_assistant/__init__.py
"""Core package for the technical knowledge assistant."""

__version__ = "0.1.0"
Line 1
"""Core package for the technical knowledge assistant."""
This is a module docstring.
A docstring is a string placed at the beginning of a Python file to describe its purpose.
This file represents the main Python package:
rag_assistant
Python packages are folders containing Python modules. The __init__.py file tells Python:
“Treat this folder as a Python package.”

Modern Python can sometimes work without __init__.py, but explicitly having it makes the project clearer and compatible with traditional Python packaging.
Line 3
__version__ = "0.1.0"
This stores the current version of the application.
The name has double underscores around it:
__version__
This is a conventional name used by Python packages.
The value:
"0.1.0"
usually means:
- major version: 0
- minor version: 1
- patch version: 0
The project is still in an early development stage, so version 0.x.x is appropriate.
This value is not used by the application yet. It is metadata for future use.
For example, later we could write:
from rag_assistant import __version__

print(__version__)
and receive:
0.1.0
2. src/rag_assistant/settings.py
This is the main Phase 0 code file.
Its job is:
Read application configuration from environment variables, and use safe defaults when configuration is missing.

Complete file:
"""Small, explicit application settings for the first project milestone."""

from dataclasses import dataclass
from os import environ
from pathlib import Path


DEFAULT_APP_NAME = "Technical Knowledge Assistant"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_DATA_DIR = Path("data")


@dataclass(frozen=True)
class Settings:
    """Configuration values used by the application."""

    app_name: str = DEFAULT_APP_NAME
    environment: str = DEFAULT_ENVIRONMENT
    data_dir: Path = DEFAULT_DATA_DIR


def load_settings() -> Settings:
    """Load settings from environment variables, falling back to safe defaults."""

    return Settings(
        app_name=environ.get("RAG_APP_NAME", DEFAULT_APP_NAME),
        environment=environ.get("RAG_ENVIRONMENT", DEFAULT_ENVIRONMENT),
        data_dir=Path(environ.get("RAG_DATA_DIR", str(DEFAULT_DATA_DIR))),
    )


if __name__ == "__main__":
    settings = load_settings()
    print(f"{settings.app_name} [{settings.environment}] data_dir={settings.data_dir}")
Line 1
"""Small, explicit application settings for the first project milestone."""
This describes the purpose of the file.
“Explicit” means we are not hiding configuration inside a large framework. We can see exactly where every setting comes from.
Lines 3–5: imports
from dataclasses import dataclass
from os import environ
from pathlib import Path
dataclass
from dataclasses import dataclass
A dataclass helps us create a simple class for storing data.
Without a dataclass, we would need to write more repetitive code manually.
For example, a normal class might require:
class Settings:
    def __init__(self, app_name, environment, data_dir):
        self.app_name = app_name
        self.environment = environment
        self.data_dir = data_dir
The dataclass generates this constructor automatically.
environ
from os import environ
environ gives us access to operating-system environment variables.
For example, PowerShell can define:
$env:RAG_ENVIRONMENT = "testing"
Python can then read it.
Environment variables are useful because configuration can change without modifying source code.
Path
from pathlib import Path
Path represents filesystem paths.
Instead of treating the data directory as an ordinary string:
"data"
we represent it as:
Path("data")
This makes filesystem operations clearer and more portable.
Lines 8–10: default values
DEFAULT_APP_NAME = "Technical Knowledge Assistant"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_DATA_DIR = Path("data")
These are safe fallback values.
Application name
DEFAULT_APP_NAME = "Technical Knowledge Assistant"
If no environment variable is supplied, the application uses this name.
Environment
DEFAULT_ENVIRONMENT = "development"
This tells us the application is running in development mode.
Later we may use values such as:
development
testing
production
Data directory
DEFAULT_DATA_DIR = Path("data")
The default location for project data is the data folder.
Keeping these values in one place avoids repeating strings throughout the application.
Lines 13–19: the Settings class
@dataclass(frozen=True)
class Settings:
    """Configuration values used by the application."""

    app_name: str = DEFAULT_APP_NAME
    environment: str = DEFAULT_ENVIRONMENT
    data_dir: Path = DEFAULT_DATA_DIR
The decorator
@dataclass(frozen=True)
A decorator modifies a class.
@dataclass tells Python to automatically generate useful methods such as a constructor.
frozen=True makes the object immutable after creation.
For example:
settings = Settings()
settings.environment = "production"
would fail because the settings object is frozen.
Why is that useful?
Configuration should normally be decided when the application starts. Accidentally changing it halfway through execution could create confusing behavior.
The class
class Settings:
This defines a new type named Settings.
A Settings object groups related configuration values together.
Instead of passing three separate values around:
app_name
environment
data_dir
we can pass one object:
settings
The docstring
"""Configuration values used by the application."""
This explains what the class represents.
The fields
app_name: str = DEFAULT_APP_NAME
This defines a field named app_name.
The type annotation says:
str
The default value is:
DEFAULT_APP_NAME
So this:
Settings()
creates an object equivalent to:
Settings(
    app_name="Technical Knowledge Assistant",
    environment="development",
    data_dir=Path("data"),
)
The other fields work the same way:
environment: str = DEFAULT_ENVIRONMENT
data_dir: Path = DEFAULT_DATA_DIR
The colon separates a variable name from its type annotation.
For example:
environment: str
means:
“The environment value should be a string.”

Python does not strictly enforce this annotation at runtime, but it helps humans, editors, and static-analysis tools.
3. The load_settings() function
def load_settings() -> Settings:
    """Load settings from environment variables, falling back to safe defaults."""

    return Settings(
        app_name=environ.get("RAG_APP_NAME", DEFAULT_APP_NAME),
        environment=environ.get("RAG_ENVIRONMENT", DEFAULT_ENVIRONMENT),
        data_dir=Path(environ.get("RAG_DATA_DIR", str(DEFAULT_DATA_DIR))),
    )
Function definition
def load_settings() -> Settings:
This defines a function named load_settings.
Its job is to load configuration.
The return annotation:
-> Settings
means:
“This function is expected to return a Settings object.”

Function docstring
"""Load settings from environment variables, falling back to safe defaults."""
This tells us the function has two sources of values:
1. environment variables;
2. default values when environment variables are missing.
Returning a Settings object
return Settings(
The function creates and returns a Settings object.
Reading the application name
app_name=environ.get("RAG_APP_NAME", DEFAULT_APP_NAME),
This asks the operating system:
“Is there an environment variable named RAG_APP_NAME?”

If it exists, its value is used.
If it does not exist, this default is used:
DEFAULT_APP_NAME
The same logic applies to the environment:
environment=environ.get("RAG_ENVIRONMENT", DEFAULT_ENVIRONMENT),
Reading the data directory
data_dir=Path(environ.get("RAG_DATA_DIR", str(DEFAULT_DATA_DIR))),
This is slightly more complicated.
environ.get() returns strings because operating-system environment variables are text.
The default data directory is a Path object:
Path("data")
So we convert it to a string for consistency:
str(DEFAULT_DATA_DIR)
Then, after retrieving the value, we convert it back into a Path:
Path(...)
This means:
"data"
becomes:
Path("data")
The result is always a Path object inside Settings.
4. The executable sample
if __name__ == "__main__":
    settings = load_settings()
    print(f"{settings.app_name} [{settings.environment}] data_dir={settings.data_dir}")
The main guard
if __name__ == "__main__":
This is a very important Python pattern.
Python gives every module a special variable called __name__.
When we run this file directly as a module:
python -m rag_assistant.settings
Python sets:
__name__ == "__main__"
Therefore, the code inside the if block runs.
But if another file imports the settings module:
from rag_assistant.settings import load_settings
then the block does not run.
That prevents importing the module from unexpectedly printing output.
Load the settings
settings = load_settings()
This calls the function and stores the returned object in a variable named settings.
Print the result
print(f"{settings.app_name} [{settings.environment}] data_dir={settings.data_dir}")
This is an f-string.
It inserts values into text.
The output is:
Technical Knowledge Assistant [development] data_dir=data
5. .env.example
# Copy this file to .env for local configuration.
# Put the real key only in .env, never in this example file.
RAG_APP_NAME=Technical Knowledge Assistant
RAG_ENVIRONMENT=development
RAG_DATA_DIR=data
RAG_LLM_PROVIDER=local
GEMINI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=
The two lines beginning with # are comments.
They explain the purpose of the file.
The remaining lines show the supported configuration names:
RAG_APP_NAME
RAG_ENVIRONMENT
RAG_DATA_DIR
This file is safe to commit because it contains no secrets.
Later, a developer might copy it:
Copy-Item .env.example .env
However, the current Python code does not automatically load .env.
At this stage, the file is documentation. The application reads operating-system environment variables directly.
That is an important limitation to understand.
6. requirements.txt
pytest>=8.3,<9
This file lists external Python packages required by the project.
Currently there is only one:
pytest
Pytest is a testing framework.
The version rule means:
8.3 <= pytest < 9
The project deliberately does not yet install:
- embedding libraries;
- PDF libraries;
- vector databases;
- LLM SDKs;
- web frameworks.
Those will be added when the corresponding problem appears.
This keeps Phase 0 small and understandable.
7. tests/conftest.py
"""Make the src-layout package importable during local test runs."""

import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
Line 1
"""Make the src-layout package importable during local test runs."""
This explains why the file exists.
The project uses a src/ layout:
src/rag_assistant/
That is a good structure, but Python does not automatically search the src folder when running tests from the project root.
This file solves that during local testing.
Import sys
import sys
The sys module gives access to Python’s runtime information.
One important value is:
sys.path
This is the list of folders Python searches when importing modules.
Import Path
from pathlib import Path
We use Path to calculate the location of the src directory.
Calculate SRC_DIR
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
This line deserves careful attention.
__file__
__file__ refers to the current file:
tests/conftest.py
.resolve()
Path(__file__).resolve()
converts the file location into an absolute path.
.parents[1]
The current file is inside:
project/tests/conftest.py
Its parents are approximately:
parents[0] → project/tests
parents[1] → project
Therefore:
.parents[1]
gets the project root.
/ "src"
This adds the src directory:
project/src
So SRC_DIR becomes:
D:\Projects\RAG based intellegent assistant\src
Add src to Python’s import path
sys.path.insert(0, str(SRC_DIR))
sys.path expects strings, so the Path is converted using:
str(SRC_DIR)
insert(0, ...) puts the src folder at the beginning of the import search path.
Now this import works in tests:
from rag_assistant.settings import load_settings
Without conftest.py, the test may fail with:
ModuleNotFoundError: No module named 'rag_assistant'
conftest.py is automatically discovered by pytest. It is not a normal application module.
8. tests/test_settings.py
from pathlib import Path

from rag_assistant.settings import load_settings


def test_default_settings_are_safe_and_predictable() -> None:
    settings = load_settings()

    assert settings.app_name == "Technical Knowledge Assistant"
    assert settings.environment == "development"
    assert settings.data_dir == Path("data")
Import Path
from pathlib import Path
The test needs Path("data") to compare against the returned data directory.
Import the function under test
from rag_assistant.settings import load_settings
This imports the function we want to test.
The test is not testing Python itself. It is checking our own configuration behavior.
Define the test function
def test_default_settings_are_safe_and_predictable() -> None:
Pytest automatically finds functions whose names begin with:
test_
The name explains what the test checks:
Default settings should be safe and predictable.

The return annotation:
-> None
means this test does not return a meaningful value.
Tests report success or failure through assertions.
Load the settings
settings = load_settings()
Because no environment variables are intentionally set inside the test, the function should use the defaults.
First assertion
assert settings.app_name == "Technical Knowledge Assistant"
This checks that the default application name is correct.
If the values are equal, the test continues.
If not, pytest reports a failure.
Second assertion
assert settings.environment == "development"
This checks the default environment.
Third assertion
assert settings.data_dir == Path("data")
This checks that the data directory is represented as the expected Path object.
The test proves that the application returns the correct defaults.
It does not yet test environment overrides. That would be a useful future improvement.
9. README.md
The README is the setup guide for a new developer.
Lines 1–3
# Technical Knowledge Assistant

This project is a learning-first implementation of a technical knowledge assistant. It will grow from a small, inspectable retrieval prototype into a measured RAG system.
The first line is the project title.
The paragraph explains the philosophy:
- start small;
- keep the system inspectable;
- gradually build toward RAG;
- measure quality instead of making unsupported claims.
Lines 5–13
## Phase 0: project foundation
This identifies the current milestone.
The bullet points explain that Phase 0 provides:
- an isolated Python environment;
- the src/ package layout;
- environment-based configuration;
- a test suite;
- locations for raw and processed data.
Lines 15–25: setup
py -3.13 -m venv .venv
Creates the virtual environment.
.\.venv\Scripts\Activate.ps1
Activates it in PowerShell.
python -m pip install --upgrade pip
Updates pip inside the active environment.
python -m pip install -r requirements.txt
Installs pytest from the dependency file.
Copy-Item .env.example .env
Copies the example configuration.
Again, .env is currently documentation rather than automatically loaded configuration.
Lines 27–31: test command
python -m pytest
Runs pytest through the current Python interpreter.
Using:
python -m pytest
is safer than using a global pytest command because it makes clear which Python installation runs the tests.
Lines 33–38: sample command
$env:PYTHONPATH = "src"
python -m rag_assistant.settings
The first command tells Python to search the src folder for packages.
The second command runs settings.py as a module.
The expected output is:
Technical Knowledge Assistant [development] data_dir=data
Line 40
The README honestly explains that:
- settings currently come from operating-system environment variables;
- safe defaults are used;
- automatic .env loading is postponed.
Lines 42–47: architecture
configuration → settings module → application code
                         └──────→ tests
This means:
1. configuration values enter the system;
2. settings.py loads and organizes them;
3. future application code will use the settings;
4. tests also verify them.
Line 49
This explicitly states what does not exist yet:
- document ingestion;
- chunking;
- embeddings;
- vector search;
- generation;
- citations.
This prevents the README from making exaggerated claims.
10. .gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
.env

data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep

.vscode/
.idea/
Python-generated files
__pycache__/
*.py[cod]
.pytest_cache/
These ignore temporary Python and pytest files.
*.py[cod] matches files such as:
.pyc
.pyo
.pyd
Virtual environment
.venv/
The virtual environment can be recreated from requirements.txt, so it should not be committed.
Secrets
.env
This is extremely important.
A real .env file may eventually contain API keys. Ignoring it helps prevent credentials from entering Git.
Only .env.example should be committed.
Raw and processed data
data/raw/*
!data/raw/.gitkeep
This means:
- ignore everything inside data/raw;
- except .gitkeep.
The same logic applies to data/processed.
The documents themselves may be large, private, or generated. The empty folder should exist, but its contents should not automatically be committed.
Editor files
.vscode/
.idea/
These are settings created by editors such as Visual Studio Code and PyCharm.
They are usually specific to one developer’s computer.
11. .gitkeep files
These files are empty:
data/raw/.gitkeep
data/processed/.gitkeep
Git tracks files, not empty directories.
Without .gitkeep, the empty data directories might not appear in the repository at all.
The file itself does nothing when Python runs. Its only purpose is to preserve the directory structure.
12. Learning files
These are not required for the application to run. They are for understanding the project.
learning/explanation.md
It explains:
- why Phase 0 exists;
- why virtual environments are useful;
- why dependency files matter;
- why src/ separates code from tests and data;
- why environment variables keep configuration outside source code.
It also records the current state:
Implemented:
- project structure;
- settings module;
- deterministic settings test.
Not implemented:
- document extraction;
- chunking;
- retrieval;
- embeddings;
- vector search;
- answer generation;
- citations.
learning/progress.md
This is a short progress tracker.
It says:
- current phase is Phase 0;
- the initial package layout and settings work are complete;
- the next discovery is verifying the setup in a fresh environment.
learning/decisions.md
This records important engineering decisions.
Python 3.13
Python 3.13 is used because it is installed locally and is currently sufficient for the small dependency set.
This decision can change later if a document or machine-learning library has compatibility requirements.
src/ layout
Application code is placed under:
src/rag_assistant/
This keeps it separate from tests and data.
The current project uses PYTHONPATH=src during commands. Later, a proper packaging configuration may remove that manual step.
Minimal dependencies
Only pytest is installed.
This prevents us from adding complex libraries before understanding why we need them.
How the files work together
When running the test:
python -m pytest
the sequence is:
pytest starts
    ↓
pytest discovers tests/conftest.py
    ↓
conftest.py adds src/ to sys.path
    ↓
test_settings.py imports load_settings
    ↓
settings.py defines Settings and load_settings
    ↓
the test calls load_settings()
    ↓
default values are returned
    ↓
assertions verify those values
When running the sample:
$env:PYTHONPATH = "src"
python -m rag_assistant.settings
the sequence is:
Python searches src/
    ↓
Python finds rag_assistant/
    ↓
Python loads settings.py
    ↓
__name__ becomes "__main__"
    ↓
load_settings() runs
    ↓
configuration is printed
The project-local test command currently passes:
1 passed
The settings sample prints:
Technical Knowledge Assistant [development] data_dir=data
One important lesson: if the virtual environment is not activated, python -m pytest may use a different Python installation that does not have pytest installed.
What Phase 0 does not solve yet
Phase 0 does not yet:
- read PDF files;
- split text into chunks;
- create embeddings;
- perform semantic search;
- use FAISS;
- call an LLM;
- generate answers;
- produce citations;
- implement a web API.
It only creates the reliable foundation for those features.

Why PYTHONPATH=src is needed

The application uses a src layout:

    project/
    └── src/
        └── rag_assistant/
            └── settings.py

When the terminal is opened in the project root, Python normally searches the project root for imports. It would look for:

    project/rag_assistant/

That folder does not exist. The real package is inside:

    project/src/rag_assistant/

The PowerShell command:

    $env:PYTHONPATH = "src"

tells Python to also search inside the src folder for importable packages.

The complete sample command is:

    $env:PYTHONPATH = "src"
    python -m rag_assistant.settings

The execution flow is:

    PowerShell sets PYTHONPATH=src
            ↓
    Python starts
            ↓
    Python reads PYTHONPATH
            ↓
    Python adds src/ to its import search locations
            ↓
    Python searches for rag_assistant
            ↓
    Python finds src/rag_assistant/
            ↓
    Python loads __init__.py
            ↓
    Python loads settings.py
            ↓
    The main guard becomes active
            ↓
    load_settings() runs
            ↓
    Settings are printed

The -m option means “run this module by its importable module name.” The file path src/rag_assistant/settings.py becomes the module name rag_assistant.settings.

Without PYTHONPATH, Python may report:

    ModuleNotFoundError: No module named 'rag_assistant'

The virtual environment does not automatically solve this import problem. The virtual environment controls which Python interpreter and installed packages are used. It does not automatically know that this project stores application code inside src.

Tests work without manually setting PYTHONPATH because tests/conftest.py performs a similar operation:

    SRC_DIR = Path(__file__).resolve().parents[1] / "src"
    sys.path.insert(0, str(SRC_DIR))

Therefore, the settings sample uses PYTHONPATH while pytest uses conftest.py to make the package importable.

PYTHONPATH is temporary for the current PowerShell session. It does not modify project files. Later, a pyproject.toml file and editable package installation can remove the need for this manual command.

The expected sample output is:

    Technical Knowledge Assistant [development] data_dir=data

Explanation style going forward

Future learning notes should explain each meaningful milestone in the same beginner-friendly way:

1. State the problem being solved.
2. Explain the concept from first principles.
3. Describe the traditional construction order without pretending to know exact timestamps.
4. Explain each affected file and important line of code.
5. Trace the runtime execution flow.
6. Explain why the design was chosen and what alternatives exist.
7. Record what is not implemented yet.
8. End with a short next discovery.
## Phase 2: teaching embeddings

An embedding is a numerical representation of text. The vector is useful only when related text receives related vectors. The teaching embedder currently uses five named concept dimensions and counts recognized words in each dimension.

For example, both `inactive sessions` and `logged in` contribute to the authentication dimension. This gives related wording a shared numerical direction even when the exact phrases differ.

The current Phase 2 flow is:

```text
text
  ↓
teaching embedder
  ↓
fixed-size vector
  ↓
cosine similarity
  ↓
in-memory VectorIndex
  ↓
top-k records
```

This embedder is intentionally a learning tool, not a general-purpose language model. It demonstrates the interface and data flow before we introduce a pretrained embedding model.

# Current Project State

Implemented:
- Phase 1 keyword-search baseline;
- cosine similarity with dimension validation;
- in-memory vector index with deterministic ranking;
- deterministic teaching embedder; and
- tests for vector shapes, repeatability, related concept dimensions, and unknown text.

Not implemented yet:
- pretrained embeddings;
- generation;
- citations; and
- conversation memory.

## Provider-neutral generation boundary

The generator does not need to know which company serves the model. It accepts
a `GenerationProvider` with one operation: `generate(prompt) -> str`. The
prompt contains instructions, the question, and retrieved evidence.

`ExtractiveProvider` remains the default local implementation. `GeminiProvider`
is an alternative adapter: it converts the same `GenerationPrompt` to plain
text, sends it through Google's `google-genai` client, and returns Gemini's
text. Retrieval, evidence filtering, citations, and refusal behavior stay in
our code and are therefore provider-independent.

The flow is:

```text
question
  ↓
retrieval and evidence filtering
  ↓
GenerationPrompt
  ↓
GenerationProvider
  ├── ExtractiveProvider (local, deterministic)
  └── GeminiProvider (remote model)
  ↓
answer text + citations owned by our pipeline
```

The Gemini key belongs in the project-root `.env` file as
`GEMINI_API_KEY=...`. It is ignored by Git. The provider loads that value only
when the Gemini provider is selected; local runs do not need a key.

## Semantic search command

`semantic_search.py` connects the existing pieces into an executable retrieval flow:

```text
document
  ↓
passages
  ↓
teaching embeddings
  ↓
VectorIndex
  ↓
cosine-similarity ranking
  ↓
top-k passages
```

With `--compare-keyword`, the same query is sent through both retrieval methods. Keyword search rewards exact word overlap. Semantic search compares the direction of the query and passage vectors, so related concept words can match even when the wording differs.

The teaching embedder can reject a passage when none of its small, hand-written concept vocabulary appears. The command reports those passage IDs instead of pretending that every passage was represented. A pretrained embedder later will produce vectors for ordinary text, although it will still have its own quality limitations.

### First comparison observation

On `data/phase-1-example.txt` with the query `How long can I remain logged in without activity?`:

- semantic search ranked the session passage first with cosine similarity about `0.981`;
- keyword search returned unrelated passages because words such as `how`, `can`, and `in` appeared elsewhere; and
- the `MAX_RETRIES` passage was skipped because the teaching vocabulary did not recognize its words.

The result demonstrates both the promise and the limitations of the toy system. Semantic similarity can connect related wording, but its score depends on the dimensions and counts produced by the embedder. Keyword matching is transparent and useful for exact terms, but common-word overlap can create false positives.

## Phase 3: basic RAG over one document

RAG has two different jobs:

1. **Retrieval** finds passages that may contain the answer.
2. **Generation** turns those passages into a response.

The Phase 3 flow is:

```text
document
  ↓
passages and embeddings
  ↓
vector retrieval
  ↓
retrieved evidence
  ↓
GenerationPrompt
  ├── instructions
  ├── question
  └── evidence
  ↓
GenerationProvider
  ↓
answer or insufficient-evidence refusal
```

The prompt is kept as a structured object so we can inspect exactly what would be sent to an LLM. The provider is a small interface: an external LLM can be added later without changing retrieval or context construction.

For now, `ExtractiveProvider` is deliberately local and deterministic. It returns the first usable passage. This is not intended to imitate a language model; it makes the grounding boundary visible and keeps tests independent of API credentials.

The generator refuses before calling the provider when no retrieved passage reaches the minimum similarity score. This is a useful safety boundary, but it is not a guarantee against hallucination once a real LLM is connected. Retrieval can still be wrong, incomplete, or ambiguous.

# Current Project State

Implemented:
- Phase 1 keyword-search baseline;
- Phase 2 teaching embeddings, cosine similarity, and semantic search;
- Phase 3 one-document RAG pipeline;
- structured grounded prompts;
- replaceable generation-provider interface;
- deterministic local extractive provider; and
- insufficient-evidence refusal tests.

Not implemented yet:
- pretrained embeddings;
- external LLM generation;
- original-source opening; and
- conversation memory.

## Phase 4: provenance begins at ingestion

The first Phase 4 change adds provenance fields to every `Passage` and carries
them into `VectorRecord`:

- `document_id`
- `document_name`
- `source_path`
- `page_number`
- `section`

This matters because a citation cannot be reliably reconstructed from answer
text after retrieval. The source information must travel with the chunk through
indexing and retrieval. The current test proves that semantic retrieval keeps
the metadata attached to the selected record.

The metadata fields have defaults so the Phase 1–3 one-document examples keep
working. That is a temporary compatibility choice, not a claim that all future
documents have the same source.

## Phase 4: citations at the answer boundary

`Evidence` now carries the same provenance fields as the vector record. A
supported `GeneratedAnswer` exposes a tuple of structured `Citation` objects,
while the local extractive provider also renders a readable source reference
in the answer text.

This gives us two useful representations:

- structured citation data for a CLI, API, or web interface to consume;
- human-readable citation text for inspecting the local prototype.

An insufficient-evidence answer returns no citations. This prevents the system
from displaying a source merely because an answer object exists. A citation is
created only from evidence that passed the generator's minimum-score boundary.

## Phase 4: multiple documents with distinct citations

`DocumentInput` is the ingestion boundary for the current text-only lesson.
It gives each document a stable ID, display name, optional source path, and
text. `MultiDocumentRagPipeline` splits every document into passages, assigns
globally unique passage IDs, and copies the document metadata onto each one.

The important experiment uses two passages that both describe 30-minute idle
session expiration. The teaching embedder retrieves both. The observed
citations retain different document IDs, names, source paths, and passage IDs.
Therefore, similar content does not make the sources indistinguishable.

The pipeline currently receives text in memory. It does not yet read the
original files or know page numbers, so source opening and page-aware parsing
remain future ingestion work.

## Phase 4: the document-loading boundary

`document_loader.load_document()` is the first small boundary between a source
file and the RAG pipeline. It reads one UTF-8 text file and returns a
`DocumentInput` containing:

- the caller-provided stable document ID;
- a display name, defaulting to the file name;
- the original source path; and
- the extracted text.

The loader does not split text, create embeddings, or search. Keeping those
responsibilities separate means a future PDF or DOCX loader can produce the
same `DocumentInput` without changing retrieval code. Missing files and invalid
UTF-8 are still reported by the existing file-reading operation rather than
hidden or silently replaced.

## Phase 6: a common text-ingestion contract

The loader now accepts `.txt`, `.md`, and `.markdown` files through the same
interface. Markdown is intentionally preserved as text for now: headings and
paragraphs remain visible to the later chunking step, and we have not yet
introduced a Markdown parser before we know which structure we need.

Unsupported extensions are rejected before reading. This makes the boundary
explicit: the loader decides whether a source format is supported, while the
retrieval pipeline continues to receive only `DocumentInput` values.

PDF and DOCX are deliberately not implemented yet. They will need format-
specific extraction and may provide metadata such as page numbers. Adding
those parsers is the next ingestion experiment, after we compare chunking
behavior on the text formats we can inspect directly.

## Phase 6: first chunking comparison

The first chunking experiment uses the same Markdown fixture and a target of
140 characters for every strategy:

1. fixed-size windows;
2. fixed-size windows with 35 characters of overlap; and
3. paragraph-aware grouping.

The fixed-size strategy produced 5 chunks but cut through words and the
`SESSION_TIMEOUT_MINUTES` identifier. The overlapping strategy produced 7
chunks and repeated boundary text, so it preserved some context at the cost
of duplication but still cut words in places. Paragraph-aware grouping
produced 8 chunks and preserved blank-line paragraphs and readable sentences.
It can exceed the target for a long paragraph and does not yet understand
that a Markdown heading may deserve special treatment.

This experiment demonstrates why chunking is a retrieval design choice, not
just string slicing. The observations are from one fixture; retrieval quality
must be measured on questions before selecting a general strategy.

The follow-up Markdown-aware strategy treats headings as context for the next
content block and splits blocks that exceed the target. This improves the
meaning of a heading-only chunk and prevents an unbounded long paragraph. A
remaining limitation is that later subchunks from a long heading section do
not repeat the heading. Carrying a heading path as metadata is a likely next
improvement.

# Current Project State

Implemented:
- Phase 1 keyword-search baseline;
- Phase 2 teaching embeddings, cosine similarity, and semantic search;
- Phase 3 one-document RAG pipeline;
- Phase 4 provenance-aware multi-document text ingestion and citations;
- Phase 5 bounded conversation history and basic query reformulation;
- Phase 6 UTF-8 TXT/Markdown loading; and
- first chunking comparison with fixed, overlapping, paragraph-aware, and Markdown-aware strategies.

Not implemented yet:
- richer heading-path metadata on Markdown chunks;
- PDF/DOCX parsing;
- pretrained embeddings;
- external LLM generation in the application path.

## Retrieval evaluation: coverage before ordering

The current evaluation set contains nine questions with manually reviewed
expected passage IDs. The experiment compares keyword, semantic, and hybrid
retrieval at depth five.

- Recall@5 asks whether expected evidence appears in the first five results.
- Precision@5 asks how many of those result slots are relevant.
- MRR rewards placing the first relevant passage near rank one.

The current results are hybrid Recall@5 0.889 and MRR 0.833. This supports
using hybrid as a first-stage candidate retriever for this fixture, but the
fixture is too small for broad claims. Reranking was then added as a separate
second stage. The transparent reranker improved MRR to 0.889 while Recall@5
stayed 0.889. Precision@5 stayed 0.178 because the same candidates were
reordered and the fixture has only three passages.

## Reranking: improve ordering after retrieval

First-stage retrieval answers: "Which passages might be relevant?" It is
optimized for speed and coverage. A reranker answers: "Among these candidates,
which best matches this question?" It can inspect each query-passage pair more
carefully, but it cannot search passages that were not included in the
candidate set.

The current teaching reranker uses visible lexical evidence: it removes common
function words, counts shared content terms, and adds a small bonus for exact
identifiers. This is useful for understanding the boundary before introducing
a pretrained cross-encoder. Its limitation is equally important: it does not
understand synonyms or paraphrases by itself.

The pretrained comparison uses a cross-encoder after hybrid retrieval. A
cross-encoder receives the question and one candidate passage together, so the
transformer can compare them jointly. This often makes it a stronger pairwise
relevance scorer than a transparent term-overlap rule, but it must run once per
candidate pair and therefore costs more latency. It also cannot recover a
relevant passage that the first-stage retriever did not include.

On the current nine-question fixture, hybrid Precision@1 was 0.778, while both
the teaching reranker and `cross-encoder/ms-marco-MiniLM-L6-v2` reached 0.889.
At Precision@2 all three scored 0.444, and both rerankers reached MRR 0.889
compared with hybrid MRR 0.833. The measured average latency was 0.13 ms/query
for the teaching reranker and 43.44 ms/query for the cross-encoder. These are
fixture-specific results, not a general model comparison.

## Current Project State (updated)

Implemented:
- provider-neutral `GenerationProvider` boundary;
- deterministic local extractive provider remains the default;
- Gemini adapter using the `google-genai` SDK;
- CLI provider selection with `--provider local|gemini`; and
- no-network tests for Gemini prompt forwarding and missing-key behavior.

Not implemented yet:
- pretrained embeddings;
- streaming, retries, and token/cost measurement for external generation;
- PDF/DOCX parsing and page-aware source opening; and
- broader evaluation of answer faithfulness and citation correctness.

## Broader hybrid retrieval with lexical guardrails

The multi-document pipeline now runs lexical search for every query and fuses
those results with semantic results using reciprocal rank fusion. This is
broader hybrid retrieval: lexical search is no longer only an exact-identifier
fallback.

The lexical query ignores weak evidence terms such as `system` and `service`
along with common question words. Exact identifiers such as `MAX_RETRIES`
remain searchable. This matters because a generic word can occur in a passage
without the passage answering the question.

RRF scores are useful for ordering candidates but are on a different scale from
cosine similarity. Therefore, the generator does not apply the old absolute
similarity threshold to a positive `rrf_score`; an empty fused result still
causes the existing insufficient-evidence refusal.

On the 18-question fixture, broader hybrid retrieval improved Recall@1 from
0.778 to 0.889 and MRR from 0.833 to 0.889. Recall@2 and Recall@5 stayed at
0.889. The result is encouraging but fixture-specific; a larger evaluation set
and a real lexical ranker such as BM25 are still needed.

## Current Project State (latest)

Implemented:
- broad lexical-plus-semantic candidate retrieval;
- reciprocal-rank fusion with provenance-preserving context;
- lexical guardrails for generic query terms;
- exact-identifier retrieval through the fused path; and
- score-space-aware grounding behavior.

Not implemented yet:
- a larger representative retrieval evaluation set; and
- production persistence, API serving, and observability.

## Pretrained dense retrieval and hybrid comparison

The semantic index now accepts a small `TextEncoder` protocol rather than
depending on the teaching embedder. This makes the retrieval mechanism
independent from the encoder implementation: both encoders produce a vector,
and the same `VectorIndex` ranks vectors by cosine similarity.

`TeachingEmbedder` is intentionally simple and interpretable. It maps a small
hand-written vocabulary to concept counts. `PretrainedSentenceEncoder` uses
`all-MiniLM-L6-v2`, a pretrained sentence-transformer model, to map a sentence
to a normalized high-dimensional vector. Normalization makes cosine similarity
especially convenient because vector length no longer represents sentence
length in the comparison.

The retrieval experiment now compares BM25, teaching semantic retrieval,
pretrained semantic retrieval, and their hybrid variants. BM25 scores shared
terms using rarity, term frequency, and document-length normalization. The
pretrained encoder can match different wording, while BM25 can preserve exact
technical identifiers. Reciprocal rank fusion combines their ranked lists
without pretending that BM25 and cosine scores have the same numeric scale.

On the current 18-question, three-passage fixture, BM25 achieved Recall@1 and
MRR of 0.833. Pretrained semantic retrieval achieved 1.000 for both, and BM25
plus pretrained retrieval also achieved 1.000. This is evidence for the
fixture, not a general benchmark: the corpus is too small to prove that
fusion always improves the ranking.

# Current Project State

Implemented:
- BM25 lexical retrieval;
- teaching semantic retrieval;
- pretrained sentence-encoder retrieval;
- BM25 plus pretrained reciprocal-rank-fusion retrieval; and
- repeatable comparison metrics for lexical, dense, and hybrid retrieval.

Not implemented yet:
- a larger representative retrieval evaluation set;
- production model serving/caching and latency controls; and
- production persistence, API serving, and observability.

## BM25 lexical ranking

The original guarded lexical matcher gives a passage one point for each
distinct query term it contains. This is transparent, but it treats a rare
technical identifier and a common word as equally valuable, and it ignores
passage length and repeated terms.

BM25 keeps the same tokenization and lexical guardrails, then changes only the
score. A matching term contributes more when it is rare across the collection,
and repeated occurrences help with diminishing returns. A length-normalization
factor prevents long passages from winning merely because they contain more
words.

BM25 is still lexical retrieval. It cannot connect unrelated wording such as
"remain logged in without activity" with a passage that only says
"inactive sessions expire" unless a shared guarded term exists. Semantic
retrieval is still needed for that kind of paraphrase.

On the current 18-question, three-passage fixture, BM25 tied the guarded
matcher at Recall@1 0.833, MRR 0.833, and Recall@5 0.833. The hybrid versions
also tied at Recall@1 0.889 and MRR 0.889. This is an honest no-improvement
result: the fixture does not contain enough competing partial matches for
BM25's richer scoring to affect the order.

## Current Gemini integration

The real LLM path is connected through the provider-neutral generation
boundary. Retrieval and the insufficient-evidence gate remain local; Gemini
receives only the grounded prompt after usable evidence has been selected.

The provider uses Google's GenAI Interactions API and reads the model from
`GEMINI_MODEL`, defaulting to `gemini-3.5-flash-lite`. The local extractive
provider remains available for offline tests and demonstrations. Provider
tests inject a fake client, so the normal test suite does not require a live
API call or expose a real key.

## Phase 11: upload documents through the API

The FastAPI service accepts PDF, TXT, and Markdown files, lists uploaded
documents, reports their readiness, and runs chat over the current collection.
Uploads are capped at 20 MiB. Extracted text and provenance are stored in
`data/assistant.sqlite3`, so documents survive an API restart on a machine with
persistent local storage. The original uploaded binary is not stored.

PDFs are extracted page by page. That page number travels with each passage
through retrieval and appears in citations. A scanned PDF contains page images
instead of a text layer, so `pypdf` cannot read its words; this version rejects
it and explains that OCR is needed.

## Conversations and the web interface

Conversations, messages, answer citations, and retrieved passage text are saved
in SQLite. Uploaded documents are linked to one conversation, so a new chat
starts with an empty source collection. The API reformulates common pronoun
follow-ups for retrieval and gives recent saved turns plus retrieved evidence
to Gemini. If no Gemini key is configured, the local extractive provider
remains available. The React interface restores message and source history
from the API; it does not invent assistant turns in the browser.

# Current Project State

Implemented:
- local RAG pipeline with hybrid retrieval, reranking, citations, and refusal behavior;
- FastAPI uploads, per-conversation document lists, persistent conversations, and grounded chat;
- follow-up query reformulation and recent conversation context in generation;
- React/TypeScript chat UI with isolated uploads, saved history, expandable sources, draft chats, stable first-question titles, chat deletion, and a collapsible workspace panel;
- immediate user-message display, explicit UTC timestamp handling in the Asia/Kolkata display timezone, and basic accidental-input / per-chat rate safeguards;
- PDF text extraction with page-number provenance.

Not implemented yet:
- OCR for scanned PDFs, PDF download/source viewing, and production deployment/operations.

## Chat behavior and request safeguards

An empty chat is kept as a browser draft and is only saved when a document is
added or a message is sent. The first user message is the stable chat title.
Messages are shown optimistically in the interface; the API saves the user
message before running retrieval and generation so it remains visible during
slow model responses.

SQLite's `CURRENT_TIMESTAMP` is UTC. The API marks timestamps with `Z`, and the
interface formats them in `Asia/Kolkata`; a timezone marker prevents browsers
from treating a UTC time as local time. The API also rejects obvious low-signal
input before provider selection and allows at most ten questions per chat in a
rolling minute. These checks reduce accidental calls but do not replace
provider-level quotas or account-wide rate limiting.

