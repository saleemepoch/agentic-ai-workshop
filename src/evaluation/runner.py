"""
Evaluation runner: orchestrates eval runs against the golden dataset.

Runs the full pipeline on each golden case, computes metrics, and
persists results for trend tracking.

Interview talking points:
- Why persist results? So you can track trends. "Precision@5 dropped
  from 0.8 to 0.6 after the last prompt change" is actionable.
  "Precision@5 is 0.6 right now" is less useful without history.
- Why run the full pipeline? Because the eval must test the same code
  path that production uses. If you test components in isolation,
  you miss integration issues.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.evaluation.golden_dataset import GOLDEN_DATASET, GoldenCase
from src.evaluation.llm_judge import llm_judge


@dataclass
class CaseResult:
    """Result of evaluating a single golden case."""

    case_id: str
    scenario: str
    match_score: float
    expected_range: tuple[float, float]
    score_in_range: bool
    expected_outcome: str
    actual_outcome: str
    outcome_correct: bool
    faithfulness_score: float
    relevance_score: float
    duration_ms: float
    details: dict = field(default_factory=dict)


@dataclass
class EvalRunResult:
    """Result of a complete evaluation run."""

    run_id: str
    timestamp: str
    case_results: list[CaseResult]
    aggregate_metrics: dict
    total_duration_ms: float

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "case_results": [
                {
                    "case_id": cr.case_id,
                    "scenario": cr.scenario,
                    "match_score": cr.match_score,
                    "expected_range": list(cr.expected_range),
                    "score_in_range": cr.score_in_range,
                    "expected_outcome": cr.expected_outcome,
                    "actual_outcome": cr.actual_outcome,
                    "outcome_correct": cr.outcome_correct,
                    "faithfulness_score": cr.faithfulness_score,
                    "relevance_score": cr.relevance_score,
                    "duration_ms": cr.duration_ms,
                }
                for cr in self.case_results
            ],
            "aggregate_metrics": self.aggregate_metrics,
            "total_duration_ms": self.total_duration_ms,
        }


def _determine_outcome(score: float) -> str:
    """Map a match score to an outcome label.

    Thresholds match `route_candidate` in src/agents/nodes.py so eval and
    production routing agree on what counts as strong / partial / no match.
    """
    if score >= 0.65:
        return "strong_match"
    elif score >= 0.30:
        return "partial_match"
    else:
        return "no_match"


async def run_evaluation(
    run_agent_workflow: callable,
) -> EvalRunResult:
    """Run the evaluation pipeline against all golden cases.

    Args:
        run_agent_workflow: Async callable that takes (cv_text, jd_text)
            and returns the workflow result dict.

    Returns:
        EvalRunResult with per-case and aggregate metrics.
    """
    run_start = time.perf_counter()
    run_id = f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    case_results: list[CaseResult] = []

    for case in GOLDEN_DATASET:
        case_start = time.perf_counter()

        # Run the agent workflow
        result = await run_agent_workflow(case.cv_text, case.jd_text)

        match_score = result.get("match_score", 0.0)
        actual_outcome = _determine_outcome(match_score)
        score_in_range = case.expected_match_range[0] <= match_score <= case.expected_match_range[1]

        # LLM-as-judge scoring
        context = json.dumps(result.get("parsed_cv", {})) + json.dumps(result.get("parsed_jd", {}))
        response_text = result.get("match_reasoning", "")

        faithfulness = llm_judge.score_faithfulness(context, response_text)
        relevance = llm_judge.score_relevance(case.jd_text, response_text)

        case_results.append(CaseResult(
            case_id=case.id,
            scenario=case.scenario,
            match_score=match_score,
            expected_range=case.expected_match_range,
            score_in_range=score_in_range,
            expected_outcome=case.expected_outcome,
            actual_outcome=actual_outcome,
            outcome_correct=(actual_outcome == case.expected_outcome),
            faithfulness_score=faithfulness["score"],
            relevance_score=relevance["score"],
            duration_ms=round((time.perf_counter() - case_start) * 1000, 2),
        ))

    # Aggregate metrics
    total_cases = len(case_results)
    scores_in_range = sum(1 for cr in case_results if cr.score_in_range)
    outcomes_correct = sum(1 for cr in case_results if cr.outcome_correct)
    avg_faithfulness = sum(cr.faithfulness_score for cr in case_results) / total_cases if total_cases else 0
    avg_relevance = sum(cr.relevance_score for cr in case_results) / total_cases if total_cases else 0

    aggregate = {
        "total_cases": total_cases,
        "scores_in_expected_range": scores_in_range,
        "score_accuracy": round(scores_in_range / total_cases, 4) if total_cases else 0,
        "outcomes_correct": outcomes_correct,
        "outcome_accuracy": round(outcomes_correct / total_cases, 4) if total_cases else 0,
        "avg_faithfulness": round(avg_faithfulness, 4),
        "avg_relevance": round(avg_relevance, 4),
    }

    return EvalRunResult(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        case_results=case_results,
        aggregate_metrics=aggregate,
        total_duration_ms=round((time.perf_counter() - run_start) * 1000, 2),
    )
