"""
RecruitmentState: the typed state that flows through the agent graph.

Every node reads from and writes to this state. It's the contract between
all nodes — changing it affects the entire workflow.

Interview talking points:
- Why a TypedDict and not a Pydantic model? LangGraph works with TypedDict
  natively. TypedDict gives us type hints for IDE support without the
  serialisation overhead of Pydantic. The state is internal to the graph;
  API-facing schemas (which do need validation) use Pydantic.
- Why store step_history? For the frontend's step-through debugger. Each
  entry records what happened at each node — the state before and after,
  timing, and any decisions made.
"""

from typing import TypedDict


class StepRecord(TypedDict, total=False):
    """A record of what happened at a single graph node."""

    node: str
    description: str
    state_before: dict
    state_after: dict
    duration_ms: float
    decision: str | None
    tool: str  # "regex", "llm", "embedding", "vector_search", "logic"
    cost_usd: float


class RetrievedChunk(TypedDict, total=False):
    """A chunk retrieved from pgvector during the matching step."""

    chunk_id: int
    document_id: int
    content: str
    similarity: float


class RecruitmentState(TypedDict, total=False):
    """State that flows through the recruitment agent graph.

    Fields are optional (total=False) because they are populated
    progressively as the graph executes.
    """

    # Inputs
    cv_text: str
    jd_text: str

    # parse_cv (regex) → persisted CV with content-hash dedup
    parsed_cv: dict
    cv_document_id: int
    cv_was_cached: bool  # True if dedup found an existing document

    # chunk_cv (regex)
    cv_chunk_count: int
    cv_chunks_were_cached: bool

    # embed_cv (Voyage AI)
    cv_embedded_count: int
    cv_embeddings_were_cached: bool

    # parse_jd (regex)
    parsed_jd: dict

    # extract_requirements (LLM)
    jd_requirements: list[str]
    requirements_consolidation_text: str  # The full requirements query for retrieval
    requirements_tokens: int

    # retrieve_evidence (vector search)
    retrieved_chunks: list[RetrievedChunk]

    # score_match (LLM, grounded in retrieved evidence)
    match_score: float
    match_reasoning: str
    strengths: list[str]
    gaps: list[str]
    match_tokens: int

    # route_candidate (logic)
    route_decision: str  # "screen", "review", "reject"

    # screen_candidate (LLM)
    screening_result: dict
    screening_tokens: int

    # reject_candidate (logic)
    rejection_reason: str

    # generate_outreach (LLM)
    outreach_email: dict
    outreach_tokens: int

    # Workflow tracking
    current_step: str
    step_history: list[StepRecord]
    total_tokens: int
    total_cost: float
