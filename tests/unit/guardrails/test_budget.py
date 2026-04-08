"""
Unit tests for budget enforcement (Layer 1).

Pure arithmetic — no external dependencies.
"""

import pytest

from src.guardrails.budget import BudgetConfig, check_budget


class TestBudgetCheck:
    def test_under_budget_passes(self) -> None:
        result = check_budget("claude-sonnet-4-20250514", 1000, 500)
        assert result.passed is True
        assert result.violations == []

    def test_input_tokens_exceeded(self) -> None:
        config = BudgetConfig(max_input_tokens=100)
        result = check_budget("claude-sonnet-4-20250514", 500, 100, config)
        assert result.passed is False
        assert any("Input tokens" in v for v in result.violations)

    def test_output_tokens_exceeded(self) -> None:
        config = BudgetConfig(max_output_tokens=50)
        result = check_budget("claude-sonnet-4-20250514", 100, 200, config)
        assert result.passed is False
        assert any("Output tokens" in v for v in result.violations)

    def test_cost_exceeded(self) -> None:
        # Sonnet: 100K input * $3/M = $0.30, 100K output * $15/M = $1.50, total $1.80
        config = BudgetConfig(max_cost_usd=0.50)
        result = check_budget("claude-sonnet-4-20250514", 100_000, 100_000, config)
        assert result.passed is False
        assert any("Cost" in v for v in result.violations)

    def test_multiple_violations(self) -> None:
        config = BudgetConfig(
            max_input_tokens=100,
            max_output_tokens=50,
            max_cost_usd=0.001,
        )
        result = check_budget("claude-sonnet-4-20250514", 1000, 500, config)
        assert result.passed is False
        assert len(result.violations) >= 2

    def test_at_limit_passes(self) -> None:
        config = BudgetConfig(max_input_tokens=1000)
        result = check_budget("claude-sonnet-4-20250514", 1000, 100, config)
        assert result.passed is True

    def test_unknown_model_zero_cost(self) -> None:
        # Unknown model returns zero cost, so cost check passes
        result = check_budget("unknown-model", 1000, 500)
        assert result.estimated_cost == 0.0
