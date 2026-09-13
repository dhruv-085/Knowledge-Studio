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
# Secrets will be added only when a later phase introduces an external provider.
RAG_APP_NAME=Technical Knowledge Assistant
RAG_ENVIRONMENT=development
RAG_DATA_DIR=data
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
