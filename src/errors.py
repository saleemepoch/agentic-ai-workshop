"""
Centralised error handling for upstream provider failures.

Translates exceptions from Anthropic, Voyage AI, and other providers into
structured HTTP responses the frontend can render. Without this, errors
propagate as opaque 500s with stack traces — useless for end users.

Interview talking points:
- Why translate provider errors? Because the frontend shouldn't have to
  understand provider-specific error shapes. The backend normalises them
  into a consistent {provider, error_type, message, status_code} envelope
  so the UI can render any failure the same way.
- Why 502 (Bad Gateway) and not 500? Because these are upstream failures —
  our service is healthy, the provider isn't. 502 communicates that
  precisely. Status codes matter for monitoring and retry logic.
- Why preserve the original error type? So the frontend can show different
  UI for billing errors (link to billing page), rate limits ("try again
  in a moment"), and auth errors ("check your API key configuration").
"""

import logging

import anthropic
import voyageai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _provider_error_payload(
    provider: str,
    error_type: str,
    message: str,
    *,
    user_action: str | None = None,
) -> dict:
    """Build a consistent error envelope for the frontend."""
    return {
        "error": {
            "provider": provider,
            "type": error_type,
            "message": message,
            "user_action": user_action,
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers for upstream provider errors."""

    # ------------------------------------------------------------------
    # Anthropic errors
    # ------------------------------------------------------------------

    @app.exception_handler(anthropic.AuthenticationError)
    async def anthropic_auth(_: Request, exc: anthropic.AuthenticationError) -> JSONResponse:
        logger.error("Anthropic auth error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_provider_error_payload(
                provider="anthropic",
                error_type="authentication_error",
                message=str(exc),
                user_action="Check that ANTHROPIC_API_KEY is set correctly in .env and restart the API server.",
            ),
        )

    @app.exception_handler(anthropic.PermissionDeniedError)
    async def anthropic_permission(
        _: Request, exc: anthropic.PermissionDeniedError
    ) -> JSONResponse:
        logger.error("Anthropic permission error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_provider_error_payload(
                provider="anthropic",
                error_type="permission_denied",
                message=str(exc),
                user_action="Your API key does not have permission for this operation.",
            ),
        )

    @app.exception_handler(anthropic.RateLimitError)
    async def anthropic_rate_limit(_: Request, exc: anthropic.RateLimitError) -> JSONResponse:
        logger.warning("Anthropic rate limit: %s", exc)
        return JSONResponse(
            status_code=429,
            content=_provider_error_payload(
                provider="anthropic",
                error_type="rate_limit",
                message=str(exc),
                user_action="Anthropic rate limit reached. Wait a moment and try again.",
            ),
        )

    @app.exception_handler(anthropic.BadRequestError)
    async def anthropic_bad_request(_: Request, exc: anthropic.BadRequestError) -> JSONResponse:
        msg = str(exc)
        logger.error("Anthropic bad request: %s", msg)
        # The most common BadRequestError in this workshop is "credit balance
        # too low" — surface that with a clear action.
        if "credit balance" in msg.lower():
            return JSONResponse(
                status_code=502,
                content=_provider_error_payload(
                    provider="anthropic",
                    error_type="insufficient_credits",
                    message=msg,
                    user_action=(
                        "Your Anthropic credit balance is too low. Top up at "
                        "console.anthropic.com/settings/billing and ensure your "
                        "API key belongs to the funded workspace."
                    ),
                ),
            )
        return JSONResponse(
            status_code=400,
            content=_provider_error_payload(
                provider="anthropic",
                error_type="bad_request",
                message=msg,
                user_action="The request to Anthropic was rejected. Check the message for details.",
            ),
        )

    @app.exception_handler(anthropic.APIConnectionError)
    async def anthropic_connection(
        _: Request, exc: anthropic.APIConnectionError
    ) -> JSONResponse:
        logger.error("Anthropic connection error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_provider_error_payload(
                provider="anthropic",
                error_type="connection_error",
                message=str(exc),
                user_action="Could not reach Anthropic. Check your internet connection.",
            ),
        )

    @app.exception_handler(anthropic.APIStatusError)
    async def anthropic_status(_: Request, exc: anthropic.APIStatusError) -> JSONResponse:
        # Catch-all for any other Anthropic API error (5xx, etc.)
        logger.error("Anthropic API status error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_provider_error_payload(
                provider="anthropic",
                error_type="api_error",
                message=str(exc),
                user_action="Anthropic returned an unexpected error. See the message for details.",
            ),
        )

    # ------------------------------------------------------------------
    # Voyage AI errors
    # ------------------------------------------------------------------

    @app.exception_handler(voyageai.error.AuthenticationError)
    async def voyage_auth(_: Request, exc: voyageai.error.AuthenticationError) -> JSONResponse:
        logger.error("Voyage auth error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_provider_error_payload(
                provider="voyage_ai",
                error_type="authentication_error",
                message=str(exc),
                user_action="Check that VOYAGE_API_KEY is set correctly in .env and restart the API server.",
            ),
        )

    @app.exception_handler(voyageai.error.RateLimitError)
    async def voyage_rate_limit(_: Request, exc: voyageai.error.RateLimitError) -> JSONResponse:
        msg = str(exc)
        logger.warning("Voyage rate limit: %s", msg)
        # Free-tier message includes specific guidance about adding a payment method
        action = "Voyage AI rate limit reached. Wait a moment and try again."
        if "payment method" in msg.lower():
            action = (
                "You are on the Voyage AI free tier (3 requests/minute). Add a "
                "payment method at dashboard.voyageai.com to remove the throttle "
                "while keeping the 200M free tokens for voyage-3."
            )
        return JSONResponse(
            status_code=429,
            content=_provider_error_payload(
                provider="voyage_ai",
                error_type="rate_limit",
                message=msg,
                user_action=action,
            ),
        )

    @app.exception_handler(voyageai.error.InvalidRequestError)
    async def voyage_invalid(
        _: Request, exc: voyageai.error.InvalidRequestError
    ) -> JSONResponse:
        logger.error("Voyage invalid request: %s", exc)
        return JSONResponse(
            status_code=400,
            content=_provider_error_payload(
                provider="voyage_ai",
                error_type="invalid_request",
                message=str(exc),
                user_action="The request to Voyage AI was rejected.",
            ),
        )

    @app.exception_handler(voyageai.error.APIError)
    async def voyage_api(_: Request, exc: voyageai.error.APIError) -> JSONResponse:
        # Catch-all for any other Voyage error
        logger.error("Voyage API error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_provider_error_payload(
                provider="voyage_ai",
                error_type="api_error",
                message=str(exc),
                user_action="Voyage AI returned an unexpected error.",
            ),
        )
