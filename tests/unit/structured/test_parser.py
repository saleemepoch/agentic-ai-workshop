"""
Unit tests for the parse-validate-retry pipeline.

Tests the schemas and the helper logic without calling the LLM.
The integration test exercises the actual retry behaviour with real Claude calls.
"""

import pytest
from pydantic import ValidationError

from src.structured.output_models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    JobRequirements,
    MatchAssessment,
    OutreachEmail,
    ScreeningDecision,
)
from src.structured.parser import ParseAttempt, ParseResult, StructuredParser


class TestCandidateProfileSchema:
    def test_minimal_valid(self) -> None:
        profile = CandidateProfile(name="John Doe")
        assert profile.name == "John Doe"
        assert profile.experience == []

    def test_full_valid(self) -> None:
        profile = CandidateProfile(
            name="Jane Smith",
            summary="Senior engineer",
            experience=[
                ExperienceEntry(title="Senior Dev", company="Acme", dates="2020-2024"),
            ],
            education=[
                EducationEntry(degree="BSc CS", institution="MIT", year="2018"),
            ],
            skills=["Python", "Go"],
        )
        assert len(profile.experience) == 1
        assert len(profile.skills) == 2

    def test_missing_name_fails(self) -> None:
        with pytest.raises(ValidationError):
            CandidateProfile()

    def test_empty_name_fails(self) -> None:
        with pytest.raises(ValidationError):
            CandidateProfile(name="")


class TestMatchAssessmentSchema:
    def test_valid_score(self) -> None:
        m = MatchAssessment(
            score=0.85,
            reasoning="Strong technical match with relevant experience.",
            strengths=["Python", "Backend"],
            gaps=["No Kubernetes"],
        )
        assert m.score == 0.85

    def test_score_above_one_fails(self) -> None:
        with pytest.raises(ValidationError):
            MatchAssessment(score=1.5, reasoning="Too high score for this match.")

    def test_score_below_zero_fails(self) -> None:
        with pytest.raises(ValidationError):
            MatchAssessment(score=-0.1, reasoning="Negative score not allowed here.")

    def test_short_reasoning_fails(self) -> None:
        with pytest.raises(ValidationError):
            MatchAssessment(score=0.5, reasoning="too short")


class TestScreeningDecisionSchema:
    def test_valid_decisions(self) -> None:
        for decision in ("proceed_to_interview", "hold", "reject"):
            d = ScreeningDecision(
                decision=decision,
                justification="Decision based on detailed assessment of fit.",
            )
            assert d.decision == decision

    def test_invalid_decision_fails(self) -> None:
        with pytest.raises(ValidationError):
            ScreeningDecision(decision="maybe", justification="A long enough justification.")


class TestOutreachEmailSchema:
    def test_valid(self) -> None:
        email = OutreachEmail(
            subject="Opportunity at TechCo",
            body="Hi Jane, I came across your profile and was impressed by your experience...",
        )
        assert email.tone == "professional"

    def test_short_body_fails(self) -> None:
        with pytest.raises(ValidationError):
            OutreachEmail(subject="Hi", body="Too short.")

    def test_long_subject_fails(self) -> None:
        with pytest.raises(ValidationError):
            OutreachEmail(subject="x" * 200, body="A" * 100)


class TestParseAttempt:
    def test_to_dict(self) -> None:
        attempt = ParseAttempt(
            attempt=1,
            raw_response='{"name": "John"}',
            success=True,
            parsed={"name": "John"},
            input_tokens=100,
            output_tokens=20,
        )
        d = attempt.to_dict()
        assert d["attempt"] == 1
        assert d["success"] is True
        assert d["parsed"] == {"name": "John"}


class TestParseResult:
    def test_empty_result(self) -> None:
        r = ParseResult(success=False, parsed_model=None)
        d = r.to_dict()
        assert d["success"] is False
        assert d["parsed"] is None
        assert d["total_attempts"] == 0


class TestStructuredParser:
    def test_initial_prompt_includes_schema(self) -> None:
        p = StructuredParser()
        prompt = p._build_initial_prompt("Parse this CV", CandidateProfile)
        assert "Parse this CV" in prompt
        assert "schema" in prompt.lower()
        # Schema should mention the model's fields
        assert "name" in prompt
        assert "experience" in prompt

    def test_retry_prompt_includes_error(self) -> None:
        p = StructuredParser()
        prompt = p._build_retry_prompt(
            "Parse this", CandidateProfile, "Missing field 'name'"
        )
        assert "Missing field 'name'" in prompt
        assert "previous response failed" in prompt
