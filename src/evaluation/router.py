"""
FastAPI router for evaluation endpoints.

Endpoints:
- POST /evaluation/run      — Trigger an eval run against the golden dataset
- GET  /evaluation/results   — Get the latest eval results
- GET  /evaluation/golden    — View the golden dataset
"""

from fastapi import APIRouter

from src.agents.graph import compile_graph
from src.evaluation.golden_dataset import GOLDEN_DATASET
from src.evaluation.runner import run_evaluation

router = APIRouter()

# In-memory storage for eval results (would be DB in production)
_eval_results: list[dict] = []

# Compiled graph for running evaluations
_graph = compile_graph()


async def _run_workflow(cv_text: str, jd_text: str) -> dict:
    """Run the agent workflow for evaluation purposes."""
    initial_state = {
        "cv_text": cv_text,
        "jd_text": jd_text,
        "step_history": [],
        "total_tokens": 0,
        "total_cost": 0.0,
    }
    return await _graph.ainvoke(initial_state)


@router.post("/run")
async def trigger_eval_run() -> dict:
    """Run the evaluation pipeline against the golden dataset.

    Executes the full agent workflow on each golden case, scores with
    LLM-as-judge, and returns aggregate metrics.
    """
    result = await run_evaluation(_run_workflow)
    result_dict = result.to_dict()
    _eval_results.append(result_dict)
    return result_dict


@router.get("/results")
async def get_eval_results() -> dict:
    """Get the latest evaluation results."""
    if not _eval_results:
        return {"message": "No evaluation runs yet. POST /evaluation/run to start one."}
    return _eval_results[-1]


@router.get("/results/history")
async def get_eval_history() -> dict:
    """Get all evaluation results for trend tracking."""
    return {
        "runs": [
            {
                "run_id": r["run_id"],
                "timestamp": r["timestamp"],
                "aggregate_metrics": r["aggregate_metrics"],
                "total_duration_ms": r["total_duration_ms"],
            }
            for r in _eval_results
        ],
        "total_runs": len(_eval_results),
    }


@router.get("/golden")
async def get_golden_dataset() -> dict:
    """View the golden dataset cases."""
    return {
        "cases": [
            {
                "id": case.id,
                "scenario": case.scenario,
                "description": case.description,
                "expected_match_range": list(case.expected_match_range),
                "expected_outcome": case.expected_outcome,
                "expected_keywords": case.expected_keywords,
                "cv_preview": case.cv_text[:200] + "...",
                "jd_preview": case.jd_text[:200] + "...",
            }
            for case in GOLDEN_DATASET
        ],
        "total_cases": len(GOLDEN_DATASET),
    }
