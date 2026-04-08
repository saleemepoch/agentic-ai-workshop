"""
Pydantic schemas for the agent workflow API.
"""

from pydantic import BaseModel, Field


class WorkflowRequest(BaseModel):
    """Request to run the recruitment agent workflow."""

    cv_text: str = Field(..., min_length=1, description="Full CV text")
    jd_text: str = Field(..., min_length=1, description="Full job description text")


class WorkflowStepResult(BaseModel):
    """Result from a single workflow step."""

    node: str
    description: str
    duration_ms: float
    decision: str | None = None
    tool: str | None = None  # "regex", "llm", "embedding", "vector_search", "logic"
    cost_usd: float | None = None


class RetrievedChunkResponse(BaseModel):
    """A chunk retrieved from pgvector during the matching step."""

    chunk_id: int
    document_id: int
    content: str
    similarity: float


class WorkflowResponse(BaseModel):
    """Full workflow execution response."""

    # Parsing results (regex)
    parsed_cv: dict
    parsed_jd: dict

    # CV ingestion (regex + embedding, with content-hash dedup)
    cv_document_id: int | None = None
    cv_was_cached: bool = False

    # JD requirements (LLM consolidation across sections)
    jd_requirements: list[str] = []

    # Retrieved evidence (vector search via pgvector)
    retrieved_chunks: list[RetrievedChunkResponse] = []

    # Match results (LLM, grounded in retrieved evidence)
    match_score: float
    match_reasoning: str
    strengths: list[str]
    gaps: list[str]

    # Routing (logic)
    route_decision: str

    # Outcome (one of these will be populated)
    screening_result: dict | None = None
    rejection_reason: str | None = None
    outreach_email: dict | None = None

    # Execution trace
    steps: list[WorkflowStepResult]
    total_tokens: int
    total_cost: float


class GraphStructureResponse(BaseModel):
    """Graph topology for frontend visualisation."""

    nodes: list[dict]
    edges: list[dict]
