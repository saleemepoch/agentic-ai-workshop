"""
FastAPI router for resilience demos.

Endpoints simulate failure scenarios so the frontend can demonstrate
each pattern interactively.
"""

import random

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.resilience.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    get_breaker,
    list_breakers,
    reset_all,
)
from src.resilience.fallback import FallbackProvider, fallback_chain
from src.resilience.retry import RetryConfig, retry

router = APIRouter()


class RetryDemoRequest(BaseModel):
    fail_first_n: int = Field(default=2, ge=0, le=10, description="How many attempts to fail")
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=0.1, ge=0, le=5.0)


class FallbackDemoRequest(BaseModel):
    providers: list[str] = Field(
        default_factory=lambda: ["primary", "secondary", "tertiary"]
    )
    fail_until_index: int = Field(default=1, description="Index of provider that succeeds")


class CircuitBreakerDemoRequest(BaseModel):
    service: str = Field(default="demo_service")
    fail: bool = True


@router.post("/demo/retry")
async def demo_retry(body: RetryDemoRequest) -> dict:
    """Demonstrate retry with exponential backoff.

    Simulates a function that fails the first N attempts then succeeds.
    """
    attempt_counter = {"count": 0}

    def flaky_func() -> str:
        attempt_counter["count"] += 1
        if attempt_counter["count"] <= body.fail_first_n:
            raise RuntimeError(f"Simulated failure on attempt {attempt_counter['count']}")
        return f"Success on attempt {attempt_counter['count']}"

    config = RetryConfig(
        max_attempts=body.max_attempts,
        base_delay=body.base_delay,
        jitter=False,  # Deterministic for demo
    )
    result = retry(flaky_func, config)
    return result.to_dict()


@router.post("/demo/fallback")
async def demo_fallback(body: FallbackDemoRequest) -> dict:
    """Demonstrate fallback chain.

    Each provider in the list "fails" until the one at fail_until_index.
    Shows how the chain tries providers until one succeeds.
    """
    def make_func(name: str, should_fail: bool):
        def f():
            if should_fail:
                raise RuntimeError(f"{name} is unavailable")
            return f"Response from {name}"
        return f

    providers = [
        FallbackProvider(
            name=name,
            func=make_func(name, should_fail=(i < body.fail_until_index)),
        )
        for i, name in enumerate(body.providers)
    ]

    result = fallback_chain(providers)
    return result.to_dict()


@router.post("/demo/circuit-breaker")
async def demo_circuit_breaker(body: CircuitBreakerDemoRequest) -> dict:
    """Demonstrate circuit breaker.

    Repeatedly call this endpoint with fail=True to trip the breaker.
    Then call with fail=False after cooldown to see recovery.
    """
    breaker = get_breaker(
        body.service,
        CircuitBreakerConfig(failure_threshold=3, cooldown_seconds=5),
    )

    def func() -> str:
        if body.fail:
            raise RuntimeError(f"Simulated failure for {body.service}")
        return f"Success from {body.service}"

    try:
        value = breaker.call(func)
        return {
            "called": True,
            "rejected_by_breaker": False,
            "result": value,
            "breaker_state": breaker.to_dict(),
        }
    except CircuitBreakerOpenError as e:
        return {
            "called": False,
            "rejected_by_breaker": True,
            "error": str(e),
            "breaker_state": breaker.to_dict(),
        }
    except Exception as e:
        return {
            "called": True,
            "rejected_by_breaker": False,
            "error": str(e),
            "breaker_state": breaker.to_dict(),
        }


@router.get("/circuit-breaker/state")
async def get_circuit_breaker_state() -> dict:
    """Return current state of all circuit breakers."""
    return {"breakers": list_breakers()}


@router.post("/circuit-breaker/reset")
async def reset_circuit_breakers() -> dict:
    """Reset all circuit breakers to closed state."""
    reset_all()
    return {"status": "reset", "breakers": list_breakers()}
