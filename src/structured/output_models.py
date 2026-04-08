"""
Pydantic schemas for LLM structured outputs.

These models define what we expect the LLM to return. The same models
are used throughout the pipeline — agent nodes, RAG generation, evaluation.

Interview talking points:
- Why use Pydantic instead of plain dicts? Type safety, automatic validation,
  clear schemas. When the LLM returns a malformed response, Pydantic gives
  you a precise error message that you can feed back into a retry.
- Why are field constraints (min/max length) here and not in the prompt?
  Because constraints in code are enforceable — you can validate them
  reliably. Constraints in prompts are suggestions — the LLM might ignore
  them. Use both: ask in the prompt, enforce in the code.
"""

from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    """A single role in a candidate's work history."""

    title: str = Field(..., min_length=1, description="Job title")
    company: str = Field(..., min_length=1, description="Company name")
    dates: str = Field(default="", description="Employment dates (e.g., '2020-2024')")
    highlights: list[str] = Field(
        default_factory=list,
        description="Key achievements or responsibilities",
    )


class EducationEntry(BaseModel):
    """A single education credential."""

    degree: str = Field(..., min_length=1)
    institution: str = Field(..., min_length=1)
    year: str = Field(default="")


class CandidateProfile(BaseModel):
    """A parsed CV with structured fields."""

    name: str = Field(..., min_length=1, description="Candidate's full name")
    summary: str = Field(default="", description="1-2 sentence professional summary")
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills")
    certifications: list[str] = Field(default_factory=list)


class JobRequirements(BaseModel):
    """A parsed job description with structured requirements."""

    title: str = Field(..., min_length=1)
    company: str = Field(default="")
    summary: str = Field(default="", description="1-2 sentence company/role summary")
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list, description="Must-have requirements")
    nice_to_haves: list[str] = Field(default_factory=list)


class MatchAssessment(BaseModel):
    """A scored match between a candidate and job."""

    score: float = Field(..., ge=0.0, le=1.0, description="Match score from 0.0 to 1.0")
    reasoning: str = Field(..., min_length=10, description="2-3 sentences explaining the score")
    strengths: list[str] = Field(default_factory=list, description="Specific matching points")
    gaps: list[str] = Field(default_factory=list, description="Specific missing requirements")


class ScreeningDecision(BaseModel):
    """A screening decision for a candidate."""

    decision: str = Field(
        ...,
        pattern="^(proceed_to_interview|hold|reject)$",
        description="One of: proceed_to_interview, hold, reject",
    )
    justification: str = Field(..., min_length=10)
    screening_questions: list[str] = Field(
        default_factory=list,
        description="3-5 questions to ask in interview",
    )


class OutreachEmail(BaseModel):
    """A personalised outreach email draft."""

    subject: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=50, description="Professional email body")
    tone: str = Field(default="professional", description="Tone descriptor")
