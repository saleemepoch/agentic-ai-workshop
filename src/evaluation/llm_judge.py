"""
LLM-as-judge: automated quality scoring for generation outputs.

Uses Claude to score two dimensions:
1. **Faithfulness**: Is the response grounded in the provided context?
   (Does it make claims that aren't supported by the retrieved chunks?)
2. **Relevance**: Does the response actually answer the query?

Interview talking points:
- Why LLM-as-judge? Manual review doesn't scale. You can't have a human
  read every response in CI. LLM-as-judge gives you automated quality
  scoring that correlates well with human judgment.
- Isn't this circular? Partly — we're using an LLM to judge an LLM.
  But the judge sees the context, the query, AND the response. It's
  judging faithfulness to context, not general correctness. This is
  more reliable than it sounds.
- Why two dimensions? A response can be faithful but irrelevant (accurately
  quotes context but doesn't answer the question) or relevant but
  unfaithful (answers the question but makes things up). You need both.
"""

import anthropic
from langfuse import observe

from src.config import settings
from src.utils.llm_json import parse_llm_json


class LLMJudge:
    """Scores LLM outputs for faithfulness and relevance."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    @observe(name="judge_faithfulness")
    def score_faithfulness(
        self, context: str, response: str
    ) -> dict[str, float | str]:
        """Score whether the response is grounded in the provided context.

        Returns:
            Dict with score (0.0-1.0) and reasoning.
        """
        result = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""Score the faithfulness of this response to the provided context.
Faithfulness means: every claim in the response is supported by the context.
Unfaithful means: the response makes claims not found in the context (hallucination).

Score from 0.0 to 1.0:
- 0.0: Completely unfaithful, makes up information not in context
- 0.5: Partially faithful, some claims supported, some not
- 1.0: Fully faithful, every claim is supported by context

Respond with ONLY a JSON object: {{"score": <float>, "reasoning": "<one sentence>"}}

Context:
{context[:2000]}

Response:
{response[:1000]}""",
            }],
        )

        parsed = parse_llm_json(result.content[0].text)
        if not isinstance(parsed, dict):
            return {
                "score": 0.0,
                "reasoning": f"Failed to parse judge response: {result.content[0].text[:120]}",
            }
        return {
            "score": float(parsed.get("score", 0)),
            "reasoning": str(parsed.get("reasoning", "")),
        }

    @observe(name="judge_relevance")
    def score_relevance(
        self, query: str, response: str
    ) -> dict[str, float | str]:
        """Score whether the response answers the query.

        Returns:
            Dict with score (0.0-1.0) and reasoning.
        """
        result = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""Score the relevance of this response to the query.
Relevance means: the response directly addresses what the query is asking.
Irrelevant means: the response talks about something else or misses the point.

Score from 0.0 to 1.0:
- 0.0: Completely irrelevant, doesn't address the query at all
- 0.5: Partially relevant, addresses some aspects but misses others
- 1.0: Fully relevant, directly and completely addresses the query

Respond with ONLY a JSON object: {{"score": <float>, "reasoning": "<one sentence>"}}

Query:
{query}

Response:
{response[:1000]}""",
            }],
        )

        parsed = parse_llm_json(result.content[0].text)
        if not isinstance(parsed, dict):
            return {
                "score": 0.0,
                "reasoning": f"Failed to parse judge response: {result.content[0].text[:120]}",
            }
        return {
            "score": float(parsed.get("score", 0)),
            "reasoning": str(parsed.get("reasoning", "")),
        }


llm_judge = LLMJudge()
