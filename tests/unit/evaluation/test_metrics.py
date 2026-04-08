"""
Unit tests for retrieval quality metrics.

Tests precision@k, recall@k, and MRR with known inputs and expected outputs.
Pure logic — no external dependencies.
"""

import pytest

from src.evaluation.metrics import (
    compute_retrieval_metrics,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)


class TestPrecisionAtK:
    def test_all_relevant(self) -> None:
        assert precision_at_k(["a", "b", "c"], {"a", "b", "c"}, k=3) == 1.0

    def test_none_relevant(self) -> None:
        assert precision_at_k(["x", "y", "z"], {"a", "b"}, k=3) == 0.0

    def test_partial(self) -> None:
        # 2 out of 4 are relevant
        assert precision_at_k(["a", "x", "b", "y"], {"a", "b"}, k=4) == 0.5

    def test_k_less_than_retrieved(self) -> None:
        # Only look at top 2
        assert precision_at_k(["a", "x", "b"], {"a", "b"}, k=2) == 0.5

    def test_k_zero(self) -> None:
        assert precision_at_k(["a"], {"a"}, k=0) == 0.0

    def test_empty_retrieved(self) -> None:
        assert precision_at_k([], {"a"}, k=5) == 0.0


class TestRecallAtK:
    def test_all_retrieved(self) -> None:
        assert recall_at_k(["a", "b"], {"a", "b"}, k=5) == 1.0

    def test_none_retrieved(self) -> None:
        assert recall_at_k(["x", "y"], {"a", "b"}, k=5) == 0.0

    def test_partial(self) -> None:
        # 1 of 2 relevant items found
        assert recall_at_k(["a", "x"], {"a", "b"}, k=5) == 0.5

    def test_no_relevant_items(self) -> None:
        # If nothing is relevant, recall is 1.0 (trivially)
        assert recall_at_k(["a", "b"], set(), k=5) == 1.0

    def test_k_limits_search(self) -> None:
        # "b" is at position 3 but k=2 so it's not considered
        assert recall_at_k(["x", "a", "b"], {"a", "b"}, k=2) == 0.5


class TestMRR:
    def test_first_is_relevant(self) -> None:
        assert mean_reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0

    def test_second_is_relevant(self) -> None:
        assert mean_reciprocal_rank(["x", "a", "b"], {"a"}) == 0.5

    def test_third_is_relevant(self) -> None:
        assert mean_reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)

    def test_none_relevant(self) -> None:
        assert mean_reciprocal_rank(["x", "y", "z"], {"a"}) == 0.0

    def test_empty_retrieved(self) -> None:
        assert mean_reciprocal_rank([], {"a"}) == 0.0

    def test_multiple_relevant_uses_first(self) -> None:
        # MRR uses the FIRST relevant result
        assert mean_reciprocal_rank(["x", "a", "b"], {"a", "b"}) == 0.5


class TestComputeRetrievalMetrics:
    def test_returns_all_metrics(self) -> None:
        metrics = compute_retrieval_metrics(
            ["a", "x", "b"], {"a", "b"}, k=3
        )
        assert "precision@3" in metrics
        assert "recall@3" in metrics
        assert "mrr" in metrics

    def test_perfect_retrieval(self) -> None:
        metrics = compute_retrieval_metrics(
            ["a", "b"], {"a", "b"}, k=5
        )
        assert metrics["precision@5"] == pytest.approx(1.0)
        assert metrics["recall@5"] == pytest.approx(1.0)
        assert metrics["mrr"] == pytest.approx(1.0)
