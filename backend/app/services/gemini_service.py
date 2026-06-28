import logging
from functools import lru_cache
from typing import Any, Protocol

from google import genai
from google.genai import types

from app.config.settings import Settings
from app.core.errors import GeminiConfigurationError, GeminiProviderError

logger = logging.getLogger(__name__)

DEFAULT_MAX_OUTPUT_TOKENS = 8_192


class JsonGenerationService(Protocol):
    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
    ) -> str: ...


@lru_cache(maxsize=1)
def _build_client(api_key: str, timeout_seconds: int) -> genai.Client:
    """Cache a single Gemini client per process to avoid repeated TCP setup."""
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_seconds),
    )


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
    ) -> str:
        if not self._settings.gemini_api_key:
            raise GeminiConfigurationError()

        client = _build_client(
            self._settings.gemini_api_key,
            self._settings.gemini_timeout_seconds,
        )

        try:
            response = await client.aio.models.generate_content(
                model=self._settings.gemini_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self._settings.gemini_temperature,
                    candidate_count=1,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                    response_json_schema=response_schema,
                ),
            )
        except GeminiConfigurationError:
            raise
        except Exception:
            logger.exception("Gemini provider call failed")
            raise GeminiProviderError()

        if not response or not getattr(response, "text", None):
            logger.warning("Gemini returned an empty response body")
            raise GeminiProviderError()

        return response.text