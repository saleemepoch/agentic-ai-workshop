"""
Unit tests for the LLM-based reranker.

Tests scoring, sort order, and edge cases. The reranker is async and runs
chunk scoring in parallel via asyncio.gather, so these tests are async too.

Requires ANTHROPIC_API_KEY in .env.
"""

import pytest

from src.matching.reranker import Reranker


@pytest.fixture
def reranker_instance() -> Reranker:
    return Reranker()


@pytest.mark.asyncio
class TestReranker:
    """Tests for LLM-based chunk reranking."""

    async def test_score_relevant_chunk_high(self, reranker_instance: Reranker) -> None:
        """A highly relevant chunk should score >= 6."""
        result = await reranker_instance.score_chunk(
            query="Senior Python backend developer with API experience",
            chunk_content="8 years of Python development experience. Built REST APIs serving 2M daily users using FastAPI and Django. Led backend architecture at CloudScale Inc.",
        )
        assert result["score"] >= 6
        assert len(result["reasoning"]) > 0

    async def test_score_irrelevant_chunk_low(self, reranker_instance: Reranker) -> None:
        """A completely irrelevant chunk should score low."""
        result = await reranker_instance.score_chunk(
            query="Senior Python backend developer with API experience",
            chunk_content="Professional pastry chef with 10 years in French patisserie. Specialises in wedding cakes and chocolate sculptures.",
        )
        assert result["score"] <= 4

    async def test_rerank_sorts_by_score(self, reranker_instance: Reranker) -> None:
        """After reranking, chunks should be sorted by score descending."""
        chunks = [
            {"content": "UX designer with Figma experience.", "chunk_id": 1},
            {"content": "Python developer with 10 years of Django and FastAPI.", "chunk_id": 2},
            {"content": "Marketing manager for consumer products.", "chunk_id": 3},
        ]
        reranked = await reranker_instance.rerank(
            query="Looking for a Python backend engineer",
            chunks=chunks,
        )
        # Scores should be in descending order
        scores = [c["rerank_score"] for c in reranked]
        assert scores == sorted(scores, reverse=True)
        # Each chunk should have rerank fields added
        for chunk in reranked:
            assert "rerank_score" in chunk
            assert "rerank_reasoning" in chunk

    async def test_rerank_top_k(self, reranker_instance: Reranker) -> None:
        """top_k should limit the number of returned chunks."""
        chunks = [
            {"content": f"Chunk {i} about various topics.", "chunk_id": i}
            for i in range(5)
        ]
        reranked = await reranker_instance.rerank(
            query="Any topic",
            chunks=chunks,
            top_k=2,
        )
        assert len(reranked) == 2

    async def test_rerank_empty_list(self, reranker_instance: Reranker) -> None:
        """Empty input should return empty output without making any LLM calls."""
        reranked = await reranker_instance.rerank(query="anything", chunks=[])
        assert reranked == []
