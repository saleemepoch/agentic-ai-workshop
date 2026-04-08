"""
Voyage AI embedding client.

Wraps the Voyage AI SDK to embed text into 1024-dimensional vectors.
All calls are traced via Langfuse @observe for observability (Pillar 5).

Interview talking points:
- Why a wrapper around the SDK? Testability (mock the wrapper, not the SDK),
  observability (add tracing in one place), and abstraction (swap providers
  without touching business logic).
- Why batch embedding? Voyage AI supports batching — sending multiple texts
  in one API call is cheaper and faster than individual calls. This matters
  when embedding hundreds of chunks during document ingestion.
- Why 1024 dimensions? Voyage AI's voyage-3 model outputs 1024-dim vectors.
  This is a good balance: higher dimensions give marginally better results
  but cost more in storage and search time (4KB per vector at float32).
- What about rate limits? With a payment method on file, Voyage's standard
  rate limits are generous enough that the workshop never hits them. If a
  429 does occur, the centralised error handler (src/errors.py) translates
  it into a structured response the frontend renders nicely. We deliberately
  do NOT retry rate limits in this client — fail fast, surface the error,
  let the user decide.

See ADR-002 for the embedding model decision.
"""

import voyageai
from langfuse import observe

from src.config import settings


class EmbeddingClient:
    """Client for generating text embeddings via Voyage AI.

    Uses the voyage-3 model (1024 dimensions). Supports single and batch embedding.
    """

    def __init__(self) -> None:
        self._client: voyageai.Client | None = None
        self.model = "voyage-3"
        self.dimensions = 1024

    @property
    def client(self) -> voyageai.Client:
        """Lazy-initialise the Voyage AI client on first use.

        This avoids failing at import time when the API key isn't set
        (e.g., during testing or when only running unrelated modules).
        """
        if self._client is None:
            self._client = voyageai.Client(api_key=settings.voyage_api_key)
        return self._client

    @observe(name="embed_text")
    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a vector.

        Args:
            text: The text to embed.

        Returns:
            A list of 1024 floats representing the embedding vector.
        """
        result = self.client.embed([text], model=self.model, input_type="document")
        return result.embeddings[0]

    @observe(name="embed_query")
    def embed_query(self, query: str) -> list[float]:
        """Embed a query string for search.

        Voyage AI distinguishes between document and query embeddings.
        Query embeddings are optimised for retrieval — they emphasise
        the aspects of text that are useful for finding relevant documents.
        """
        result = self.client.embed([query], model=self.model, input_type="query")
        return result.embeddings[0]

    @observe(name="embed_batch")
    def embed_batch(self, texts: list[str], input_type: str = "document") -> list[list[float]]:
        """Embed multiple texts in a single API call.

        More efficient than calling embed_text() in a loop — Voyage AI
        processes batches server-side, reducing network overhead.

        Args:
            texts: List of texts to embed.
            input_type: "document" for storage, "query" for search.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []
        result = self.client.embed(texts, model=self.model, input_type=input_type)
        return result.embeddings


# Singleton instance — reused across the application
embedding_client = EmbeddingClient()
