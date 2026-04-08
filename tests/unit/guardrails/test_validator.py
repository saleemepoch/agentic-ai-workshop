"""
Unit tests for the guardrail validator orchestrator.

Tests layer ordering, fail-fast behaviour, and sampling logic.
Mocks the LLM-as-judge for Layer 3 to avoid API calls.
"""

import pytest

from src.guardrails.validator import (
    GuardrailConfig,
    _should_sample,
    validate,
)


class TestSampling:
    def test_sample_rate_zero(self) -> None:
        assert _should_sample("any text", 0.0) is False

    def test_sample_rate_one(self) -> None:
        assert _should_sample("any text", 1.0) is True

    def test_deterministic(self) -> None:
        # Same input → same decision
        assert _should_sample("test", 0.5) == _should_sample("test", 0.5)


class TestLayer1Only:
    """Test the validator with only Layer 1 enabled."""

    def test_clean_response_passes(self) -> None:
        config = GuardrailConfig(
            enable_layer_1=True,
            enable_layer_2=False,
            enable_layer_3=False,
        )
        result = validate(
            response_text="A clean response with no personal information.",
            input_tokens=100,
            output_tokens=50,
            config=config,
        )
        assert result.passed is True
        assert "layer_1" in result.layers_run
        assert result.layer_1_results["pii"]["passed"] is True

    def test_pii_in_response_fails(self) -> None:
        config = GuardrailConfig(
            enable_layer_1=True,
            enable_layer_2=False,
            enable_layer_3=False,
        )
        result = validate(
            response_text="Email candidate at john.doe@example.com to schedule",
            input_tokens=100,
            output_tokens=50,
            config=config,
        )
        assert result.passed is False
        assert result.layer_1_results["pii"]["count"] >= 1
        assert any("PII" in flag for flag in result.flags)

    def test_budget_violation_fails(self) -> None:
        from src.guardrails.budget import BudgetConfig

        config = GuardrailConfig(
            enable_layer_1=True,
            enable_layer_2=False,
            enable_layer_3=False,
            budget=BudgetConfig(max_input_tokens=100),
        )
        result = validate(
            response_text="Clean response",
            input_tokens=10000,  # Way over budget
            output_tokens=50,
            config=config,
        )
        assert result.passed is False
        assert result.layer_1_results["budget"]["passed"] is False


class TestLayer2:
    """Test Layer 2 retrieval relevance and context utilisation."""

    def test_low_relevance_fails(self) -> None:
        config = GuardrailConfig(
            enable_layer_1=True,
            enable_layer_2=True,
            enable_layer_3=False,
            relevance_threshold=0.7,
        )
        result = validate(
            response_text="Clean response",
            retrieval_scores=[0.3, 0.2, 0.1],  # All below threshold
            input_tokens=100,
            output_tokens=50,
            config=config,
        )
        assert result.passed is False
        assert result.layer_2_results["retrieval_relevance"]["passed"] is False

    def test_high_relevance_passes(self) -> None:
        config = GuardrailConfig(
            enable_layer_1=True,
            enable_layer_2=True,
            enable_layer_3=False,
        )
        result = validate(
            response_text="Clean response",
            retrieval_scores=[0.9, 0.8, 0.7],
            input_tokens=100,
            output_tokens=50,
            config=config,
        )
        assert result.passed is True


class TestFailFast:
    """Test that subsequent layers don't run when earlier layers fail."""

    def test_layer_1_failure_skips_layer_2(self) -> None:
        config = GuardrailConfig(
            enable_layer_1=True,
            enable_layer_2=True,
            enable_layer_3=False,
        )
        result = validate(
            response_text="Email me at john@example.com",  # PII triggers Layer 1
            retrieval_scores=[0.9, 0.8],
            input_tokens=100,
            output_tokens=50,
            config=config,
        )
        assert result.passed is False
        assert "layer_1" in result.layers_run
        # Layer 2 should not have been run
        assert "layer_2" not in result.layers_run
