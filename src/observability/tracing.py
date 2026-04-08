"""
Langfuse client initialisation and tracing utilities.

Sets up the Langfuse client and provides the @observe decorator
for wrapping functions with automatic tracing. All LLM calls,
embedding requests, and pipeline stages should use @observe.

Interview talking points:
- Why a singleton client? Langfuse batches trace data and sends it
  asynchronously. A single client instance manages the batch queue
  and connection pool efficiently.
- Why @observe over manual span creation? Less boilerplate. The decorator
  automatically captures function name, arguments, return value, duration,
  and any exceptions. Manual spans are used only when you need custom
  metadata (e.g., token counts).
"""

from langfuse import Langfuse
from langfuse import observe  # noqa: F401 — re-exported for convenience

from src.config import settings

# Langfuse client singleton — lazy initialised
_langfuse_client: Langfuse | None = None


def get_langfuse() -> Langfuse:
    """Get or create the Langfuse client singleton.

    Lazy initialisation avoids failing at import time when
    Langfuse credentials aren't set (e.g., during unit testing).
    """
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    return _langfuse_client


def flush_traces() -> None:
    """Flush any pending traces to Langfuse.

    Called during application shutdown to ensure all traces are sent.
    In normal operation, Langfuse batches and sends automatically.
    """
    if _langfuse_client is not None:
        _langfuse_client.flush()


def shutdown() -> None:
    """Shutdown the Langfuse client and flush pending data."""
    global _langfuse_client
    if _langfuse_client is not None:
        _langfuse_client.shutdown()
        _langfuse_client = None
