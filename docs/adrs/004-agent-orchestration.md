# ADR-004: Agent Orchestration Framework

## Status
Accepted

## Context

The workshop needs an agentic workflow (Pillar 4) that demonstrates multi-step AI orchestration. The recruitment use case involves: parsing CVs and JDs, matching candidates, routing based on match quality, screening or rejecting, and generating outreach. This needs to be a state machine with conditional branching — not a simple linear pipeline.

## Options Considered

### Option A: LangGraph
- State machine abstraction: nodes (functions), edges (transitions), conditional edges (branching)
- Built on LangChain ecosystem but usable standalone
- TypedDict-based state that flows between nodes
- **Pro**: Explicit state management, visual graph structure, conditional routing, built-in persistence
- **Con**: LangChain ecosystem dependency, learning curve for the graph DSL

### Option B: CrewAI
- Agent-based: define agents with roles and tools, they collaborate
- **Pro**: Higher-level abstraction, good for "team of agents" scenarios
- **Con**: Less control over execution flow, harder to visualise state transitions, opaque decision-making

### Option C: AutoGen / AG2
- Multi-agent conversation framework
- **Pro**: Good for chat-based agent interactions
- **Con**: Conversation-oriented, not workflow-oriented. The recruitment pipeline is a workflow, not a conversation

### Option D: Custom (plain Python)
- Build a state machine from scratch using functions and dicts
- **Pro**: No framework dependency, full control
- **Con**: Reinventing the wheel. No built-in graph visualisation, persistence, or streaming

## Decision

**LangGraph** (Option A), with a refined design that emerged from the implementation:

1. **Agents orchestrate tools, not just LLM calls.** The first iteration of this pillar made every node an LLM call (`parse_cv` → LLM, `parse_jd` → LLM, `match_candidate` → LLM, etc.). That conflated "agent" with "LLM pipeline." The refactored design has the agent pick the right tool for each step: regex for structural extraction, vector search for evidence retrieval, LLM for semantic reasoning, plain logic for routing decisions. Five distinct tools are used across 11 nodes.

2. **Nodes are async and the graph runs via `ainvoke`.** Several nodes touch the database (chunking, embedding, retrieval); making the whole graph async lets these operations cooperate properly with FastAPI's event loop.

3. **CV ingestion is part of the workflow with content-hash dedup.** When the agent receives a CV it parses, chunks, embeds, and persists it via a SHA256 content hash. Re-running the agent on the same CV reuses the existing document, chunks, and embeddings — zero cost on the second run.

4. **Match scoring is grounded in retrieved evidence.** The earlier design passed both parsed structures (CV + JD) directly to the LLM for scoring. The current design embeds the JD requirements, retrieves the most relevant CV chunks via pgvector, and feeds *only those chunks* to the scoring LLM. This makes the agent demonstrably use Pillars 1–3 of the workshop and produces sharper, more evidence-grounded scores.

## Rationale

### Why LangGraph (still true)
- **State machine maps perfectly to the recruitment workflow**: parse → chunk → embed → extract requirements → retrieve evidence → score → route → screen/reject → outreach is naturally a directed graph with conditional edges.
- **TypedDict state is inspectable**: The frontend can show the state at each node — what went in, what came out, which branch was taken, which tool ran.
- **Conditional routing is the agentic concept**: The graph makes decisions (route based on match score), which is what distinguishes an agentic workflow from a pipeline.
- **Graph structure is serialisable**: We expose the graph topology via API for the frontend's React Flow visualisation, including a `tool` hint per node so the frontend can colour-code by tool type.

### Why "agent orchestrates tools" rather than "agent calls LLM at every step"
- **Cost.** Replacing two LLM calls (parse_cv, parse_jd) with regex saved ~$0.01 and ~1.4s per workflow run with zero quality loss. CVs and JDs are highly structured documents — regex handles the structure for free.
- **Latency.** The original 5-LLM-call workflow took ~25-30s end-to-end. The refactored 3-LLM-call workflow takes ~12-16s.
- **Teaching value.** The contrast between "LLM for everything" and "the right tool for each job" is the most important lesson Pillar 4 can teach. An engineer who walks away thinking "agents are just LLM pipelines" has missed the point.
- **Honesty.** Production agent systems do not pay for an LLM call to extract a heading — they use string operations. Modelling the workshop on what production looks like prevents the demo from teaching the wrong defaults.

### Why content-hash dedup
- The same CV will be evaluated against multiple JDs over time. Re-chunking and re-embedding it on every run is pure waste.
- Hash check is ~1ms; chunking + embedding is ~300ms and a fraction of a cent. The dedup pays for itself on the second run.
- Persisting to the database (rather than caching in memory) means the dedup survives server restarts and shows up on the documents page — the user can see the agent's accumulated CV corpus.

### Why match scoring uses retrieved evidence
- Without retrieval, scoring sees the *whole* CV — including sections irrelevant to the JD. The LLM has to do its own filtering, and the score reflects an averaged impression rather than focused matching.
- With retrieval, scoring sees only the top-k chunks pgvector identifies as relevant to the JD requirements. This is sharper, cheaper (less context), and demonstrably uses the retrieval pipeline built in Pillars 1–3.
- It also closes a teaching gap from the first iteration: the original agent didn't actually use the RAG pipeline that lived in the same codebase, which made Pillar 3 feel disconnected.

## Consequences

- Adds LangGraph and langchain-core as dependencies.
- The state schema (`RecruitmentState` TypedDict) must accommodate every field any node might read or write — see `src/agents/state.py`. This is the contract between all nodes.
- Nodes are `async def`, so the graph must be invoked via `await graph.ainvoke(...)` rather than `.invoke()`. The eval runner (`src/evaluation/router.py`) hit this constraint and was updated accordingly.
- The `route_candidate` thresholds (0.65 / 0.30) are deliberately aligned with the golden dataset thresholds in `src/evaluation/runner.py` so eval cases that score in their expected range produce the expected outcome label. Changing one without the other creates a dead zone — see ADR-006.
- Per-step cost is tracked accurately by each node (not estimated from total tokens), so the workflow's `total_cost` is the literal sum of each step's contribution.

## Graph Design

```
                ┌─────────────────────────────────────────────────────────┐
                │  CV ingestion lane                                       │
                │  parse_cv (regex) → chunk_cv (regex) → embed (Voyage)    │
                └─────────────────────────────────────────────────────────┘
                                              │
                ┌─────────────────────────────┴───────────────────────────┐
                │  JD lane                                                 │
                │  parse_jd (regex) → extract_requirements (LLM)           │
                └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                          retrieve_evidence (vector_search via pgvector)
                                              │
                                              ▼
                                  score_match (LLM, grounded)
                                              │
                                              ▼
                                  route_candidate (logic)
                                              │
                                ┌─────────────┼─────────────┐
                                ▼                           ▼
                          score ≥ 0.30                  score < 0.30
                                │                           │
                          screen_candidate              reject_candidate
                                │                           │
                                ▼                           ▼
                          generate_outreach              [END]
                                │
                                ▼
                              [END]
```

11 nodes, 5 distinct tools (regex, embedding, vector_search, llm, logic). Each node reads from and writes to `RecruitmentState`. The state at every step is serialised and returned to the frontend for the step-through visualiser, including the `tool` and `cost_usd` for each step so users can see which tool was used and what it cost.
