"""
Unit tests for retry with exponential backoff.

Pure logic tests — no external dependencies. Uses fast delays.
"""

import pytest

from src.resilience.retry import RetryConfig, calculate_delay, retry


class TestCalculateDelay:
    def test_first_attempt_no_delay(self) -> None:
        config = RetryConfig(base_delay=1.0, jitter=False)
        assert calculate_delay(1, config) == 0.0

    def test_exponential_growth(self) -> None:
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        # Attempt 2: 1.0, Attempt 3: 2.0, Attempt 4: 4.0
        assert calculate_delay(2, config) == 1.0
        assert calculate_delay(3, config) == 2.0
        assert calculate_delay(4, config) == 4.0

    def test_max_delay_cap(self) -> None:
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=False)
        # Would be 16, but capped at 5
        assert calculate_delay(10, config) == 5.0

    def test_jitter_within_bounds(self) -> None:
        config = RetryConfig(base_delay=1.0, jitter=True)
        delay = calculate_delay(3, config)
        assert 0 <= delay <= 2.0  # base * 2^1 = 2, jitter is 0-2


class TestRetry:
    def test_success_first_attempt(self) -> None:
        result = retry(lambda: "success", RetryConfig(max_attempts=3))
        assert result.success is True
        assert result.value == "success"
        assert len(result.attempts) == 1

    def test_success_after_retries(self) -> None:
        counter = {"n": 0}

        def flaky():
            counter["n"] += 1
            if counter["n"] < 3:
                raise RuntimeError("transient")
            return "ok"

        result = retry(flaky, RetryConfig(max_attempts=5, base_delay=0.01, jitter=False))
        assert result.success is True
        assert result.value == "ok"
        assert len(result.attempts) == 3

    def test_max_attempts_exceeded(self) -> None:
        def always_fails():
            raise RuntimeError("nope")

        result = retry(
            always_fails, RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)
        )
        assert result.success is False
        assert len(result.attempts) == 3
        assert result.final_error is not None
        assert "nope" in result.final_error

    def test_all_attempts_recorded(self) -> None:
        def always_fails():
            raise ValueError("fail")

        result = retry(
            always_fails, RetryConfig(max_attempts=4, base_delay=0.01, jitter=False)
        )
        assert len(result.attempts) == 4
        for i, attempt in enumerate(result.attempts, start=1):
            assert attempt.attempt == i
            assert attempt.success is False
            assert attempt.error is not None

    def test_retry_on_specific_exception(self) -> None:
        def raises_value_error():
            raise ValueError("specific")

        # Only retry on RuntimeError → ValueError should propagate
        config = RetryConfig(
            max_attempts=3, base_delay=0.01, jitter=False, retry_on=(RuntimeError,)
        )
        with pytest.raises(ValueError):
            retry(raises_value_error, config)
