"""
Integration tests for embedding storage and vector retrieval.

Tests the full flow: embed text → store in pgvector → search by similarity.
Requires a running PostgreSQL instance with pgvector and a valid VOYAGE_API_KEY.

Run with: pytest tests/integration/matching/ -v -m integration
"""

import pytest

from httpx import AsyncClient

pytestmark = pytest.mark.integration


SAMPLE_CHUNKS = [
    {
        "title": "Python Dev CV",
        "content": "Senior Python developer with 8 years of experience in Django, FastAPI, and distributed systems. Led migration of monolithic app to microservices at CloudScale Inc.",
        "doc_type": "cv",
    },
    {
        "title": "Data Scientist CV",
        "content": "Data scientist specialising in NLP and recommendation systems. Built ML pipeline processing 10M records daily using PyTorch and Spark at DataCorp.",
        "doc_type": "cv",
    },
    {
        "title": "UX Designer CV",
        "content": "UX design lead with 6 years creating enterprise SaaS products. Expert in Figma, user research, and design systems. Led redesign that improved conversion by 35%.",
        "doc_type": "cv",
    },
]


class TestEmbedAndSearch:
    """Test embedding storage and similarity search."""

    async def test_embed_text_endpoint(self, client: AsyncClient) -> None:
        response = await client.post("/embeddings/embed", json={
            "text": "A test document about Python programming.",
            "input_type": "document",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["dimensions"] == 1024
        assert len(data["embedding"]) == 1024

    async def test_search_returns_relevant_results(self, client: AsyncClient) -> None:
        """Upload documents, chunk, embed, then search."""
        # Upload and chunk documents
        doc_ids = []
        for doc in SAMPLE_CHUNKS:
            upload = await client.post("/documents", json=doc)
            doc_id = upload.json()["id"]
            doc_ids.append(doc_id)
            await client.post(f"/documents/{doc_id}/chunk", json={
                "strategy": "semantic", "max_tokens": 500,
            })

        # Embed all chunks
        response = await client.post("/embeddings/embed-all")
        assert response.status_code == 200
        assert response.json()["embedded_count"] > 0

        # Search for Python developers
        search_response = await client.post("/embeddings/search", json={
            "query": "Looking for an experienced Python backend developer",
            "top_k": 3,
            "distance_metric": "cosine",
        })
        assert search_response.status_code == 200
        results = search_response.json()["results"]
        assert len(results) > 0

        # The Python dev CV should rank highest
        top_result = results[0]
        assert top_result["similarity"] > 0.5
        assert "Python" in top_result["content"]

    async def test_compare_metrics_returns_all_three(self, client: AsyncClient) -> None:
        """Upload, embed, then compare distance metrics."""
        # Upload and chunk a document
        upload = await client.post("/documents", json={
            "title": "Test Doc",
            "content": "Machine learning engineer with expertise in deep learning and NLP.",
            "doc_type": "cv",
        })
        doc_id = upload.json()["id"]
        await client.post(f"/documents/{doc_id}/chunk", json={
            "strategy": "semantic", "max_tokens": 500,
        })
        await client.post("/embeddings/embed-all")

        # Compare metrics
        response = await client.post("/embeddings/compare-metrics", json={
            "query": "ML engineer needed for NLP project",
            "top_k": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert "cosine" in data
        assert "euclidean" in data
        assert "inner_product" in data
