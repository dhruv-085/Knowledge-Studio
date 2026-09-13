from pathlib import Path

from rag_assistant.settings import load_settings


def test_default_settings_are_safe_and_predictable() -> None:
    settings = load_settings()

    assert settings.app_name == "Technical Knowledge Assistant"
    assert settings.environment == "development"
    assert settings.data_dir == Path("data")
