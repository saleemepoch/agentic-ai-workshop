"""
FastAPI router for the agent workflow.

Endpoints:
- POST /agents/run   — Run the full recruitment workflow
- GET  /agents/graph — Get graph structure for visualisation
"""

from fastapi import APIRouter

from src.agents.graph import compile_graph, get_graph_structure
from src.agents.schemas import (
    GraphStructureResponse,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStepResult,
)

router = APIRouter()

# Compile the graph once at module level
_compiled_graph = compile_graph()


@router.post("/run", response_model=WorkflowResponse)
async def run_workflow(body: WorkflowRequest) -> WorkflowResponse:
    """Run the full recruitment agent workflow.

    Executes the LangGraph state machine: parse CV → parse JD → match →
    route → screen/reject → outreach. Returns the full execution trace
    with state at each step.
    """
    # Initial state
    initial_state = {
        "cv_text": body.cv_text,
        "jd_text": body.jd_text,
        "step_history": [],
        "total_tokens": 0,
        "total_cost": 0.0,
    }

    # Run the graph asynchronously — nodes touch the database and external APIs
    final_state = await _compiled_graph.ainvoke(initial_state)

    total_tokens = final_state.get("total_tokens", 0)
    # Per-step costs are now tracked accurately by each node, so we sum them
    # rather than averaging over total tokens.
    total_cost = sum(
        float(step.get("cost_usd", 0.0))
        for step in final_state.get("step_history", [])
    )

    steps = [
        WorkflowStepResult(
            node=step.get("node", ""),
            description=step.get("description", ""),
            duration_ms=step.get("duration_ms", 0),
            decision=step.get("decision"),
            tool=step.get("tool"),
            cost_usd=step.get("cost_usd"),
        )
        for step in final_state.get("step_history", [])
    ]

    return WorkflowResponse(
        parsed_cv=final_state.get("parsed_cv", {}),
        parsed_jd=final_state.get("parsed_jd", {}),
        match_score=final_state.get("match_score", 0),
        match_reasoning=final_state.get("match_reasoning", ""),
        strengths=final_state.get("strengths", []),
        gaps=final_state.get("gaps", []),
        route_decision=final_state.get("route_decision", ""),
        screening_result=final_state.get("screening_result"),
        rejection_reason=final_state.get("rejection_reason"),
        outreach_email=final_state.get("outreach_email"),
        steps=steps,
        total_tokens=total_tokens,
        total_cost=round(total_cost, 6),
        cv_document_id=final_state.get("cv_document_id"),
        cv_was_cached=final_state.get("cv_was_cached", False),
        jd_requirements=final_state.get("jd_requirements", []),
        retrieved_chunks=final_state.get("retrieved_chunks", []),
    )


@router.get("/graph", response_model=GraphStructureResponse)
async def get_graph() -> GraphStructureResponse:
    """Get the graph structure for frontend visualisation.

    Returns nodes and edges in a format compatible with React Flow.
    """
    structure = get_graph_structure()
    return GraphStructureResponse(
        nodes=structure["nodes"],
        edges=structure["edges"],
    )
