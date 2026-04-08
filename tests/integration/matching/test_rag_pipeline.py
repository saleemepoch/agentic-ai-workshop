"""
Integration tests for the full RAG pipeline.

Tests the end-to-end flow: upload → chunk → embed → RAG query.
Requires PostgreSQL, VOYAGE_API_KEY, and ANTHROPIC_API_KEY.

Run with: pytest tests/integration/matching/test_rag_pipeline.py -v -m integration
"""

import pytest

from httpx import AsyncClient

pytestmark = pytest.mark.integration


class TestRAGPipeline:
    """End-to-end RAG pipeline tests."""

    async def test_full_pipeline_returns_staged_results(self, client: AsyncClient) -> None:
        """Run the full pipeline and verify all stages are present."""
        # Setup: upload, chunk, embed a CV
        upload = await client.post("/documents", json={
            "title": "Pipeline Test CV",
            "content": """SUMMARY
Senior backend engineer with 8 years building distributed systems in Python.

EXPERIENCE
Senior Engineer at CloudScale, 2020-2024. Designed event-driven architecture processing 500K events/sec. Led migration from monolith to microservices.

Software Engineer at DataFlow, 2016-2020. Built REST APIs for 2M daily users using Django and FastAPI. Implemented Redis caching layer.

SKILLS
Python, Go, Kubernetes, PostgreSQL, Kafka, Redis, Docker, AWS, Terraform.""",
            "doc_type": "cv",
        })
        doc_id = upload.json()["id"]
        await client.post(f"/documents/{doc_id}/chunk", json={
            "strategy": "semantic", "max_tokens": 300,
        })
        await client.post("/embeddings/embed-all")

        # Run RAG pipeline
        response = await client.post("/embeddings/rag/run", json={
            "query": "Looking for a senior Python developer with microservices experience",
            "top_k": 5,
            "distance_metric": "cosine",
            "doc_type": "cv",
        })
        assert response.status_code == 200
        data = response.json()

        # Verify all 5 stages are present
        stage_names = [s["stage"] for s in data["stages"]]
        assert "embed_query" in stage_names
        assert "retrieve" in stage_names
        assert "rerank" in stage_names
        assert "build_prompt" in stage_names
        assert "generate" in stage_names

        # Verify final output is non-empty and grounded
        assert len(data["final_output"]) > 50
        assert data["total_tokens"] > 0
        assert data["total_cost"] > 0
        assert data["total_duration_ms"] > 0

        # Verify each stage has timing
        for stage in data["stages"]:
            assert stage["duration_ms"] >= 0

    async def test_pipeline_with_no_documents(self, client: AsyncClient) -> None:
        """Pipeline should handle gracefully when no documents are embedded."""
        response = await client.post("/embeddings/rag/run", json={
            "query": "Find me a data scientist",
            "top_k": 5,
        })
        assert response.status_code == 200
        data = response.json()
        # Should have at least embed + retrieve stages, then a graceful message
        assert "No relevant documents found" in data["final_output"]
