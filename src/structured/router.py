"""
FastAPI router for structured output endpoints.

Endpoints:
- GET  /structured/schemas        — List available output schemas
- POST /structured/parse          — Parse a prompt into a chosen schema
- POST /structured/demo           — Demonstrate the parse-validate-retry flow
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.structured.output_models import (
    CandidateProfile,
    JobRequirements,
    MatchAssessment,
    OutreachEmail,
    ScreeningDecision,
)
from src.structured.parser import parser

router = APIRouter()

# Registry of available schemas, keyed by name
SCHEMAS: dict[str, type[BaseModel]] = {
    "candidate_profile": CandidateProfile,
    "job_requirements": JobRequirements,
    "match_assessment": MatchAssessment,
    "screening_decision": ScreeningDecision,
    "outreach_email": OutreachEmail,
}


class ParseRequest(BaseModel):
    schema_name: str = Field(..., description="Name of the schema to parse into")
    prompt: str = Field(..., min_length=1, description="The user prompt to send to the LLM")
    max_tokens: int = Field(default=1000, ge=100, le=4000)


@router.get("/schemas")
async def list_schemas() -> dict:
    """List all available output schemas with their JSON schema."""
    return {
        "schemas": [
            {
                "name": name,
                "model_name": schema.__name__,
                "description": schema.__doc__ or "",
                "json_schema": schema.model_json_schema(),
            }
            for name, schema in SCHEMAS.items()
        ],
        "total": len(SCHEMAS),
    }


@router.get("/schemas/{name}")
async def get_schema(name: str) -> dict:
    """Get a single schema by name."""
    if name not in SCHEMAS:
        raise HTTPException(status_code=404, detail=f"Schema '{name}' not found")
    schema = SCHEMAS[name]
    return {
        "name": name,
        "model_name": schema.__name__,
        "description": schema.__doc__ or "",
        "json_schema": schema.model_json_schema(),
    }


@router.post("/parse")
async def parse_to_schema(body: ParseRequest) -> dict:
    """Run a prompt through the parse-validate-retry pipeline.

    Returns the parsed result and the full attempt history.
    """
    if body.schema_name not in SCHEMAS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown schema '{body.schema_name}'. Available: {list(SCHEMAS.keys())}",
        )

    schema = SCHEMAS[body.schema_name]
    result = parser.parse(body.prompt, schema, max_tokens=body.max_tokens)
    return result.to_dict()


@router.post("/demo")
async def demo_parse(cv_text: str) -> dict:
    """Demonstrate parsing a CV into a CandidateProfile.

    Convenience endpoint for the frontend demo. Shows the full flow:
    raw response → validation → (retry if needed) → typed result.
    """
    prompt = f"Parse this CV into structured fields.\n\nCV:\n{cv_text}"
    result = parser.parse(prompt, CandidateProfile)
    return {
        "schema": "CandidateProfile",
        "result": result.to_dict(),
    }
