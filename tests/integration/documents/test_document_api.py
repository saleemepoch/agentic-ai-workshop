"""
Integration tests for the document processing API.

These tests hit the real database and test the full HTTP flow:
upload → chunk → compare strategies.

Requires a running PostgreSQL instance with pgvector.
Run with: pytest tests/integration/ -v -m integration
"""

import pytest

from httpx import AsyncClient

pytestmark = pytest.mark.integration

SAMPLE_CV = """SUMMARY
Senior software engineer with 8 years of experience in backend systems and distributed architecture.

EXPERIENCE
Senior Engineer at CloudScale Inc, 2020-2024. Led the migration of a monolithic application to microservices, reducing deployment time by 70%. Designed and implemented a real-time event processing pipeline handling 500K events per second using Kafka and Python.

Software Engineer at DataFlow Ltd, 2016-2020. Built REST APIs serving 2M daily active users. Implemented caching layer with Redis that reduced database load by 60%.

EDUCATION
BSc Computer Science, University of Edinburgh, 2016.

SKILLS
Python, Go, Kubernetes, PostgreSQL, Kafka, Redis, Docker, AWS, Terraform, gRPC.
"""

SAMPLE_JD = """JOB TITLE
Senior Backend Engineer

COMPANY
TechVentures is a Series B startup building the next generation of developer tools.

RESPONSIBILITIES
Design and implement scalable backend services. Lead technical architecture decisions. Mentor junior engineers. Collaborate with product on roadmap.

REQUIREMENTS
5+ years backend development experience. Strong Python or Go skills. Experience with distributed systems. Familiarity with cloud infrastructure (AWS/GCP).

NICE TO HAVE
Experience with Kubernetes. Open source contributions. Prior startup experience.
"""


class TestDocumentUpload:
    """Test document creation endpoints."""

    async def test_upload_cv(self, client: AsyncClient) -> None:
        response = await client.post("/documents", json={
            "title": "Test CV",
            "content": SAMPLE_CV,
            "doc_type": "cv",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test CV"
        assert data["doc_type"] == "cv"
        assert data["id"] > 0
        assert data["chunks"] == []

    async def test_upload_jd(self, client: AsyncClient) -> None:
        response = await client.post("/documents", json={
            "title": "Test JD",
            "content": SAMPLE_JD,
            "doc_type": "jd",
        })
        assert response.status_code == 201
        assert response.json()["doc_type"] == "jd"

    async def test_upload_invalid_type(self, client: AsyncClient) -> None:
        response = await client.post("/documents", json={
            "title": "Bad Doc",
            "content": "Some content",
            "doc_type": "invalid",
        })
        assert response.status_code == 422

    async def test_upload_empty_content(self, client: AsyncClient) -> None:
        response = await client.post("/documents", json={
            "title": "Empty",
            "content": "",
            "doc_type": "cv",
        })
        assert response.status_code == 422


class TestDocumentRetrieval:
    """Test document listing and retrieval."""

    async def test_list_documents(self, client: AsyncClient) -> None:
        # Upload two documents
        await client.post("/documents", json={
            "title": "CV 1", "content": SAMPLE_CV, "doc_type": "cv",
        })
        await client.post("/documents", json={
            "title": "JD 1", "content": SAMPLE_JD, "doc_type": "jd",
        })

        response = await client.get("/documents")
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) >= 2

    async def test_get_single_document(self, client: AsyncClient) -> None:
        upload = await client.post("/documents", json={
            "title": "Fetch Me", "content": SAMPLE_CV, "doc_type": "cv",
        })
        doc_id = upload.json()["id"]

        response = await client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Fetch Me"

    async def test_get_nonexistent_document(self, client: AsyncClient) -> None:
        response = await client.get("/documents/99999")
        assert response.status_code == 404


class TestChunking:
    """Test document chunking endpoints."""

    async def test_semantic_chunking(self, client: AsyncClient) -> None:
        upload = await client.post("/documents", json={
            "title": "Chunk Me", "content": SAMPLE_CV, "doc_type": "cv",
        })
        doc_id = upload.json()["id"]

        response = await client.post(f"/documents/{doc_id}/chunk", json={
            "strategy": "semantic",
            "max_tokens": 100,
            "overlap_tokens": 20,
        })
        assert response.status_code == 200
        chunks = response.json()
        assert len(chunks) >= 3  # Summary, Experience, Education, Skills
        for chunk in chunks:
            assert chunk["strategy"] == "semantic"
            assert chunk["token_count"] > 0
            assert chunk["has_embedding"] is False

    async def test_naive_chunking(self, client: AsyncClient) -> None:
        upload = await client.post("/documents", json={
            "title": "Chunk Naive", "content": SAMPLE_CV, "doc_type": "cv",
        })
        doc_id = upload.json()["id"]

        response = await client.post(f"/documents/{doc_id}/chunk", json={
            "strategy": "naive",
            "max_tokens": 100,
        })
        assert response.status_code == 200
        chunks = response.json()
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk["strategy"] == "naive"

    async def test_compare_strategies(self, client: AsyncClient) -> None:
        upload = await client.post("/documents", json={
            "title": "Compare Me", "content": SAMPLE_CV, "doc_type": "cv",
        })
        doc_id = upload.json()["id"]

        response = await client.post(f"/documents/{doc_id}/compare", json={
            "max_tokens": 100,
            "overlap_tokens": 20,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["semantic_count"] > 0
        assert data["naive_count"] > 0
        assert len(data["semantic_chunks"]) == data["semantic_count"]
        assert len(data["naive_chunks"]) == data["naive_count"]
        assert data["semantic_avg_tokens"] > 0
        assert data["naive_avg_tokens"] > 0

    async def test_rechunking_is_idempotent(self, client: AsyncClient) -> None:
        """Chunking the same document twice should replace, not duplicate."""
        upload = await client.post("/documents", json={
            "title": "Idempotent", "content": SAMPLE_CV, "doc_type": "cv",
        })
        doc_id = upload.json()["id"]

        # Chunk twice with same strategy
        await client.post(f"/documents/{doc_id}/chunk", json={"strategy": "semantic"})
        response = await client.post(f"/documents/{doc_id}/chunk", json={"strategy": "semantic"})
        chunks = response.json()

        # Get the document — should only have one set of semantic chunks
        doc_response = await client.get(f"/documents/{doc_id}")
        doc_chunks = doc_response.json()["chunks"]
        semantic_chunks = [c for c in doc_chunks if c["strategy"] == "semantic"]
        assert len(semantic_chunks) == len(chunks)
