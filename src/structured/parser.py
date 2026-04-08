"""
Parse-validate-retry pipeline for structured LLM outputs.

Sends a prompt to Claude, parses the response into a Pydantic model,
and retries with error feedback if validation fails. Returns the
parsed model and the full attempt history.

Interview talking points:
- Why include error feedback in the retry? Because LLMs can correct their
  own mistakes when told what went wrong. The success rate of retry-with-feedback
  is dramatically higher than retry-with-same-prompt. Treat the LLM like a
  collaborator that needs specific feedback, not a slot machine.
- Why return the attempt history? For the frontend's failure-recovery demo.
  Users see the raw response, the validation error, the retry prompt, and
  the eventual success. That's the teaching value of this pillar.
- Why JSON-only output? Because parsing is reliable. Asking the LLM to
  "respond with JSON" gives 95%+ valid JSON. Mixing prose with JSON drops
  that to 50%. Constrain the format to maximise parse success.
"""

import json
from dataclasses import dataclass, field
from typing import TypeVar

import anthropic
from langfuse import observe
from pydantic import BaseModel, ValidationError

from src.config import settings

T = TypeVar("T", bound=BaseModel)


@dataclass
class ParseAttempt:
    """A single parse attempt within the pipeline."""

    attempt: int
    raw_response: str
    success: bool
    parsed: dict | None = None
    error: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt,
            "raw_response": self.raw_response,
            "success": self.success,
            "parsed": self.parsed,
            "error": self.error,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass
class ParseResult:
    """The result of a parse-validate-retry pipeline run."""

    success: bool
    parsed_model: BaseModel | None
    attempts: list[ParseAttempt] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "parsed": self.parsed_model.model_dump() if self.parsed_model else None,
            "attempts": [a.to_dict() for a in self.attempts],
            "total_attempts": len(self.attempts),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }


class StructuredParser:
    """Parse-validate-retry pipeline for typed LLM outputs."""

    def __init__(self, max_retries: int = 2) -> None:
        self.max_retries = max_retries
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    @observe(name="structured_parse")
    def parse(
        self,
        prompt: str,
        schema: type[T],
        max_tokens: int = 1000,
    ) -> ParseResult:
        """Run a prompt through the parse-validate-retry pipeline.

        Args:
            prompt: The user prompt (should ask for JSON output).
            schema: A Pydantic model class to validate against.
            max_tokens: Max tokens per LLM call.

        Returns:
            ParseResult with the parsed model (if successful) and full attempt history.
        """
        result = ParseResult(success=False, parsed_model=None)
        current_prompt = self._build_initial_prompt(prompt, schema)
        last_error: str | None = None

        for attempt_num in range(1, self.max_retries + 2):
            # Build prompt — include error feedback on retries
            messages_content = (
                self._build_retry_prompt(prompt, schema, last_error)
                if last_error
                else current_prompt
            )

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": messages_content}],
            )

            raw = response.content[0].text.strip()
            input_tok = response.usage.input_tokens
            output_tok = response.usage.output_tokens
            result.total_input_tokens += input_tok
            result.total_output_tokens += output_tok

            attempt = ParseAttempt(
                attempt=attempt_num,
                raw_response=raw,
                success=False,
                input_tokens=input_tok,
                output_tokens=output_tok,
            )

            # Try to parse JSON
            try:
                # Strip markdown code fences if present
                cleaned = raw
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
                parsed_dict = json.loads(cleaned)
                attempt.parsed = parsed_dict
            except json.JSONDecodeError as e:
                attempt.error = f"Invalid JSON: {e}"
                last_error = attempt.error
                result.attempts.append(attempt)
                continue

            # Try to validate against schema
            try:
                validated = schema.model_validate(parsed_dict)
                attempt.success = True
                result.attempts.append(attempt)
                result.parsed_model = validated
                result.success = True
                return result
            except ValidationError as e:
                attempt.error = f"Schema validation failed: {e.errors()}"
                last_error = attempt.error
                result.attempts.append(attempt)
                continue

        # All retries exhausted
        return result

    def _build_initial_prompt(self, user_prompt: str, schema: type[BaseModel]) -> str:
        """Build the first attempt prompt with schema description."""
        schema_json = schema.model_json_schema()
        return f"""{user_prompt}

Respond with ONLY a JSON object matching this schema:
{json.dumps(schema_json, indent=2)}

Do not include any text outside the JSON object. Do not wrap in markdown code fences."""

    def _build_retry_prompt(
        self, user_prompt: str, schema: type[BaseModel], error: str
    ) -> str:
        """Build a retry prompt that includes the previous error as feedback."""
        schema_json = schema.model_json_schema()
        return f"""{user_prompt}

Your previous response failed validation with this error:
{error}

Please fix the error and respond with ONLY a JSON object matching this schema:
{json.dumps(schema_json, indent=2)}

Do not include any text outside the JSON object."""


parser = StructuredParser()
