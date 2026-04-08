"""
Pillar 10: Error Handling & Fallbacks

Resilience patterns for production AI systems:
- **Retry with backoff**: handles transient failures
- **Fallback chain**: handles provider outages
- **Circuit breaker**: stops calls to clearly-broken services
- **Timeout management**: prevents indefinite hangs
- **Graceful degradation**: returns partial results rather than nothing

These patterns are built from scratch (~50 lines each) rather than imported
from libraries. The teaching point is *how* they work, not just that they
exist. Students can read the code and understand the failure modes.

Interview talking points:
- Why build instead of using tenacity/circuitbreaker libraries? Because the
  goal is teaching the patterns, not abstracting them away. A decorator that
  "just works" doesn't help students debug a flaky system.
- When does each pattern apply? Retry handles transient failures (timeouts,
  5xx errors). Fallback handles provider outages. Circuit breaker prevents
  wasted calls when a service is clearly down. They compose — typically
  retry inside circuit breaker inside fallback.
- What's the cost? Each retry is another LLM call. Each fallback might use
  a different (potentially more expensive) provider. The patterns trade
  cost for reliability — pick your trade-off based on your SLO.

See ADR-010 for the resilience patterns decision.
"""
