"""
Layer 1 — Budget enforcement.

Per-request token and cost limits. Zero-cost arithmetic check that
prevents runaway requests from consuming the daily budget.

Interview talking points:
- Why per-request? Because daily budgets don't catch single-request blowouts.
  A single buggy retry loop can burn through hundreds of dollars in minutes.
  Per-request limits stop the bleeding before it starts.
- Why both tokens AND cost? Tokens are the unit of work — they tell you
  how much the LLM is doing. Cost is the unit of money — it tells you
  what you're spending. Different models have different token-to-cost
  ratios, so you need both checks.
"""

from dataclasses import dataclass

from src.observability.cost import calculate_llm_cost


@dataclass
class BudgetConfig:
    """Per-request budget limits."""

    max_input_tokens: int = 50_000
    max_output_tokens: int = 4_000
    max_cost_usd: float = 1.0  # $1 per request limit

    def to_dict(self) -> dict:
        return {
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_cost_usd": self.max_cost_usd,
        }


@dataclass
class BudgetCheckResult:
    """Result of a budget check."""

    passed: bool
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    config: BudgetConfig
    violations: list[str]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(self.estimated_cost, 6),
            "config": self.config.to_dict(),
            "violations": self.violations,
        }


def check_budget(
    model: str,
    input_tokens: int,
    output_tokens: int,
    config: BudgetConfig | None = None,
) -> BudgetCheckResult:
    """Check whether a request fits within the configured budget.

    Args:
        model: The LLM model name (used for cost calculation).
        input_tokens: Estimated or actual input token count.
        output_tokens: Estimated or actual output token count.
        config: Budget limits. Uses defaults if not provided.

    Returns:
        BudgetCheckResult indicating pass/fail with details.
    """
    cfg = config or BudgetConfig()
    cost_info = calculate_llm_cost(model, input_tokens, output_tokens)
    estimated_cost = cost_info["total_cost"]

    violations: list[str] = []
    if input_tokens > cfg.max_input_tokens:
        violations.append(
            f"Input tokens ({input_tokens}) exceeds limit ({cfg.max_input_tokens})"
        )
    if output_tokens > cfg.max_output_tokens:
        violations.append(
            f"Output tokens ({output_tokens}) exceeds limit ({cfg.max_output_tokens})"
        )
    if estimated_cost > cfg.max_cost_usd:
        violations.append(
            f"Cost (${estimated_cost:.4f}) exceeds limit (${cfg.max_cost_usd})"
        )

    return BudgetCheckResult(
        passed=len(violations) == 0,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
        config=cfg,
        violations=violations,
    )
