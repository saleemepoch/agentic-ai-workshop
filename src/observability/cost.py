"""
Cost calculation and budget tracking.

Provides utilities for calculating LLM costs from token usage and
model pricing. Used by the observability endpoints and the guardrails
budget enforcement (Pillar 7).

Interview talking points:
- Why track costs per-request? Because stakeholders always ask "how much
  does a single match cost?" You need per-request granularity to answer
  that, not just monthly bills.
- Why maintain our own pricing table? Langfuse has built-in pricing, but
  we maintain a local copy for: (a) unit testing without Langfuse, (b)
  budget enforcement in the guardrails layer, (c) teaching — showing
  students exactly how costs are calculated.
"""

from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing per million tokens for a model."""

    model: str
    input_cost_per_m: float  # USD per 1M input tokens
    output_cost_per_m: float  # USD per 1M output tokens


# Pricing as of 2025 — update as prices change
MODEL_PRICING: dict[str, ModelPricing] = {
    "claude-sonnet-4-20250514": ModelPricing(
        model="claude-sonnet-4-20250514",
        input_cost_per_m=3.0,
        output_cost_per_m=15.0,
    ),
    "claude-haiku-4-5-20251001": ModelPricing(
        model="claude-haiku-4-5-20251001",
        input_cost_per_m=0.80,
        output_cost_per_m=4.0,
    ),
    "claude-opus-4-6": ModelPricing(
        model="claude-opus-4-6",
        input_cost_per_m=15.0,
        output_cost_per_m=75.0,
    ),
}

# Voyage AI embedding pricing
EMBEDDING_PRICING = {
    "voyage-3": 0.06,  # USD per 1M tokens
}


def calculate_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, float]:
    """Calculate the cost of an LLM call.

    Returns:
        Dict with input_cost, output_cost, total_cost (all in USD).
    """
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        # Unknown model — return zero cost with a flag
        return {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
            "model_known": False,
        }

    input_cost = input_tokens * pricing.input_cost_per_m / 1_000_000
    output_cost = output_tokens * pricing.output_cost_per_m / 1_000_000

    return {
        "input_cost": round(input_cost, 8),
        "output_cost": round(output_cost, 8),
        "total_cost": round(input_cost + output_cost, 8),
        "model_known": True,
    }


def calculate_embedding_cost(model: str, token_count: int) -> float:
    """Calculate embedding cost in USD."""
    price_per_m = EMBEDDING_PRICING.get(model, 0.0)
    return round(token_count * price_per_m / 1_000_000, 8)


@dataclass
class CostSummary:
    """Aggregate cost summary across multiple operations."""

    total_llm_cost: float = 0.0
    total_embedding_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_embedding_tokens: int = 0
    request_count: int = 0

    @property
    def total_cost(self) -> float:
        return round(self.total_llm_cost + self.total_embedding_cost, 6)

    @property
    def avg_cost_per_request(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_cost / self.request_count, 6)

    def add_llm_call(self, model: str, input_tokens: int, output_tokens: int) -> None:
        cost = calculate_llm_cost(model, input_tokens, output_tokens)
        self.total_llm_cost += cost["total_cost"]
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def add_embedding_call(self, model: str, token_count: int) -> None:
        self.total_embedding_cost += calculate_embedding_cost(model, token_count)
        self.total_embedding_tokens += token_count

    def to_dict(self) -> dict:
        return {
            "total_cost_usd": self.total_cost,
            "total_llm_cost_usd": round(self.total_llm_cost, 6),
            "total_embedding_cost_usd": round(self.total_embedding_cost, 6),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_embedding_tokens": self.total_embedding_tokens,
            "request_count": self.request_count,
            "avg_cost_per_request_usd": self.avg_cost_per_request,
        }
