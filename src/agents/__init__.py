"""
Pillar 4: Agentic Workflow (LangGraph)

Implements a recruitment workflow as a LangGraph state machine:
parse CV → parse JD → match candidate → route → screen/reject → outreach.

The key teaching concepts:
- **State machines over pipelines**: Conditional routing based on intermediate results
  is what makes a workflow "agentic." The graph makes decisions, not just executes steps.
- **Explicit state**: A TypedDict flows between nodes. Every node reads from and writes
  to this shared state. The frontend can inspect the state at each step.
- **Nodes are plain functions**: No magic. Each node is a function that takes state
  and returns updated state. This makes them independently testable.

Interview talking points:
- Why LangGraph over CrewAI? LangGraph gives explicit control over state transitions
  and conditional routing. CrewAI is higher-level but obscures decision-making. For
  teaching, transparency matters more than convenience.
- Why TypedDict for state? It's typed, inspectable, serialisable. The frontend needs
  to render state at each step — a TypedDict makes that straightforward.
- How is this different from the RAG pipeline? The RAG pipeline (Pillar 3) is linear:
  retrieve → rerank → generate. The agent workflow has conditional branches — the
  path depends on the match score. That's the agentic part.

See ADR-004 for the orchestration framework decision.
"""
