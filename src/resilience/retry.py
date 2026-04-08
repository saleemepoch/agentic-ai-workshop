"""
Retry with exponential backoff and jitter.

Retries a callable on failure with progressively longer delays between
attempts. Includes jitter to prevent thundering herd when multiple
clients retry simultaneously.

Interview talking points:
- Why exponential backoff? Because failing services usually need time to
  recover. Hammering them with retries every 100ms makes things worse.
  Doubling the delay each time gives the service room to breathe.
- Why jitter? Because if 1000 clients all hit the same exponential schedule,
  they synchronise their retries and create traffic spikes. Adding random
  jitter spreads them out.
- When NOT to retry? When the error is permanent (4xx errors, validation
  failures, auth errors). Retrying these wastes calls. Only retry on
  transient errors (5xx, timeouts, network errors).
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    # If set, only retry these exception types. Otherwise retry any.
    retry_on: tuple[type[Exception], ...] = (Exception,)


@dataclass
class RetryAttempt:
    """A record of a single retry attempt."""

    attempt: int
    delay_before: float
    error: str | None
    success: bool


@dataclass
class RetryResult:
    """The outcome of a retry sequence."""

    success: bool
    value: Any = None
    attempts: list[RetryAttempt] = field(default_factory=list)
    final_error: str | None = None
    total_duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "value": str(self.value) if self.value is not None else None,
            "attempts": [
                {
                    "attempt": a.attempt,
                    "delay_before": round(a.delay_before, 3),
                    "error": a.error,
                    "success": a.success,
                }
                for a in self.attempts
            ],
            "total_attempts": len(self.attempts),
            "final_error": self.final_error,
            "total_duration_seconds": round(self.total_duration, 3),
        }


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate the delay before a given attempt number (1-indexed).

    Returns 0 for attempt 1 (no initial delay).
    """
    if attempt <= 1:
        return 0.0

    delay = config.base_delay * (config.exponential_base ** (attempt - 2))
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Full jitter: random value between 0 and the calculated delay
        delay = random.uniform(0, delay)

    return delay


def retry(
    func: Callable[[], T],
    config: RetryConfig | None = None,
) -> RetryResult:
    """Retry a callable with exponential backoff.

    Args:
        func: Zero-argument callable to invoke. Use a lambda to bind args.
        config: Retry configuration. Uses defaults if not provided.

    Returns:
        RetryResult with the final outcome and per-attempt history.
    """
    cfg = config or RetryConfig()
    result = RetryResult(success=False)
    start = time.perf_counter()

    for attempt_num in range(1, cfg.max_attempts + 1):
        delay = calculate_delay(attempt_num, cfg)
        if delay > 0:
            time.sleep(delay)

        attempt = RetryAttempt(
            attempt=attempt_num,
            delay_before=delay,
            error=None,
            success=False,
        )

        try:
            value = func()
            attempt.success = True
            result.attempts.append(attempt)
            result.success = True
            result.value = value
            result.total_duration = time.perf_counter() - start
            return result
        except cfg.retry_on as e:
            attempt.error = f"{type(e).__name__}: {e}"
            result.attempts.append(attempt)
            result.final_error = attempt.error
            continue

    result.total_duration = time.perf_counter() - start
    return result
