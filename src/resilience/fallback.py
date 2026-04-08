"""
Fallback chain pattern.

Tries a sequence of providers in order, returning the first success.
Records which provider was used and the failures of earlier ones.

Interview talking points:
- Why a fallback chain? Because vendor lock-in is risk. If your primary
  provider is down, your product is down. A fallback chain — primary →
  secondary → tertiary — keeps you running through provider outages.
- What about quality differences? Fallback providers may give worse
  results. That's the trade-off — degraded quality is better than no
  service. The frontend can show which provider was used so the team
  knows the result is from a fallback.
- How does this compose with retry? Typically: retry the primary a few
  times, then fall back. Don't fall back on the first failure — transient
  errors are common.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class FallbackProvider:
    """A single provider in a fallback chain."""

    name: str
    func: Callable[[], Any]


@dataclass
class FallbackAttempt:
    """A record of trying one provider."""

    provider: str
    success: bool
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class FallbackResult:
    """The outcome of a fallback chain run."""

    success: bool
    value: Any = None
    provider_used: str | None = None
    attempts: list[FallbackAttempt] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "provider_used": self.provider_used,
            "attempts": [
                {
                    "provider": a.provider,
                    "success": a.success,
                    "error": a.error,
                    "duration_ms": round(a.duration_ms, 2),
                }
                for a in self.attempts
            ],
            "fallback_count": len(self.attempts) - 1 if self.success else len(self.attempts),
        }


def fallback_chain(providers: list[FallbackProvider]) -> FallbackResult:
    """Try providers in order, return the first success.

    Args:
        providers: Ordered list of providers to try.

    Returns:
        FallbackResult with the value (if any), the provider used, and
        the failure history.
    """
    result = FallbackResult(success=False)

    for provider in providers:
        start = time.perf_counter()
        attempt = FallbackAttempt(provider=provider.name, success=False)

        try:
            value = provider.func()
            attempt.success = True
            attempt.duration_ms = (time.perf_counter() - start) * 1000
            result.attempts.append(attempt)
            result.success = True
            result.value = value
            result.provider_used = provider.name
            return result
        except Exception as e:
            attempt.error = f"{type(e).__name__}: {e}"
            attempt.duration_ms = (time.perf_counter() - start) * 1000
            result.attempts.append(attempt)
            continue

    return result
