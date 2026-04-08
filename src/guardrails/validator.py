"""
Guardrails validator: orchestrates all three layers.

Runs Layer 1 (sync, free) → Layer 2 (async, cheap) → Layer 3 (LLM, sampled).
Each layer's results are returned even if subsequent layers don't run,
so the frontend can show exactly what was checked.

Interview talking points:
- Why an orchestrator? Because the layers have ordering rules (cheap before
  expensive, fail-fast on Layer 1) that shouldn't be the responsibility
  of any individual layer. Orchestration belongs in one place.
- Why expose layer results separately? Transparency. The frontend can show
  "Layer 1: passed (0ms, $0). Layer 2: passed (50ms, $0). Layer 3: skipped
  (not sampled)." That's the teaching value — users see what each layer cost.
- How is sampling decided? A configurable rate (default 10%). The validator
  uses a deterministic hash for testability — given the same input, the same
  sample decision is made. Production systems would use a random sample.
"""

import hashlib
from dataclasses import dataclass, field

from src.guardrails.budget import BudgetCheckResult, BudgetConfig, check_budget
from src.guardrails.faithfulness import check_completeness, check_faithfulness
from src.guardrails.pii import detect_pii


@dataclass
class GuardrailConfig:
    """Configuration for the guardrails validator."""

    enable_layer_1: bool = True
    enable_layer_2: bool = True
    enable_layer_3: bool = True
    layer_3_sample_rate: float = 0.1  # 10% of requests
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    relevance_threshold: float = 0.5

    def to_dict(self) -> dict:
        return {
            "enable_layer_1": self.enable_layer_1,
            "enable_layer_2": self.enable_layer_2,
            "enable_layer_3": self.enable_layer_3,
            "layer_3_sample_rate": self.layer_3_sample_rate,
            "budget": self.budget.to_dict(),
            "relevance_threshold": self.relevance_threshold,
        }


@dataclass
class GuardrailResult:
    """Aggregated result from all guardrail layers."""

    passed: bool
    layer_1_results: dict = field(default_factory=dict)
    layer_2_results: dict = field(default_factory=dict)
    layer_3_results: dict = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    layers_run: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "layer_1_results": self.layer_1_results,
            "layer_2_results": self.layer_2_results,
            "layer_3_results": self.layer_3_results,
            "flags": self.flags,
            "layers_run": self.layers_run,
            "total_cost_usd": round(self.total_cost_usd, 6),
        }


def _should_sample(content: str, sample_rate: float) -> bool:
    """Deterministic sampling based on content hash.

    Same input → same sample decision. This makes tests reproducible
    while still hitting roughly `sample_rate` of unique inputs.
    """
    if sample_rate >= 1.0:
        return True
    if sample_rate <= 0.0:
        return False
    h = int(hashlib.md5(content.encode()).hexdigest(), 16)
    return (h % 100) < (sample_rate * 100)


def validate(
    response_text: str,
    query: str | None = None,
    context: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    input_tokens: int = 0,
    output_tokens: int = 0,
    retrieval_scores: list[float] | None = None,
    config: GuardrailConfig | None = None,
) -> GuardrailResult:
    """Run a response through all enabled guardrail layers.

    Args:
        response_text: The LLM response to validate.
        query: The original user query (needed for Layer 3 completeness).
        context: The retrieved context (needed for Layer 3 faithfulness).
        model: Model name for cost calculation.
        input_tokens: Token count for budget check.
        output_tokens: Token count for budget check.
        retrieval_scores: Similarity scores from retrieval (for Layer 2).
        config: Guardrail configuration. Uses defaults if not provided.

    Returns:
        GuardrailResult with per-layer results and overall pass/fail.
    """
    cfg = config or GuardrailConfig()
    result = GuardrailResult(passed=True)

    # ==================== LAYER 1: Sync, Free ====================
    if cfg.enable_layer_1:
        result.layers_run.append("layer_1")
        layer_1: dict = {}

        # PII detection
        pii_matches = detect_pii(response_text)
        layer_1["pii"] = {
            "passed": len(pii_matches) == 0,
            "matches": [m.to_dict() for m in pii_matches],
            "count": len(pii_matches),
        }
        if pii_matches:
            result.passed = False
            result.flags.append(f"PII detected: {len(pii_matches)} item(s)")

        # Budget check
        budget_result = check_budget(model, input_tokens, output_tokens, cfg.budget)
        layer_1["budget"] = budget_result.to_dict()
        if not budget_result.passed:
            result.passed = False
            result.flags.extend(budget_result.violations)

        result.layer_1_results = layer_1

        # Fail-fast: if Layer 1 failed, don't run subsequent layers
        if not result.passed:
            return result

    # ==================== LAYER 2: Async, Cheap ====================
    if cfg.enable_layer_2:
        result.layers_run.append("layer_2")
        layer_2: dict = {}

        # Retrieval relevance check
        if retrieval_scores:
            avg_relevance = sum(retrieval_scores) / len(retrieval_scores)
            max_relevance = max(retrieval_scores)
            relevance_passed = max_relevance >= cfg.relevance_threshold
            layer_2["retrieval_relevance"] = {
                "passed": relevance_passed,
                "avg_score": round(avg_relevance, 4),
                "max_score": round(max_relevance, 4),
                "threshold": cfg.relevance_threshold,
            }
            if not relevance_passed:
                result.passed = False
                result.flags.append(
                    f"Retrieval relevance too low: max {max_relevance:.2f} < {cfg.relevance_threshold}"
                )

        # Context utilisation: was the response actually using the context?
        # Heuristic: count word overlap between response and context
        if context and response_text:
            context_words = set(context.lower().split())
            response_words = set(response_text.lower().split())
            overlap = len(context_words & response_words)
            utilisation = overlap / max(len(response_words), 1)
            layer_2["context_utilisation"] = {
                "passed": utilisation > 0.05,  # At least 5% word overlap
                "score": round(utilisation, 4),
                "shared_words": overlap,
            }

        result.layer_2_results = layer_2

        if not result.passed:
            return result

    # ==================== LAYER 3: LLM Judge, Sampled ====================
    if cfg.enable_layer_3:
        sampled = _should_sample(response_text, cfg.layer_3_sample_rate)
        layer_3: dict = {"sampled": sampled, "sample_rate": cfg.layer_3_sample_rate}

        if sampled:
            result.layers_run.append("layer_3")

            if context:
                faith_result = check_faithfulness(context, response_text)
                layer_3["faithfulness"] = faith_result
                if not faith_result["passed"]:
                    result.passed = False
                    result.flags.append(
                        f"Faithfulness below threshold: {faith_result['score']:.2f}"
                    )

            if query:
                comp_result = check_completeness(query, response_text)
                layer_3["completeness"] = comp_result
                if not comp_result["passed"]:
                    result.flags.append(
                        f"Completeness below threshold: {comp_result['score']:.2f}"
                    )
                    # Completeness is informational, doesn't fail the check

            # Approximate cost: 2 LLM judge calls
            result.total_cost_usd += 0.005

        result.layer_3_results = layer_3

    return result
