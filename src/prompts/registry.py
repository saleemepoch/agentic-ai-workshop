"""
Prompt registry: loading, caching, and A/B comparison.

Provides a higher-level interface over the template loader. Caches
loaded prompts in memory and offers A/B comparison by running two
versions through the same input via Claude.

Interview talking points:
- Why cache? Loading YAML on every request is wasteful. The registry
  loads prompts once and serves them from memory. File watchers could
  reload on change in dev mode (not implemented for simplicity).
- Why A/B comparison? Because "I changed the prompt and it seems better"
  isn't evidence. Running both versions on the same input gives you a
  side-by-side diff and lets the evaluation pipeline (Pillar 6) score
  both objectively.
"""

import anthropic
from langfuse import observe

from src.config import settings
from src.prompts.loader import Prompt, list_prompts, load_prompt


class PromptRegistry:
    """In-memory cache and A/B testing for prompts."""

    def __init__(self) -> None:
        self._cache: dict[str, Prompt] = {}
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def get(self, name: str) -> Prompt:
        """Get a prompt by name. Loads from disk on first access."""
        if name not in self._cache:
            self._cache[name] = load_prompt(name)
        return self._cache[name]

    def list_all(self) -> list[Prompt]:
        """Return all available prompts (loads them if not cached)."""
        return [self.get(name) for name in list_prompts()]

    def reload(self, name: str | None = None) -> None:
        """Drop cached prompts so they reload from disk on next access."""
        if name is None:
            self._cache.clear()
        elif name in self._cache:
            del self._cache[name]

    @observe(name="prompt_ab_compare")
    def compare_versions(
        self,
        name: str,
        version_a: int,
        version_b: int,
        variables: dict[str, str],
        max_tokens: int = 800,
    ) -> dict:
        """Run the same input through two prompt versions and return both outputs.

        This is the A/B testing endpoint. Used by the frontend to demonstrate
        how prompt changes affect output quality.
        """
        prompt = self.get(name)
        v_a = prompt.get_version(version_a)
        v_b = prompt.get_version(version_b)
        if v_a is None or v_b is None:
            raise ValueError(
                f"Version not found. Available: {[v.version for v in prompt.versions]}"
            )

        rendered_a = v_a.render(**variables)
        rendered_b = v_b.render(**variables)

        # Run both through Claude
        resp_a = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": rendered_a}],
        )
        resp_b = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": rendered_b}],
        )

        return {
            "prompt_name": name,
            "version_a": {
                "version": version_a,
                "notes": v_a.notes,
                "rendered": rendered_a,
                "output": resp_a.content[0].text,
                "input_tokens": resp_a.usage.input_tokens,
                "output_tokens": resp_a.usage.output_tokens,
            },
            "version_b": {
                "version": version_b,
                "notes": v_b.notes,
                "rendered": rendered_b,
                "output": resp_b.content[0].text,
                "input_tokens": resp_b.usage.input_tokens,
                "output_tokens": resp_b.usage.output_tokens,
            },
        }


registry = PromptRegistry()
