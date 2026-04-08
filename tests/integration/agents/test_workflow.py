"""
Integration tests for the full agent workflow.

Runs the complete LangGraph state machine with real LLM calls.
Requires ANTHROPIC_API_KEY.

Run with: pytest tests/integration/agents/ -v -m integration
"""

import pytest

from httpx import AsyncClient

pytestmark = pytest.mark.integration

SAMPLE_CV = """SUMMARY
Senior Python developer with 8 years building scalable backend systems.

EXPERIENCE
Senior Engineer at CloudScale Inc, 2020-2024. Led microservices migration, reduced deployment time by 70%. Designed event-driven architecture handling 500K events/sec.

Software Engineer at DataFlow Ltd, 2016-2020. Built REST APIs serving 2M daily users with Django and FastAPI. Implemented Redis caching.

EDUCATION
BSc Computer Science, University of Edinburgh, 2016.

SKILLS
Python, Go, FastAPI, Django, Kubernetes, PostgreSQL, Kafka, Redis, AWS, Terraform.
"""

SAMPLE_JD = """JOB TITLE
Senior Backend Engineer

COMPANY
TechVentures — Series B startup building developer tools.

RESPONSIBILITIES
Design scalable backend services. Lead technical architecture decisions. Mentor junior engineers.

REQUIREMENTS
5+ years backend development. Strong Python skills. Experience with distributed systems. Cloud infrastructure experience (AWS/GCP).

NICE TO HAVE
Kubernetes experience. Open source contributions.
"""

WEAK_CV = """SUMMARY
Junior marketing coordinator with 2 years experience in social media management.

EXPERIENCE
Marketing Coordinator at BrandCo, 2022-2024. Managed Instagram and TikTok accounts. Created content calendars.

EDUCATION
BA Communications, University of Leeds, 2022.

SKILLS
Social media, Canva, content writing, basic HTML.
"""


class TestAgentWorkflow:
    """Full workflow execution tests."""

    async def test_strong_match_goes_to_outreach(self, client: AsyncClient) -> None:
        """A good CV/JD match should route through screening to outreach."""
        response = await client.post("/agents/run", json={
            "cv_text": SAMPLE_CV,
            "jd_text": SAMPLE_JD,
        })
        assert response.status_code == 200
        data = response.json()

        # Should have parsed both documents
        assert data["parsed_cv"] != {}
        assert data["parsed_jd"] != {}

        # Should have a match score
        assert 0 <= data["match_score"] <= 1
        assert len(data["match_reasoning"]) > 0
        assert len(data["strengths"]) > 0

        # Strong match should route to screen
        assert data["match_score"] >= 0.5  # Should be a strong match
        assert data["route_decision"] in ("screen", "review")

        # Should have screening result and outreach
        assert data["screening_result"] is not None
        assert data["outreach_email"] is not None

        # Should have execution steps
        assert len(data["steps"]) >= 5  # parse_cv, parse_jd, match, route, screen, outreach
        assert data["total_tokens"] > 0

    async def test_weak_match_gets_rejected(self, client: AsyncClient) -> None:
        """A poor CV/JD match should route to rejection."""
        response = await client.post("/agents/run", json={
            "cv_text": WEAK_CV,
            "jd_text": SAMPLE_JD,
        })
        assert response.status_code == 200
        data = response.json()

        # Should have a low match score
        assert data["match_score"] < 0.5
        assert data["route_decision"] == "reject"
        assert data["rejection_reason"] is not None
        assert data["outreach_email"] is None

    async def test_graph_structure_endpoint(self, client: AsyncClient) -> None:
        """Graph structure endpoint should return nodes and edges."""
        response = await client.get("/agents/graph")
        assert response.status_code == 200
        data = response.json()
        # 11 nodes in the refactored topology (parse + chunk + embed + parse_jd
        # + extract + retrieve + score + route + screen + reject + outreach)
        assert len(data["nodes"]) == 11
        assert len(data["edges"]) >= 11

        # Verify key nodes exist and tools are surfaced
        node_ids = {n["id"] for n in data["nodes"]}
        assert "parse_cv" in node_ids
        assert "chunk_cv" in node_ids
        assert "embed_cv_chunks" in node_ids
        assert "extract_requirements" in node_ids
        assert "retrieve_evidence" in node_ids
        assert "score_match" in node_ids
        assert "route_candidate" in node_ids
        assert "generate_outreach" in node_ids

        # Each node should declare which tool it uses
        tools = {n["id"]: n["tool"] for n in data["nodes"]}
        assert tools["parse_cv"] == "regex"
        assert tools["chunk_cv"] == "regex"
        assert tools["embed_cv_chunks"] == "embedding"
        assert tools["retrieve_evidence"] == "vector_search"
        assert tools["score_match"] == "llm"
        assert tools["route_candidate"] == "logic"
