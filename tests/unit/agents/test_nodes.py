"""
Unit tests for agent node functions.

Tests the pure-logic and pure-regex nodes in isolation. Nodes that touch
external services (LLM, embedding, database) are covered by the integration
tests.
"""

import pytest

from src.agents.nodes import reject_candidate, route_candidate
from src.agents.parsers import parse_cv as regex_parse_cv
from src.agents.parsers import parse_jd_sections
from src.agents.state import RecruitmentState


@pytest.mark.asyncio
class TestRouteCandidate:
    """Route candidate based on match score — pure logic, no LLM, no DB."""

    async def test_high_score_routes_to_screen(self) -> None:
        state: RecruitmentState = {"match_score": 0.85, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "screen"

    async def test_medium_score_routes_to_review(self) -> None:
        state: RecruitmentState = {"match_score": 0.55, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "review"

    async def test_low_score_routes_to_reject(self) -> None:
        state: RecruitmentState = {"match_score": 0.20, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "reject"

    async def test_boundary_065_routes_to_screen(self) -> None:
        state: RecruitmentState = {"match_score": 0.65, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "screen"

    async def test_just_below_065_routes_to_review(self) -> None:
        state: RecruitmentState = {"match_score": 0.64, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "review"

    async def test_boundary_030_routes_to_review(self) -> None:
        state: RecruitmentState = {"match_score": 0.30, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "review"

    async def test_just_below_030_routes_to_reject(self) -> None:
        state: RecruitmentState = {"match_score": 0.29, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "reject"

    async def test_zero_score_routes_to_reject(self) -> None:
        state: RecruitmentState = {"match_score": 0.0, "step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "reject"

    async def test_adds_step_to_history(self) -> None:
        state: RecruitmentState = {"match_score": 0.85, "step_history": []}
        result = await route_candidate(state)
        assert len(result["step_history"]) == 1
        assert result["step_history"][0]["node"] == "route_candidate"
        assert result["step_history"][0]["decision"] == "screen"
        assert result["step_history"][0]["tool"] == "logic"

    async def test_missing_score_defaults_to_reject(self) -> None:
        state: RecruitmentState = {"step_history": []}
        result = await route_candidate(state)
        assert result["route_decision"] == "reject"


@pytest.mark.asyncio
class TestRejectCandidate:
    """Reject node — pure logic, generates a rejection reason."""

    async def test_includes_score(self) -> None:
        state: RecruitmentState = {
            "match_score": 0.25,
            "gaps": ["No Python", "No Kubernetes"],
            "step_history": [],
        }
        result = await reject_candidate(state)
        assert "0.25" in result["rejection_reason"]
        assert "No Python" in result["rejection_reason"]


class TestRegexParseCV:
    """Pure-regex CV parser — no LLM, no DB."""

    def test_extracts_name(self) -> None:
        cv = """JANE DOE\nSenior Engineer\n\nSUMMARY\n8 years of Python."""
        result = regex_parse_cv(cv)
        assert result["name"] == "JANE DOE"

    def test_extracts_sections(self) -> None:
        cv = """John Doe\n\nSUMMARY\nA developer.\n\nSKILLS\nPython, Go, Rust\n\nEDUCATION\nMIT 2020"""
        result = regex_parse_cv(cv)
        assert result["section_count"] >= 3
        assert "summary" in result["sections"]
        assert "skills" in result["sections"]
        assert "education" in result["sections"]

    def test_extracts_skills_list(self) -> None:
        cv = """Jane Doe\n\nSKILLS\nPython, Go, Kubernetes, PostgreSQL"""
        result = regex_parse_cv(cv)
        assert "Python" in result["skills"]
        assert "Kubernetes" in result["skills"]
        assert len(result["skills"]) == 4

    def test_handles_no_skills(self) -> None:
        cv = """Jane Doe\n\nSUMMARY\nA developer."""
        result = regex_parse_cv(cv)
        assert result["skills"] == []


class TestRegexParseJD:
    """Pure-regex JD parser — extracts structural sections."""

    def test_extracts_title(self) -> None:
        jd = """Senior Backend Engineer\n\nCOMPANY\nAcme Inc"""
        result = parse_jd_sections(jd)
        assert result["title"] == "Senior Backend Engineer"

    def test_extracts_sections(self) -> None:
        jd = """JOB TITLE\nSenior Engineer\n\nREQUIREMENTS\n5+ years Python\n\nNICE TO HAVE\nKubernetes"""
        result = parse_jd_sections(jd)
        assert result["section_count"] >= 2
