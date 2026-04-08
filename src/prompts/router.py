"""
FastAPI router for prompt management.

Endpoints:
- GET  /prompts             — List all prompts with version metadata
- GET  /prompts/{name}      — Get a specific prompt with all versions
- POST /prompts/{name}/render — Render a prompt with variables
- POST /prompts/compare     — A/B compare two versions of a prompt
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.prompts.registry import registry


router = APIRouter()


class RenderRequest(BaseModel):
    version: int | None = None
    variables: dict[str, str] = Field(default_factory=dict)


class CompareRequest(BaseModel):
    name: str
    version_a: int
    version_b: int
    variables: dict[str, str] = Field(default_factory=dict)


@router.get("")
async def list_all_prompts() -> dict:
    """List all available prompts with metadata."""
    prompts = registry.list_all()
    return {
        "prompts": [
            {
                "name": p.name,
                "description": p.description,
                "variables": p.variables,
                "version_count": len(p.versions),
                "latest_version": p.latest.version,
                "versions": [
                    {
                        "version": v.version,
                        "created": v.created,
                        "notes": v.notes,
                    }
                    for v in p.versions
                ],
            }
            for p in prompts
        ],
        "total": len(prompts),
    }


@router.get("/{name}")
async def get_prompt(name: str) -> dict:
    """Get a single prompt with all versions and templates."""
    try:
        p = registry.get(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

    return {
        "name": p.name,
        "description": p.description,
        "variables": p.variables,
        "versions": [
            {
                "version": v.version,
                "created": v.created,
                "notes": v.notes,
                "template": v.template,
            }
            for v in p.versions
        ],
        "latest_version": p.latest.version,
    }


@router.post("/{name}/render")
async def render_prompt(name: str, body: RenderRequest) -> dict:
    """Render a prompt with the given variables.

    Returns the rendered text without calling an LLM. Useful for
    previewing prompts in the frontend.
    """
    try:
        p = registry.get(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

    try:
        rendered = p.render(version=body.version, **body.variables)
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing variable: {e}. Required: {p.variables}",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "name": p.name,
        "version": body.version or p.latest.version,
        "rendered": rendered,
    }


@router.post("/compare")
async def compare_versions(body: CompareRequest) -> dict:
    """Run the same input through two prompt versions, return both outputs.

    The key A/B testing endpoint. Calls Claude twice (once per version)
    and returns both outputs side-by-side for comparison.
    """
    try:
        return registry.compare_versions(
            name=body.name,
            version_a=body.version_a,
            version_b=body.version_b,
            variables=body.variables,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Prompt '{body.name}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
