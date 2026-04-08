"""
Circuit breaker pattern.

Tracks failure rate per service and "trips" the breaker when failures
exceed a threshold. While open, all calls fail immediately without
hitting the underlying service. After a cooldown, the breaker enters
half-open state and allows one test call to check if the service has
recovered.

States:
- **closed**: normal operation, calls pass through
- **open**: too many failures, all calls fail immediately
- **half-open**: cooldown elapsed, one test call allowed

Interview talking points:
- Why a circuit breaker? Because retrying a service that's clearly down
  wastes time and money. The circuit breaker stops the bleeding by
  short-circuiting calls until the service recovers.
- Why three states? You need a way to test recovery without flooding
  the recovering service. Half-open allows exactly one test call before
  deciding whether to close (recovered) or re-open (still broken).
- Per-service state: each external service has its own circuit breaker.
  A failing Voyage AI shouldn't trip the Anthropic breaker.
"""

import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal, calls pass through
    OPEN = "open"  # Failing, calls fail immediately
    HALF_OPEN = "half_open"  # Testing recovery, one call allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for a single circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    cooldown_seconds: float = 30.0  # Time before half-open
    success_threshold: int = 1  # Successes in half-open before closing


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""

    pass


@dataclass
class CircuitBreaker:
    """Circuit breaker for a single service."""

    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    opened_at: float | None = None

    def call(self, func):
        """Execute a callable through the circuit breaker.

        Raises CircuitBreakerOpenError if the circuit is open and
        the cooldown hasn't elapsed.
        """
        self._maybe_transition_to_half_open()

        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit '{self.name}' is open. Cooldown remaining: "
                f"{self._cooldown_remaining():.1f}s"
            )

        try:
            result = func()
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    def _record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close()
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0

    def _record_failure(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            # Failed test call → reopen
            self._open()
            return

        self.failure_count += 1
        if self.failure_count >= self.config.failure_threshold:
            self._open()

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = time.monotonic()
        self.success_count = 0

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None

    def _half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0

    def _maybe_transition_to_half_open(self) -> None:
        if self.state == CircuitState.OPEN and self._cooldown_remaining() <= 0:
            self._half_open()

    def _cooldown_remaining(self) -> float:
        if self.opened_at is None:
            return 0.0
        elapsed = time.monotonic() - self.opened_at
        return max(0.0, self.config.cooldown_seconds - elapsed)

    def reset(self) -> None:
        """Manually reset the circuit to closed state."""
        self._close()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "cooldown_seconds": self.config.cooldown_seconds,
                "success_threshold": self.config.success_threshold,
            },
            "cooldown_remaining_seconds": round(self._cooldown_remaining(), 2),
        }


# Per-service breakers, accessed by name
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name, config=config or CircuitBreakerConfig())
    return _breakers[name]


def list_breakers() -> dict[str, dict]:
    """Return state of all known circuit breakers."""
    return {name: br.to_dict() for name, br in _breakers.items()}


def reset_all() -> None:
    """Reset all circuit breakers (useful for tests)."""
    for breaker in _breakers.values():
        breaker.reset()
