"""Smoke test for the refactored agent workflow.

Runs a single CV/JD pair through the full workflow and prints per-step
metrics. Useful for manual verification while staying within Voyage AI
free-tier rate limits.

Usage: python -m scripts.smoke_agent
"""

import asyncio

from src.agents.graph import compile_graph

CV = """SUMMARY
Senior Python developer with 8 years of experience building distributed systems.

EXPERIENCE
Senior Engineer at CloudScale 2020-2024. Led microservices migration. Built Kafka pipeline.

SKILLS
Python, Kubernetes, PostgreSQL, AWS, Docker, Terraform."""

JD = """JOB TITLE
Senior Backend Engineer

REQUIREMENTS
5+ years Python. Distributed systems. Cloud infrastructure.

NICE TO HAVE
Kubernetes experience."""


async def run() -> None:
    graph = compile_graph()
    state = await graph.ainvoke(
        {
            "cv_text": CV,
            "jd_text": JD,
            "step_history": [],
            "total_tokens": 0,
            "total_cost": 0.0,
        }
    )
    print()
    print("=== WORKFLOW COMPLETE ===")
    print(f"cv_document_id:  {state.get('cv_document_id')}")
    print(f"cv_was_cached:   {state.get('cv_was_cached')}")
    print(f"cv_chunk_count:  {state.get('cv_chunk_count')}")
    print(f"requirements:    {len(state.get('jd_requirements', []))}")
    print(f"retrieved:       {len(state.get('retrieved_chunks', []))}")
    print(f"match_score:     {state.get('match_score')}")
    print(f"route:           {state.get('route_decision')}")
    print(f"total tokens:    {state.get('total_tokens')}")
    print(f"total cost:      ${state.get('total_cost', 0):.4f}")
    print()
    print("Per-step trace:")
    for s in state.get("step_history", []):
        tool = s.get("tool", "?")
        node = s.get("node", "?")
        ms = s.get("duration_ms", 0)
        cost = s.get("cost_usd", 0)
        print(f"  [{tool:<14}] {node:<22} {ms:>7.0f}ms  ${cost:.4f}")


if __name__ == "__main__":
    asyncio.run(run())
