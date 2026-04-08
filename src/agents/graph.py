"""
LangGraph state machine definition for the recruitment workflow.

Composes node functions (from nodes.py) into a directed graph with
conditional routing.

The graph mixes tools — regex parsing, vector search, and LLM calls — picking
the right tool for each step. The teaching point is that an "agent" is a
workflow orchestrator, not a wrapper around an LLM.

Topology:

    parse_cv (regex)
        ↓
    chunk_cv (regex)
        ↓
    embed_cv_chunks (Voyage AI)
        ↓
    parse_jd (regex)
        ↓
    extract_requirements (LLM — semantic consolidation)
        ↓
    retrieve_evidence (vector search via pgvector)
        ↓
    score_match (LLM — grounded in retrieved evidence)
        ↓
    route_candidate (logic)
        ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
    screen_candidate                reject_candidate
    ↓                               ↓
    generate_outreach               END
    ↓
    END

Cost reduction vs the previous design: 5 LLM calls → 3 LLM calls (parse_cv
and parse_jd are now regex). Latency drops by ~30%. Match scoring is grounded
in retrieved evidence rather than the entire CV/JD.

See ADR-004 for the orchestration framework decision.
"""

from langgraph.graph import END, StateGraph

from src.agents.nodes import (
    chunk_cv,
    embed_cv_chunks,
    extract_requirements,
    generate_outreach,
    parse_cv,
    parse_jd,
    reject_candidate,
    retrieve_evidence,
    route_candidate,
    score_match,
    screen_candidate,
)
from src.agents.state import RecruitmentState


def _routing_function(state: RecruitmentState) -> str:
    """Conditional routing based on match score.

    Returns the name of the next node to execute. This is the decision
    point in the graph — the agent makes a runtime branching decision
    based on the match score.
    """
    decision = state.get("route_decision", "reject")
    if decision in ("screen", "review"):
        return "screen_candidate"
    return "reject_candidate"


def build_graph() -> StateGraph:
    """Build the recruitment workflow graph."""
    graph = StateGraph(RecruitmentState)

    # Nodes
    graph.add_node("parse_cv", parse_cv)
    graph.add_node("chunk_cv", chunk_cv)
    graph.add_node("embed_cv_chunks", embed_cv_chunks)
    graph.add_node("parse_jd", parse_jd)
    graph.add_node("extract_requirements", extract_requirements)
    graph.add_node("retrieve_evidence", retrieve_evidence)
    graph.add_node("score_match", score_match)
    graph.add_node("route_candidate", route_candidate)
    graph.add_node("screen_candidate", screen_candidate)
    graph.add_node("reject_candidate", reject_candidate)
    graph.add_node("generate_outreach", generate_outreach)

    # Linear edges: ingestion → matching pipeline
    graph.set_entry_point("parse_cv")
    graph.add_edge("parse_cv", "chunk_cv")
    graph.add_edge("chunk_cv", "embed_cv_chunks")
    graph.add_edge("embed_cv_chunks", "parse_jd")
    graph.add_edge("parse_jd", "extract_requirements")
    graph.add_edge("extract_requirements", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", "score_match")
    graph.add_edge("score_match", "route_candidate")

    # Conditional branching: route → screen or reject
    graph.add_conditional_edges(
        "route_candidate",
        _routing_function,
        {
            "screen_candidate": "screen_candidate",
            "reject_candidate": "reject_candidate",
        },
    )

    # After screening → outreach
    graph.add_edge("screen_candidate", "generate_outreach")

    # Terminal edges
    graph.add_edge("generate_outreach", END)
    graph.add_edge("reject_candidate", END)

    return graph


def compile_graph():
    """Build and compile the graph into a runnable."""
    graph = build_graph()
    return graph.compile()


def get_graph_structure() -> dict:
    """Return the graph structure for frontend visualisation.

    Includes a `tool` hint per node so the frontend can colour-code by tool
    type (regex, embedding, vector_search, llm, logic).
    """
    return {
        "nodes": [
            {"id": "parse_cv", "label": "Parse CV", "type": "process", "tool": "regex"},
            {"id": "chunk_cv", "label": "Chunk CV", "type": "process", "tool": "regex"},
            {
                "id": "embed_cv_chunks",
                "label": "Embed Chunks",
                "type": "process",
                "tool": "embedding",
            },
            {"id": "parse_jd", "label": "Parse JD", "type": "process", "tool": "regex"},
            {
                "id": "extract_requirements",
                "label": "Extract Requirements",
                "type": "process",
                "tool": "llm",
            },
            {
                "id": "retrieve_evidence",
                "label": "Retrieve Evidence",
                "type": "process",
                "tool": "vector_search",
            },
            {"id": "score_match", "label": "Score Match", "type": "process", "tool": "llm"},
            {"id": "route_candidate", "label": "Route", "type": "decision", "tool": "logic"},
            {
                "id": "screen_candidate",
                "label": "Screen Candidate",
                "type": "process",
                "tool": "llm",
            },
            {"id": "reject_candidate", "label": "Reject", "type": "terminal", "tool": "logic"},
            {
                "id": "generate_outreach",
                "label": "Generate Outreach",
                "type": "process",
                "tool": "llm",
            },
        ],
        "edges": [
            {"source": "parse_cv", "target": "chunk_cv", "label": ""},
            {"source": "chunk_cv", "target": "embed_cv_chunks", "label": ""},
            {"source": "embed_cv_chunks", "target": "parse_jd", "label": ""},
            {"source": "parse_jd", "target": "extract_requirements", "label": ""},
            {"source": "extract_requirements", "target": "retrieve_evidence", "label": ""},
            {"source": "retrieve_evidence", "target": "score_match", "label": ""},
            {"source": "score_match", "target": "route_candidate", "label": ""},
            {"source": "route_candidate", "target": "screen_candidate", "label": "score >= 0.4"},
            {"source": "route_candidate", "target": "reject_candidate", "label": "score < 0.4"},
            {"source": "screen_candidate", "target": "generate_outreach", "label": ""},
            {"source": "generate_outreach", "target": "__end__", "label": ""},
            {"source": "reject_candidate", "target": "__end__", "label": ""},
        ],
    }
