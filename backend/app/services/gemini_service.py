import copy
import logging
from functools import lru_cache
from typing import Any, Protocol

from google import genai
from google.genai import types

from app.config.settings import Settings
from app.core.errors import GeminiConfigurationError, GeminiProviderError

logger = logging.getLogger(__name__)

DEFAULT_MAX_OUTPUT_TOKENS = 8_192

# JSON Schema keywords that Google's Gemini structured output does not accept.
_UNSUPPORTED_SCHEMA_KEYWORDS: frozenset[str] = frozenset({
    "additionalProperties",
    "title",
    "maxLength",
    "minLength",
    "maximum",
    "minimum",
    "maxItems",
    "minItems",
    "const",
    "default",
    "$defs",
})


def _clean_schema(
    schema: Any,
    root_defs: dict[str, Any] | None = None,
    *,
    _is_properties_map: bool = False,
) -> Any:
    """Recursively clean a Pydantic JSON Schema for Gemini compatibility.

    Gemini's structured output accepts a strict subset of JSON Schema.  This
    function:

    * Resolves ``$ref`` references inline using the top-level ``$defs``.
    * Strips keywords Gemini does not support (``title``, ``additionalProperties``,
      length / count constraints, etc.).
    * Collapses ``anyOf`` unions to ``{"type": "string"}``.
    * Guarantees that every ``required`` entry exists in ``properties``.
    * Deep-copies resolved ``$ref`` targets to avoid shared-dict mutation.
    """
    # Capture the top-level $defs on the first call.
    if root_defs is None and isinstance(schema, dict):
        root_defs = schema.get("$defs", {})

    if isinstance(schema, dict):
        # ── $ref resolution ──────────────────────────────────────────
        if "$ref" in schema:
            ref_key = schema["$ref"].split("/")[-1]
            resolved = root_defs.get(ref_key, {}) if root_defs else {}
            return _clean_schema(copy.deepcopy(resolved), root_defs)

        # ── Properties-map pass ──────────────────────────────────────
        # The value of a ``"properties"`` key is a dict whose keys are
        # *property names*, NOT JSON-Schema keywords.  We must preserve
        # every key and only recurse into its value (which IS a schema).
        if _is_properties_map:
            return {
                prop_name: _clean_schema(prop_value, root_defs)
                for prop_name, prop_value in schema.items()
            }

        # ── Regular schema-object pass ───────────────────────────────
        has_any_of = "anyOf" in schema

        cleaned: dict[str, Any] = {}
        for key, value in schema.items():
            if key in _UNSUPPORTED_SCHEMA_KEYWORDS:
                continue
            if key == "anyOf":
                # Gemini does not support anyOf; skip the key itself.
                continue
            if key == "properties":
                # Recurse with the flag so property names are preserved.
                cleaned[key] = _clean_schema(
                    value, root_defs, _is_properties_map=True
                )
            else:
                cleaned[key] = _clean_schema(value, root_defs)

        # Replace anyOf with a simple string type when no type was set.
        if has_any_of and "type" not in cleaned:
            cleaned["type"] = "string"

        # ── Enforce required ⊆ properties ────────────────────────────
        if "required" in cleaned and "properties" in cleaned:
            valid_keys = set(cleaned["properties"].keys())
            cleaned["required"] = [
                r for r in cleaned["required"] if r in valid_keys
            ]
            if not cleaned["required"]:
                del cleaned["required"]

        return cleaned

    if isinstance(schema, list):
        return [_clean_schema(item, root_defs) for item in schema]

    return schema


def _validate_schema(schema: Any, path: str = "root") -> None:
    """Recursively assert that every ``required`` entry exists in ``properties``.

    Raises :class:`ValueError` with a descriptive message if the invariant is
    violated, so an invalid schema is never sent to Gemini.
    """
    if not isinstance(schema, dict):
        return

    if "required" in schema and "properties" in schema:
        prop_keys = set(schema["properties"].keys())
        required = set(schema["required"])
        orphans = required - prop_keys
        if orphans:
            raise ValueError(
                f"Schema validation failed at '{path}': "
                f"required fields {orphans} are not in properties {prop_keys}"
            )

    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            _validate_schema(prop_schema, path=f"{path}.{prop_name}")

    if "items" in schema and isinstance(schema["items"], dict):
        _validate_schema(schema["items"], path=f"{path}.items")


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
        http_options=types.HttpOptions(timeout=timeout_seconds * 1000),
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

        cleaned = _clean_schema(response_schema)
        _validate_schema(cleaned)

        try:
            response = await client.aio.models.generate_content(
                model=self._settings.gemini_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self._settings.gemini_temperature,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                    response_schema=cleaned,
                ),
            )
        except GeminiConfigurationError:
            raise
        except Exception as e:
            logger.exception("Gemini API request failed")
            raise GeminiProviderError() from e

        if not response or not getattr(response, "text", None):
            logger.warning("Gemini returned an empty response body")
            raise GeminiProviderError()

        return response.text