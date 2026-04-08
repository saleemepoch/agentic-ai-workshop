# ADR-010: Error Handling & Fallbacks

## Status
Accepted

## Context

External AI services fail. APIs time out, rate limits trigger, services go down, models return garbage. Production AI systems need to handle these failures gracefully — not by hiding them, but by recovering when possible and degrading gracefully when not.

The patterns we need:
- **Retry with backoff**: transient failures (timeouts, 5xx errors) usually resolve themselves
- **Fallback chain**: if the primary provider fails, try a secondary
- **Circuit breaker**: stop calling a service that's clearly down — don't waste retries
- **Timeout management**: set per-step and per-request timeouts so a slow call doesn't block indefinitely
- **Graceful degradation**: return partial results rather than nothing

## Options Considered

### Option A: Build the patterns from scratch
- Custom retry, fallback, circuit breaker implementations
- **Pro**: Visible internals (teaching value), zero dependencies, matches the workshop's "no hidden magic" philosophy
- **Con**: More code to write and maintain

### Option B: Use existing libraries
- `tenacity` for retries, `circuitbreaker` for circuit breaker
- **Pro**: Less code, battle-tested
- **Con**: Hides the mechanics. Students see decorators instead of logic.

### Option C: LangChain's resilience features
- LangChain has built-in retry and fallback for LLM chains
- **Pro**: Tight LangGraph integration
- **Con**: LangChain ecosystem lock-in. Doesn't teach the patterns generically.

## Decision

**Option A** (build from scratch).

## Rationale

- **Teaching value**: Students need to understand *how* circuit breakers work, not just that they exist. The implementation is short enough (~50 lines per pattern) to be readable and instructive.
- **Provider-agnostic**: The patterns work for any external service — not just LLMs. The workshop teaches the principles, not the libraries.
- **No magic**: A decorator that "just works" doesn't help students debug a flaky system. Building it ourselves means students can read the code and understand the failure modes.

## Consequences

- We maintain ~150 lines of resilience code instead of importing it
- Each pattern is independently testable
- The patterns can be composed (retry + fallback + circuit breaker)
- The frontend can simulate failures and show each pattern's behaviour

## Relationship to error handling at the API boundary

This ADR covers the *resilience* side: what to do when an external call fails. There's a complementary concern — how to *surface* failures to the user when resilience can't recover. That belongs to **ADR-011 (Provider Error Translation)**, which describes the centralised exception handlers in `src/errors.py` that convert provider-specific exceptions (Anthropic, Voyage AI) into structured HTTP responses the frontend renders as actionable error banners.

The two work together: Pillar 10's resilience patterns absorb the failures they can; whatever escapes goes through ADR-011's translation layer so the user sees a coherent error instead of a stack trace.

## Where the resilience patterns are NOT applied

Worth being explicit: the embedder client (`src/matching/embedder.py`) does **not** wrap its calls in the retry helper. We tried it briefly to handle Voyage AI's free-tier rate limit and reverted the change. The reason: rate-limit windows on the free tier are ~60 seconds wide, so any backoff long enough to clear the window also produces an unacceptably bad UX (30+ seconds of frozen frontend per retry). Adding a payment method to Voyage was the correct fix; the retry pattern was the wrong tool for this specific failure mode.

The lesson worth keeping: resilience patterns are not free. They trade latency for success rate. Pick the trade-off based on the actual failure characteristics, not on "more resilience is always better."

## Patterns

### Retry with Exponential Backoff
- Configurable max retries (default 3)
- Exponential delay: 1s, 2s, 4s, 8s...
- Jitter to avoid thundering herd
- Optional retry-with-modified-prompt for LLM-specific failures

### Fallback Chain
- Ordered list of provider/model options
- Try each in order, return first success
- Record which provider was used
- Surface the failure mode of earlier providers in the result

### Circuit Breaker
- Three states: closed (normal), open (failing), half-open (testing recovery)
- Configurable failure threshold (default: 5 failures in 60 seconds)
- Configurable cooldown (default: 30 seconds before half-open)
- Per-service tracking — independent state per provider

### Timeouts
- Per-step timeout (default: 30s for LLM calls)
- Per-request timeout (default: 120s for full pipeline)
- Timeout errors trigger retry/fallback chain

## Composition Example

```python
@retry(max_attempts=3, backoff=exponential)
@circuit_breaker(failure_threshold=5)
@timeout(seconds=30)
def call_llm(prompt: str) -> str:
    ...
```

In the workshop, we don't use decorators (to keep the logic visible), but the patterns compose the same way.
