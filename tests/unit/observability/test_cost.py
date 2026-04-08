"""
Unit tests for cost calculation.

Tests pricing lookups, cost arithmetic, and summary aggregation.
No external dependencies — pure logic.
"""

import pytest

from src.observability.cost import (
    CostSummary,
    calculate_embedding_cost,
    calculate_llm_cost,
)


class TestCalculateLLMCost:
    """Test LLM cost calculation from token counts."""

    def test_sonnet_cost(self) -> None:
        cost = calculate_llm_cost("claude-sonnet-4-20250514", 1000, 500)
        # Input: 1000 * $3/M = $0.003, Output: 500 * $15/M = $0.0075
        assert cost["input_cost"] == pytest.approx(0.003, abs=1e-6)
        assert cost["output_cost"] == pytest.approx(0.0075, abs=1e-6)
        assert cost["total_cost"] == pytest.approx(0.0105, abs=1e-6)
        assert cost["model_known"] is True

    def test_haiku_cost(self) -> None:
        cost = calculate_llm_cost("claude-haiku-4-5-20251001", 10000, 1000)
        # Input: 10000 * $0.8/M = $0.008, Output: 1000 * $4/M = $0.004
        assert cost["input_cost"] == pytest.approx(0.008, abs=1e-6)
        assert cost["output_cost"] == pytest.approx(0.004, abs=1e-6)
        assert cost["total_cost"] == pytest.approx(0.012, abs=1e-6)

    def test_opus_cost(self) -> None:
        cost = calculate_llm_cost("claude-opus-4-6", 1000, 100)
        assert cost["input_cost"] == pytest.approx(0.015, abs=1e-6)
        assert cost["output_cost"] == pytest.approx(0.0075, abs=1e-6)

    def test_unknown_model_returns_zero(self) -> None:
        cost = calculate_llm_cost("unknown-model-v1", 1000, 500)
        assert cost["total_cost"] == 0.0
        assert cost["model_known"] is False

    def test_zero_tokens(self) -> None:
        cost = calculate_llm_cost("claude-sonnet-4-20250514", 0, 0)
        assert cost["total_cost"] == 0.0


class TestCalculateEmbeddingCost:
    """Test embedding cost calculation."""

    def test_voyage_cost(self) -> None:
        cost = calculate_embedding_cost("voyage-3", 1_000_000)
        assert cost == pytest.approx(0.06, abs=1e-6)

    def test_unknown_model(self) -> None:
        cost = calculate_embedding_cost("unknown-embed", 1000)
        assert cost == 0.0


class TestCostSummary:
    """Test cost summary aggregation."""

    def test_empty_summary(self) -> None:
        summary = CostSummary()
        assert summary.total_cost == 0.0
        assert summary.avg_cost_per_request == 0.0

    def test_add_llm_calls(self) -> None:
        summary = CostSummary()
        summary.add_llm_call("claude-sonnet-4-20250514", 1000, 500)
        summary.add_llm_call("claude-sonnet-4-20250514", 2000, 300)
        summary.request_count = 2

        assert summary.total_input_tokens == 3000
        assert summary.total_output_tokens == 800
        assert summary.total_llm_cost > 0
        assert summary.avg_cost_per_request > 0

    def test_add_embedding_calls(self) -> None:
        summary = CostSummary()
        summary.add_embedding_call("voyage-3", 5000)
        assert summary.total_embedding_tokens == 5000
        assert summary.total_embedding_cost > 0

    def test_to_dict(self) -> None:
        summary = CostSummary()
        summary.add_llm_call("claude-sonnet-4-20250514", 1000, 500)
        summary.request_count = 1

        d = summary.to_dict()
        assert "total_cost_usd" in d
        assert "total_llm_cost_usd" in d
        assert "total_embedding_cost_usd" in d
        assert "avg_cost_per_request_usd" in d
        assert d["request_count"] == 1
