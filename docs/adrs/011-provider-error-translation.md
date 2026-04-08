# ADR-011: Provider Error Translation

## Status
Accepted

## Context

Production AI systems integrate multiple external providers (Anthropic, Voyage AI, Langfuse in this workshop). Each provider has its own exception hierarchy, error message conventions, and failure modes. Without translation, three problems compound:

1. **Stack traces leak to the frontend.** A FastAPI route that raises `anthropic.BadRequestError` produces an HTTP 500 with the traceback in the body. The frontend has no way to render this usefully — users see "Error: Failed to fetch" or a blob of JSON.

2. **The frontend has to know provider internals.** Without a normalised envelope, the React code would need to import `anthropic` types and `voyageai` types and switch on them to render appropriate UI. That's an unreasonable coupling between layers.

3. **Errors look the same regardless of severity.** A 500 from a transient timeout looks identical to a 500 from a missing API key. Users need to know which they're hitting, and the fix is different in each case.

We need a centralised translation layer that converts provider exceptions into a consistent, frontend-friendly error envelope.

## Options Considered

### Option A: Per-route try/except blocks
Each FastAPI route catches provider exceptions and translates them inline.

- **Pro**: Locality — each route handles its own errors
- **Con**: Massive duplication. Every route needs the same translation logic. Inevitable drift between routes. Easy to forget when adding a new route.

### Option B: Centralised FastAPI exception handlers
Register `@app.exception_handler` for each provider exception type once at app startup. Routes just `raise` and the handler does the translation.

- **Pro**: One place to maintain the translation logic. New routes inherit it for free. Clear separation between business logic (raises) and presentation (translates).
- **Con**: Slightly less local — you have to look at `src/errors.py` to understand what happens to a raised exception.

### Option C: Custom middleware
A FastAPI middleware that wraps every request and catches exceptions in a try/except.

- **Pro**: Same centralisation benefit as Option B
- **Con**: Middleware is more invasive than needed. Exception handlers are the FastAPI-native mechanism for this specific job.

### Option D: Don't translate — let stack traces through
Accept that errors look bad and rely on logs for debugging.

- **Pro**: Zero code
- **Con**: Bad UX. Bad teaching example. Real production systems do not do this.

## Decision

**Option B** (centralised FastAPI exception handlers).

Implementation lives in `src/errors.py` and is registered once via `register_error_handlers(app)` in `src/main.py`.

## Rationale

- **Single source of truth.** Every provider exception has exactly one translation, and all routes benefit from it. Adding a new route requires zero error-handling code.
- **Native FastAPI mechanism.** `@app.exception_handler(SomeException)` is the documented way to handle exceptions globally. Using the framework correctly is better than reinventing it.
- **Frontend coupling stays clean.** The frontend only ever sees the structured envelope. It never imports provider-specific types and never has to understand provider-specific error shapes.
- **Status codes carry meaning.** We map thoughtfully: rate limits become 429, auth/permission errors become 502 (the *upstream* failed, not us), bad request becomes 400, and so on. Monitoring and retry logic can act on these correctly.

## The Error Envelope

Every translated error returns the same JSON shape:

```json
{
  "error": {
    "provider": "anthropic" | "voyage_ai" | ...,
    "type": "rate_limit" | "authentication_error" | "insufficient_credits" | ...,
    "message": "<the raw provider message>",
    "user_action": "<actionable next step the user can take>"
  }
}
```

The `user_action` field is the most important part. It's not just "what went wrong" — it's "what should you do about it." Examples:

- **insufficient_credits**: "Your Anthropic credit balance is too low. Top up at console.anthropic.com/settings/billing and ensure your API key belongs to the funded workspace."
- **voyage_ai rate_limit (free tier)**: "You are on the Voyage AI free tier (3 requests/minute). Add a payment method at dashboard.voyageai.com to remove the throttle while keeping the 200M free tokens for voyage-3."
- **authentication_error**: "Check that ANTHROPIC_API_KEY is set correctly in .env and restart the API server."

These are not generic error messages — they reflect actual problems we hit during development and the actual fixes that resolved them. The translation layer is also a place to capture institutional knowledge about provider quirks.

## Special Cases

The `BadRequestError` handler for Anthropic does substring matching on `"credit balance"` to surface a more specific `insufficient_credits` type. This is a small concession to provider-specific diagnostics, justified because "credit balance too low" is one of the most common failures during initial setup and deserves a clearer banner than the generic "bad request."

## Frontend Side

The frontend has a single shared `ErrorBanner` component (`web/src/components/ui/ErrorBanner.tsx`) that:

- Parses the structured envelope
- Renders provider name as a pill, error type as a heading, message verbatim
- Highlights the `user_action` in a separate callout
- Uses warning (yellow) styling for 429s, error (red) for everything else
- Is dismissable

Every page that calls the API uses this component. The result: any error from any provider on any page renders consistently and includes a "what to do" hint.

## Consequences

- A new provider added later (OpenAI, Cohere, etc.) needs its own set of exception handlers in `src/errors.py`. There's no way around this — provider exceptions are provider-specific by definition.
- The handlers must be kept in sync with the provider SDKs. If `voyageai` introduces a new exception type, we won't catch it until we add an explicit handler. This is acceptable because the catch-all `APIError` handler at the bottom of each provider's section catches anything that escapes the specific handlers.
- Logs use `logger.error` for unexpected failures and `logger.warning` for rate limits, so monitoring can distinguish them.
- The translation layer is purely presentational — it does not affect the *resilience* layer (ADR-010). Retry/fallback/circuit-breaker patterns absorb failures they can; this layer translates whatever escapes.

## Where this is implemented

- `src/errors.py` — exception handlers and the `_provider_error_payload` helper
- `src/main.py` — `register_error_handlers(app)` call after CORS middleware
- `web/src/components/ui/ErrorBanner.tsx` — frontend component that parses and renders the envelope
- All 9 pillar pages on the frontend use `ErrorBanner` for any thrown error
