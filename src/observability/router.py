"""
FastAPI router for observability endpoints.

Provides access to traces, costs, and latency data. These endpoints
proxy data from Langfuse for the frontend rather than having the
frontend call Langfuse directly.

Endpoints:
- GET /observability/traces          — Recent traces with costs
- GET /observability/traces/{id}     — Full trace tree
- GET /observability/costs/summary   — Aggregate cost statistics
- GET /observability/models          — Available models with pricing
"""

from fastapi import APIRouter

from src.observability.cost import (
    MODEL_PRICING,
    EMBEDDING_PRICING,
    CostSummary,
    calculate_llm_cost,
)
from src.observability.tracing import get_langfuse

router = APIRouter()


@router.get("/traces")
async def get_recent_traces(limit: int = 20) -> dict:
    """Fetch recent traces from Langfuse.

    Returns a list of traces with their total cost, duration, and metadata.
    """
    try:
        langfuse = get_langfuse()
        traces = langfuse.fetch_traces(limit=limit)
        return {
            "traces": [
                {
                    "id": t.id,
                    "name": t.name,
                    "timestamp": str(t.timestamp) if t.timestamp else None,
                    "metadata": t.metadata,
                    "tags": t.tags,
                }
                for t in traces.data
            ],
            "total": len(traces.data),
        }
    except Exception as e:
        return {"traces": [], "total": 0, "error": str(e)}


@router.get("/traces/{trace_id}")
async def get_trace_detail(trace_id: str) -> dict:
    """Fetch a single trace with its full observation tree.

    Returns the trace metadata and all nested spans/generations,
    enabling the frontend to render a trace tree with costs at each level.
    """
    try:
        langfuse = get_langfuse()
        trace = langfuse.fetch_trace(trace_id)
        return {
            "id": trace.id,
            "name": trace.name,
            "timestamp": str(trace.timestamp) if trace.timestamp else None,
            "metadata": trace.metadata,
            "tags": trace.tags,
            "observations": [
                {
                    "id": obs.id,
                    "name": obs.name,
                    "type": obs.type,
                    "start_time": str(obs.start_time) if obs.start_time else None,
                    "end_time": str(obs.end_time) if obs.end_time else None,
                    "model": obs.model,
                    "usage": {
                        "input_tokens": obs.usage.input if obs.usage else 0,
                        "output_tokens": obs.usage.output if obs.usage else 0,
                        "total_tokens": obs.usage.total if obs.usage else 0,
                    } if obs.usage else None,
                    "metadata": obs.metadata,
                }
                for obs in (trace.observations or [])
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/costs/summary")
async def get_cost_summary() -> dict:
    """Aggregate cost statistics from recent traces.

    Returns total costs, token counts, and averages. This is the
    data behind the cost dashboard on the frontend.
    """
    try:
        langfuse = get_langfuse()
        traces = langfuse.fetch_traces(limit=100)

        summary = CostSummary()
        for trace in traces.data:
            summary.request_count += 1
            for obs in (trace.observations or []):
                if obs.usage and obs.model:
                    input_tokens = obs.usage.input or 0
                    output_tokens = obs.usage.output or 0
                    summary.add_llm_call(obs.model, input_tokens, output_tokens)

        return summary.to_dict()
    except Exception as e:
        return {"error": str(e), **CostSummary().to_dict()}


@router.get("/models")
async def get_model_pricing() -> dict:
    """Return available models with their pricing.

    Used by the frontend to display cost breakdowns and for
    the guardrails budget enforcement calculations.
    """
    return {
        "llm_models": {
            name: {
                "input_cost_per_m_tokens": p.input_cost_per_m,
                "output_cost_per_m_tokens": p.output_cost_per_m,
            }
            for name, p in MODEL_PRICING.items()
        },
        "embedding_models": EMBEDDING_PRICING,
    }


@router.post("/costs/calculate")
async def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """Calculate the cost of a hypothetical LLM call.

    Useful for the frontend's cost estimation feature.
    """
    return calculate_llm_cost(model, input_tokens, output_tokens)
