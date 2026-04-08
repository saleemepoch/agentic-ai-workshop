"""
Unit tests for the circuit breaker pattern.

Tests state transitions: closed → open → half-open → closed (or → open).
"""

import time

import pytest

from src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)


def make_breaker(failure_threshold: int = 3, cooldown_seconds: float = 0.1) -> CircuitBreaker:
    return CircuitBreaker(
        name="test",
        config=CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            cooldown_seconds=cooldown_seconds,
            success_threshold=1,
        ),
    )


def failing():
    raise RuntimeError("nope")


def succeeding():
    return "ok"


class TestClosedState:
    def test_starts_closed(self) -> None:
        breaker = make_breaker()
        assert breaker.state == CircuitState.CLOSED

    def test_successes_keep_closed(self) -> None:
        breaker = make_breaker()
        for _ in range(10):
            assert breaker.call(succeeding) == "ok"
        assert breaker.state == CircuitState.CLOSED

    def test_failures_below_threshold_stay_closed(self) -> None:
        breaker = make_breaker(failure_threshold=5)
        for _ in range(4):
            with pytest.raises(RuntimeError):
                breaker.call(failing)
        assert breaker.state == CircuitState.CLOSED


class TestOpenTransition:
    def test_threshold_failures_open_circuit(self) -> None:
        breaker = make_breaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                breaker.call(failing)
        assert breaker.state == CircuitState.OPEN

    def test_open_circuit_rejects_calls(self) -> None:
        breaker = make_breaker(failure_threshold=2)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(failing)

        # Now open
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(succeeding)


class TestHalfOpenTransition:
    def test_cooldown_transitions_to_half_open(self) -> None:
        breaker = make_breaker(failure_threshold=2, cooldown_seconds=0.05)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(failing)
        assert breaker.state == CircuitState.OPEN

        time.sleep(0.06)
        # Next call should transition to half-open
        result = breaker.call(succeeding)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED  # Success closes it

    def test_half_open_failure_reopens(self) -> None:
        breaker = make_breaker(failure_threshold=2, cooldown_seconds=0.05)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(failing)

        time.sleep(0.06)
        # Test call fails → reopen
        with pytest.raises(RuntimeError):
            breaker.call(failing)
        assert breaker.state == CircuitState.OPEN


class TestReset:
    def test_reset_closes_circuit(self) -> None:
        breaker = make_breaker(failure_threshold=2)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(failing)
        assert breaker.state == CircuitState.OPEN

        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
