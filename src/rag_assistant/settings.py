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
