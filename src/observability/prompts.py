"""
Langfuse prompt management integration.

Provides utilities for fetching versioned prompts from Langfuse and
serving them at runtime. This bridges the observability and prompt
engineering pillars.

Interview talking points:
- Why manage prompts in Langfuse? Versioning, A/B testing, and linking
  prompt versions to traces. When a response is bad, you can see exactly
  which prompt version produced it.
- How does this relate to Pillar 8? Pillar 8 uses local YAML templates
  as the primary prompt management system. Langfuse is referenced as
  an alternative for teams that want cloud-hosted prompt management.
"""

from src.observability.tracing import get_langfuse


def get_prompt(name: str, version: int | None = None) -> str | None:
    """Fetch a prompt from Langfuse by name and optional version.

    If version is None, returns the latest production version.

    Returns None if the prompt is not found or Langfuse is unavailable.
    """
    try:
        langfuse = get_langfuse()
        prompt = langfuse.get_prompt(name, version=version)
        return prompt.prompt
    except Exception:
        return None


def list_prompt_names() -> list[str]:
    """List available prompt names from Langfuse.

    Note: Langfuse's Python SDK doesn't have a native list-prompts endpoint.
    This would use the REST API in production. For the workshop, we maintain
    a known set of prompt names.
    """
    return [
        "cv_parser",
        "jd_parser",
        "match_scorer",
        "screening_assessor",
        "outreach_generator",
        "reranker",
        "faithfulness_judge",
    ]
