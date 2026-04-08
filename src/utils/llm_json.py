"""
Shared helpers for parsing JSON from LLM responses.

LLMs are inconsistent about following "respond with ONLY JSON" instructions.
Sonnet usually obeys, Haiku frequently wraps output in ```json ... ``` code
fences. Either model occasionally adds a leading sentence ("Here is the JSON:")
or trailing commentary. This module centralises the parse logic so every
caller benefits from the same robustness.

Interview talking points:
- Why centralise? Because we had the same bug in five places independently
  (reranker, score_match, extract_requirements, llm_judge.faithfulness,
  llm_judge.relevance). Fixing it in one location and reusing the helper
  prevents the next caller from making the same mistake.
- Why not use Pydantic for everything? Pillar 9's structured outputs pipeline
  IS the heavy-duty option — it parses, validates, and retries on failure.
  This module is the lightweight option for callers that don't need a full
  Pydantic schema, just a robust JSON parse.
"""

import json
from typing import Any, TypeVar

T = TypeVar("T")


def strip_code_fences(text: str) -> str:
    """Strip markdown code fences from an LLM response.

    Handles all the common variations:
        ```json\n{...}\n```
        ```\n{...}\n```
        ``` json\n{...}\n```

    Returns the stripped text. If no fences are present, returns the
    text trimmed of leading/trailing whitespace.
    """
    text = text.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    # Drop the opening fence line (```json, ```, etc.)
    lines = lines[1:]
    # Drop the closing fence if present
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_llm_json(text: str, fallback: T | None = None) -> dict | list | T | None:
    """Parse a JSON object from an LLM response, with code-fence stripping.

    Args:
        text: The raw LLM response text.
        fallback: Value to return if parsing fails. Defaults to None.

    Returns:
        The parsed JSON (typically a dict), or `fallback` on parse failure.

    Use this when you want a robust parse without raising. For strict
    schema validation with retry-on-failure, use src/structured/parser.py
    (Pillar 9) instead.
    """
    try:
        cleaned = strip_code_fences(text)
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError, AttributeError):
        return fallback


def parse_llm_json_strict(text: str) -> Any:
    """Parse JSON from an LLM response, raising on failure.

    Same as parse_llm_json() but raises json.JSONDecodeError instead of
    returning a fallback. Use this when you want callers to handle the
    error explicitly.
    """
    cleaned = strip_code_fences(text)
    return json.loads(cleaned)
