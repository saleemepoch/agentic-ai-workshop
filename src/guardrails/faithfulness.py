"""
Layer 3 — Faithfulness check (LLM-as-judge).

Uses Claude to score whether a response is grounded in the provided context.
Expensive (~$0.005-0.01 per check), so runs only on a sampled subset
of requests by default.

Reuses the LLMJudge from the evaluation pillar — same logic, different
context. In evaluation, it's used to score golden dataset runs. Here,
it's used as a runtime guardrail.

Interview talking points:
- Why share code with evaluation? Same problem, same solution. Faithfulness
  scoring is the same operation whether you're testing or guarding. The
  difference is when and how often you run it.
- Why sample instead of running on every request? Cost. At ~$0.01 per
  check, running on every request 24/7 costs $864/day at 1 request/second.
  10% sampling gives you statistical confidence at 1/10th the cost.
"""

from src.evaluation.llm_judge import llm_judge


def check_faithfulness(context: str, response: str) -> dict:
    """Score faithfulness of a response against the provided context.

    Returns:
        Dict with score (0-1), reasoning, and a `passed` boolean
        (passed = True if score >= 0.7).
    """
    result = llm_judge.score_faithfulness(context, response)
    score = float(result.get("score", 0))
    return {
        "score": score,
        "reasoning": result.get("reasoning", ""),
        "passed": score >= 0.7,
        "threshold": 0.7,
    }


def check_completeness(query: str, response: str) -> dict:
    """Score whether the response completely addresses the query.

    Reuses the relevance scorer from evaluation as a proxy for completeness —
    a complete response is one that fully addresses the query.
    """
    result = llm_judge.score_relevance(query, response)
    score = float(result.get("score", 0))
    return {
        "score": score,
        "reasoning": result.get("reasoning", ""),
        "passed": score >= 0.6,
        "threshold": 0.6,
    }
