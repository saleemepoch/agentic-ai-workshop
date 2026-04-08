"""
Unit tests for the embedding client.

Tests input validation and batch handling. These tests use the real
Voyage AI API — they verify the client wrapper works correctly.

Note: These tests require a valid VOYAGE_API_KEY in .env with a payment
method on file. The free tier (3 RPM) is too slow to run the full suite
without artificial delays; standard tier has no such constraint.
"""

import pytest

from src.matching.embedder import EmbeddingClient


@pytest.fixture
def client() -> EmbeddingClient:
    return EmbeddingClient()


class TestEmbeddingClient:
    """Tests for the Voyage AI embedding wrapper."""

    def test_embed_text_returns_correct_dimensions(self, client: EmbeddingClient) -> None:
        vector = client.embed_text("A sample document about Python programming.")
        assert len(vector) == 1024
        assert all(isinstance(v, float) for v in vector)

    def test_embed_query_returns_correct_dimensions(self, client: EmbeddingClient) -> None:
        vector = client.embed_query("Find Python developers")
        assert len(vector) == 1024

    def test_embed_batch_returns_matching_count(self, client: EmbeddingClient) -> None:
        texts = [
            "First document about data science.",
            "Second document about machine learning.",
            "Third document about product management.",
        ]
        vectors = client.embed_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) == 1024 for v in vectors)

    def test_embed_batch_empty_list(self, client: EmbeddingClient) -> None:
        vectors = client.embed_batch([])
        assert vectors == []

    def test_different_texts_produce_different_embeddings(
        self, client: EmbeddingClient
    ) -> None:
        v1 = client.embed_text("Python software engineer with 10 years experience")
        v2 = client.embed_text("Pastry chef specialising in French desserts")
        # Vectors should be different for semantically different texts
        assert v1 != v2

    def test_similar_texts_produce_similar_embeddings(
        self, client: EmbeddingClient
    ) -> None:
        v1 = client.embed_text("Senior Python developer with AWS experience")
        v2 = client.embed_text("Experienced Python engineer skilled in cloud infrastructure")
        # Compute cosine similarity manually
        dot_product = sum(a * b for a, b in zip(v1, v2))
        mag1 = sum(a * a for a in v1) ** 0.5
        mag2 = sum(b * b for b in v2) ** 0.5
        similarity = dot_product / (mag1 * mag2)
        # Similar texts should have high cosine similarity
        assert similarity > 0.7
