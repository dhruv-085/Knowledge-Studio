"""Gemini implementation of the provider-neutral generation boundary."""

from os import environ
from typing import Any

from .generator import GenerationPrompt


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


class GeminiProvider:
    """Generate grounded answers with Google's Gemini API."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        try:
            from dotenv import load_dotenv
        except ImportError:
            load_dotenv = None

        if load_dotenv is not None:
            load_dotenv()

        self.model = model or environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        configured_key = api_key or environ.get("GEMINI_API_KEY")

        if client is not None:
            self.client = client
            return

        if not configured_key:
            raise ValueError(
                "GEMINI_API_KEY is required when using the Gemini provider"
            )

        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError(
                "The Gemini provider requires the google-genai package. "
                "Install the project requirements first."
            ) from error

        self.client = genai.Client(api_key=configured_key)

    def generate(self, prompt: GenerationPrompt) -> str:
        """Send the complete grounded prompt to Gemini and return its text."""

        interaction = self.client.interactions.create(
            model=self.model,
            input=prompt.as_text(),
        )
        text = interaction.output_text

        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response")

        return text.strip()
