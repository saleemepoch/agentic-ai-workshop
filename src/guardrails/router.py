"""
FastAPI router for guardrail testing endpoints.

Endpoints expose each layer individually plus the full validator,
so the frontend can demonstrate each layer's behaviour interactively.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.guardrails.budget import BudgetConfig, check_budget
from src.guardrails.faithfulness import check_completeness, check_faithfulness
from src.guardrails.pii import detect_pii, redact_pii
from src.guardrails.validator import GuardrailConfig, validate

router = APIRouter()


class PIIRequest(BaseModel):
    text: str = Field(..., min_length=1)


class BudgetRequest(BaseModel):
    model: str = "claude-sonnet-4-20250514"
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    max_input_tokens: int = 50_000
    max_output_tokens: int = 4_000
    max_cost_usd: float = 1.0


class FaithfulnessRequest(BaseModel):
    context: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)


class FullCheckRequest(BaseModel):
    response_text: str = Field(..., min_length=1)
    query: str | None = None
    context: str | None = None
    model: str = "claude-sonnet-4-20250514"
    input_tokens: int = 0
    output_tokens: int = 0
    retrieval_scores: list[float] | None = None
    enable_layer_3: bool = True
    layer_3_sample_rate: float = 1.0  # Force run for demo


@router.post("/check/pii")
async def check_pii(body: PIIRequest) -> dict:
    """Run PII detection on text. Layer 1 only."""
    matches = detect_pii(body.text)
    return {
        "passed": len(matches) == 0,
        "count": len(matches),
        "matches": [m.to_dict() for m in matches],
        "redacted": redact_pii(body.text) if matches else body.text,
    }


@router.post("/check/budget")
async def check_budget_endpoint(body: BudgetRequest) -> dict:
    """Check whether a request fits within the budget. Layer 1."""
    config = BudgetConfig(
        max_input_tokens=body.max_input_tokens,
        max_output_tokens=body.max_output_tokens,
        max_cost_usd=body.max_cost_usd,
    )
    result = check_budget(body.model, body.input_tokens, body.output_tokens, config)
    return result.to_dict()


@router.post("/check/faithfulness")
async def check_faithfulness_endpoint(body: FaithfulnessRequest) -> dict:
    """Score faithfulness via LLM-as-judge. Layer 3."""
    return check_faithfulness(body.context, body.response)


@router.post("/check/completeness")
async def check_completeness_endpoint(body: FaithfulnessRequest) -> dict:
    """Score completeness via LLM-as-judge. Layer 3."""
    return check_completeness(body.context, body.response)


@router.post("/check")
async def check_full(body: FullCheckRequest) -> dict:
    """Run all enabled guardrail layers on a response.

    This is the main validator endpoint. Returns per-layer results
    and an overall pass/fail.
    """
    config = GuardrailConfig(
        enable_layer_3=body.enable_layer_3,
        layer_3_sample_rate=body.layer_3_sample_rate,
    )
    result = validate(
        response_text=body.response_text,
        query=body.query,
        context=body.context,
        model=body.model,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        retrieval_scores=body.retrieval_scores,
        config=config,
    )
    return result.to_dict()


@router.get("/config")
async def get_config() -> dict:
    """Return the default guardrail configuration."""
    return GuardrailConfig().to_dict()
