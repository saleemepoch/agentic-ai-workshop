# CLAUDE.md — Agentic AI Workshop

## Project Purpose

This is a **teaching-focused demonstration platform** called **Agentic AI Workshop**. It serves two purposes:

1. **Portfolio piece to demonstrate working knowledge and expertise**: Every file, commit, and decision must demonstrate senior-level understanding of AI engineering — not just that things work, but *why* they're built this way.
2. **Team training tool**: The platform teaches a team about agentic AI, RAG systems, and production AI engineering. The frontend is interactive documentation — users can experiment with different strategies, see how each component works, and understand the trade-offs behind every decision.

**The north star**: Someone browsing this repo should think "this person could lead our AI engineering team." Someone using the frontend should walk away understanding agentic AI well enough to make architectural decisions.

## Working Style

- **Architecture before code**: Discuss trade-offs and write ADRs before implementing. Never jump straight to code for significant decisions.
- **Teach as you build**: Every module should be explainable at three levels — engineer, PM, executive. The code teaches; the UI demonstrates.
- **Depth over breadth**: Go deep on each topic. Specifics matter — tokenisation in chunking, structured debugging approaches, golden datasets in evaluation.
- **Well-annotated code**: Docstrings explain the *why*, not the *what*. Comments should teach — "we use cosine similarity here because..." not "compute similarity". Interview talking points are embedded in module-level docstrings.
- **Clean git history**: Each commit should tell a story. Atomic commits with clear messages. The git log itself is a teaching artefact.
- **Concise output**: Don't pad responses. Lead with the answer or action.

---

## The 10 Pillars

The platform is organised into 10 pillars. Each pillar covers a core AI engineering concept, has working backend code, and is demonstrated interactively in the frontend.

### Pillar 1: Document Processing & Chunking
**What it teaches**: How to prepare unstructured text for AI pipelines.
- Semantic chunking (section-aware, not naive token splitting)
- Side-by-side comparison: naive fixed-size vs semantic chunking
- Token-aware splitting with configurable overlap
- Show how chunk quality directly affects retrieval quality
- **Frontend**: Upload a CV or JD, see it chunked in real-time. Toggle between chunking strategies. See token counts per chunk. Visual diff of what each strategy produces.

### Pillar 2: Embeddings & Retrieval
**What it teaches**: How text becomes vectors and how similarity search works.
- Embedding pipeline using Voyage AI
- pgvector storage and similarity search
- Distance metrics comparison: cosine vs euclidean vs dot product
- Dimensionality and what it means for quality vs cost
- **Frontend**: Embed text and visualise similarity scores. Toggle between distance metrics and watch rankings change. Show why cosine similarity is the default choice for normalised embeddings and when you'd pick something else.

### Pillar 3: RAG Pipeline (End-to-End)
**What it teaches**: The full retrieval-augmented generation flow, not as a black box.
- Query → embed → retrieve → rerank → generate, each step visible
- Context window management and token budgeting
- Reranking: why retrieval alone isn't enough
- Prompt construction: how retrieved chunks become LLM context
- **Frontend**: Paste a JD, retrieve matching CVs. The UI shows every pipeline stage: what was retrieved, how it was ranked, what prompt was built, what the LLM generated. Each stage expandable with explanation of what's happening and why.

### Pillar 4: Agentic Workflow (LangGraph)
**What it teaches**: How to orchestrate multi-step AI workflows as state machines.
- LangGraph state machine: nodes, edges, conditional routing
- Recruitment workflow: parse → match → route → screen/reject → outreach
- State schema: explicitly typed state flowing between nodes
- Tool use: agents calling tools (embedding, retrieval, LLM)
- Conditional branching: route based on match score
- **Frontend**: Visualise the agent graph. Step through execution node by node. Show the state at each step — what went in, what came out, which branch was taken and why. Animate the flow for a given CV/JD pair.

### Pillar 5: Observability & Cost Management (Langfuse)
**What it teaches**: How to monitor, debug, and control costs in production AI systems.
- Langfuse integration: traces, spans, nested observation hierarchy
- Per-request cost tracking: token counts, model pricing, total cost
- Latency breakdown per pipeline stage
- Prompt versioning and management
- **Frontend**: Show Langfuse traces inline — click a request, see the full trace tree. Cost breakdown per request and per stage. Latency waterfall chart. Token usage visualisation. Explain: "this is how you answer 'how much does a single match cost?'"

### Pillar 6: Evaluation Pipeline
**What it teaches**: How to measure and maintain AI system quality over time.
- Golden dataset: hand-labelled CV/JD pairs with expected outcomes
- Retrieval metrics: precision@k, recall@k, MRR
- Generation quality: LLM-as-judge scoring (faithfulness, relevance)
- Regression detection: track metrics over time, catch degradation
- **Frontend**: Run the evaluation suite from the UI. Show metrics dashboard: which test cases pass/fail, scores over time, drill into failures. Explain what each metric measures and why it matters.

### Pillar 7: Guardrails & Safety
**What it teaches**: How to detect and prevent AI failures in production.
- Layered guardrails approach (proportional cost to risk):
  - Layer 1 (sync, zero-cost): PII detection, budget enforcement, timeout, output validation
  - Layer 2 (async, low-cost): retrieval relevance scoring, context utilisation check
  - Layer 3 (LLM-as-judge, sampled): faithfulness check, completeness check
- Failure taxonomy: hallucination, PII leakage, retrieval failure, bias, context poisoning, cost blowout
- **Frontend**: Interactive demo of each guardrail layer. Feed it examples that should trigger each guardrail. Show: "here's a response that passed all checks" vs "here's one that got flagged for hallucination — here's why." Toggle guardrails on/off to see the difference.

### Pillar 8: Prompt Engineering & Management
**What it teaches**: How to treat prompts as versioned, testable artefacts — not ad-hoc strings.
- Prompt versioning via Langfuse prompt management
- Prompt templates with variable injection
- A/B comparison: run the same query with different prompt versions, compare outputs side-by-side
- Prompt design patterns: system prompts, few-shot examples, chain-of-thought, structured output instructions
- **Frontend**: Prompt editor with version history. Side-by-side output comparison for different prompt versions. Show how a small prompt change affects output quality. Explain each prompt design pattern with live examples.

### Pillar 9: Structured Outputs & Validation
**What it teaches**: How to get reliable, typed data from LLMs — not just free text.
- Pydantic models defining expected LLM output schemas
- Validation pipeline: LLM response → parse → validate → retry on failure
- Handling malformed output: retry with error feedback to the LLM
- When to use structured outputs vs free text
- **Frontend**: Show the Pydantic schema, send a query, see the raw LLM response and the validated/parsed output side by side. Demonstrate a failure case: malformed response → validation error → retry → success. Explain the retry strategy.

### Pillar 10: Error Handling & Fallbacks
**What it teaches**: How to build resilient AI systems that degrade gracefully.
- Retry strategies: exponential backoff, retry with modified prompt
- Fallback chains: if primary model fails, fall back to secondary
- Circuit breaker pattern: stop calling a failing service
- Graceful degradation: return partial results rather than nothing
- Timeout management: per-step and per-request budgets
- **Frontend**: Simulate failure scenarios from the UI. Show what happens when: the LLM times out, the embedding service is down, the LLM returns garbage. Demonstrate the fallback chain in action. Show circuit breaker state.

---

## Tech Stack

### Backend
- **Language**: Python 3.12+
- **API**: FastAPI
- **Database**: PostgreSQL + pgvector (vector similarity search)
- **LLM**: Claude (Anthropic API) via the `anthropic` Python SDK
- **Embeddings**: Voyage AI (`voyageai` SDK)
- **Agent Orchestration**: LangGraph
- **Observability**: Langfuse (tracing, evaluation, prompt management, cost tracking)
- **Validation**: Pydantic v2 for all data structures and LLM output schemas
- **Testing**: pytest (unit + integration + evaluation)

### Frontend
- **Framework**: Next.js (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State Management**: React Server Components by default, client components only for interactivity
- **Data Fetching**: Server components fetch from FastAPI backend; client components use fetch/SWR where needed
- **Charts/Visualisation**: A lightweight charting library (e.g., Recharts) for metrics dashboards; a graph visualisation library (e.g., React Flow) for agent workflow diagrams

### Infrastructure
- **Containerisation**: Docker + Docker Compose (Postgres, API, Web)
- **CI/CD**: GitHub Actions
- **Environment**: `.env` for secrets (never committed), `.env.example` as template

---

## Project Structure

```
agentic-ai-workshop/
├── CLAUDE.md                    # This file
├── README.md                    # Project overview, setup guide, pillar index
├── docs/
│   ├── adrs/                    # Architecture Decision Records
│   │   ├── 001-application-structure.md
│   │   ├── 002-api-framework.md
│   │   ├── 003-vector-storage.md
│   │   ├── 004-embedding-model.md
│   │   ├── 005-agent-orchestration.md
│   │   ├── 006-observability.md
│   │   ├── 007-guardrails.md
│   │   ├── 008-testing-strategy.md
│   │   ├── 009-prompt-management.md
│   │   ├── 010-structured-outputs.md
│   │   ├── 011-error-handling.md
│   │   └── 012-frontend.md
│   └── architecture.md          # High-level system architecture diagram + explanation
├── src/                         # Python backend
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, lifespan, router mounting
│   ├── config.py                # Pydantic Settings, env var management
│   ├── database.py              # SQLAlchemy async engine, session factory
│   ├── documents/               # Pillar 1: Document Processing & Chunking
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy models (Document, Chunk with pgvector)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── chunker.py           # Semantic chunker (section-aware, token-aware)
│   │   ├── naive_chunker.py     # Naive fixed-size chunker (for comparison)
│   │   ├── service.py           # CRUD operations
│   │   └── router.py            # FastAPI endpoints
│   ├── matching/                # Pillar 2 & 3: Embeddings, Retrieval, RAG
│   │   ├── __init__.py
│   │   ├── embedder.py          # Voyage AI embedding client
│   │   ├── retriever.py         # pgvector similarity search with distance metric toggle
│   │   ├── reranker.py          # Cross-encoder or LLM-based reranking
│   │   ├── rag_pipeline.py      # End-to-end RAG: retrieve → rerank → generate
│   │   ├── schemas.py           # Pydantic schemas for match results
│   │   ├── service.py           # Matching business logic
│   │   └── router.py            # FastAPI endpoints
│   ├── agents/                  # Pillar 4: Agentic Workflow
│   │   ├── __init__.py
│   │   ├── state.py             # RecruitmentState TypedDict
│   │   ├── nodes.py             # Node functions (parse, match, screen, outreach)
│   │   ├── graph.py             # LangGraph StateGraph definition
│   │   ├── tools.py             # Tools available to agents
│   │   ├── schemas.py           # Agent input/output schemas
│   │   └── router.py            # FastAPI endpoints (run workflow, get status)
│   ├── observability/           # Pillar 5: Observability & Cost
│   │   ├── __init__.py
│   │   ├── tracing.py           # Langfuse client, @observe decorator setup
│   │   ├── cost.py              # Cost calculation and budget enforcement
│   │   ├── prompts.py           # Langfuse prompt management (versioning, serving)
│   │   └── router.py            # Endpoints to fetch traces, costs, metrics
│   ├── evaluation/              # Pillar 6: Evaluation Pipeline
│   │   ├── __init__.py
│   │   ├── golden_dataset.py    # Hand-labelled CV/JD pairs with expected outcomes
│   │   ├── metrics.py           # Retrieval metrics (precision@k, recall@k, MRR)
│   │   ├── runner.py            # Evaluation runner — scores pipeline against golden set
│   │   ├── llm_judge.py         # LLM-as-judge scoring (faithfulness, relevance)
│   │   └── router.py            # Endpoints to trigger eval runs, fetch results
│   ├── guardrails/              # Pillar 7: Guardrails & Safety
│   │   ├── __init__.py
│   │   ├── pii.py               # PII detection (regex + lightweight NER)
│   │   ├── faithfulness.py      # Faithfulness scoring (LLM-as-judge)
│   │   ├── budget.py            # Per-request token/cost budget enforcement
│   │   ├── validator.py         # Orchestrates all guardrail layers
│   │   └── router.py            # Endpoints to test guardrails interactively
│   ├── prompts/                 # Pillar 8: Prompt Engineering & Management
│   │   ├── __init__.py
│   │   ├── templates.py         # Prompt templates with variable injection
│   │   ├── registry.py          # Prompt versioning and A/B management via Langfuse
│   │   └── router.py            # Endpoints to list/compare/test prompts
│   ├── structured/              # Pillar 9: Structured Outputs & Validation
│   │   ├── __init__.py
│   │   ├── output_models.py     # Pydantic models for expected LLM output schemas
│   │   ├── parser.py            # Parse + validate + retry pipeline
│   │   └── router.py            # Endpoints to demo structured output flow
│   └── resilience/              # Pillar 10: Error Handling & Fallbacks
│       ├── __init__.py
│       ├── retry.py             # Retry strategies (exponential backoff, modified prompt)
│       ├── fallback.py          # Fallback chains (primary → secondary model)
│       ├── circuit_breaker.py   # Circuit breaker pattern
│       └── router.py            # Endpoints to simulate failure scenarios
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures (db session, test client, mock LLM)
│   ├── unit/                    # Fast, isolated tests — mirrors src/ structure
│   │   ├── documents/
│   │   ├── matching/
│   │   ├── agents/
│   │   ├── guardrails/
│   │   ├── structured/
│   │   └── resilience/
│   ├── integration/             # Tests with real DB, real API calls
│   └── eval/                    # Evaluation pipeline tests (golden dataset)
├── scripts/
│   ├── seed_data.py             # Seed database with sample CVs and JDs
│   ├── run_eval.py              # CLI to run evaluation pipeline
│   └── demo.py                  # Quick demo script for presentation
├── web/                         # Next.js frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   │   ├── layout.tsx       # Root layout (nav, sidebar with pillar index)
│   │   │   ├── page.tsx         # Home — workshop overview, pillar cards
│   │   │   ├── chunking/        # Pillar 1: interactive chunking demo
│   │   │   │   └── page.tsx
│   │   │   ├── embeddings/      # Pillar 2: embedding & retrieval demo
│   │   │   │   └── page.tsx
│   │   │   ├── rag/             # Pillar 3: end-to-end RAG pipeline demo
│   │   │   │   └── page.tsx
│   │   │   ├── agents/          # Pillar 4: agent workflow visualisation
│   │   │   │   └── page.tsx
│   │   │   ├── observability/   # Pillar 5: traces, cost, latency
│   │   │   │   └── page.tsx
│   │   │   ├── evaluation/      # Pillar 6: eval metrics dashboard
│   │   │   │   └── page.tsx
│   │   │   ├── guardrails/      # Pillar 7: guardrail testing demo
│   │   │   │   └── page.tsx
│   │   │   ├── prompts/         # Pillar 8: prompt management & A/B
│   │   │   │   └── page.tsx
│   │   │   ├── structured/      # Pillar 9: structured output demo
│   │   │   │   └── page.tsx
│   │   │   └── resilience/      # Pillar 10: error handling demo
│   │   │       └── page.tsx
│   │   ├── components/          # Shared UI components
│   │   │   ├── layout/          # Nav, sidebar, footer
│   │   │   ├── ui/              # Buttons, cards, modals, code blocks
│   │   │   ├── pipeline/        # Pipeline step visualiser (reused across pillars)
│   │   │   ├── graph/           # Agent graph visualiser (React Flow)
│   │   │   └── charts/          # Metrics charts (Recharts)
│   │   └── lib/
│   │       ├── api.ts           # Typed API client for FastAPI backend
│   │       └── types.ts         # Shared TypeScript types (mirroring Pydantic schemas)
│   └── public/
│       └── ...                  # Static assets
├── docker-compose.yml           # postgres + api + web
├── Dockerfile                   # Python API
├── Dockerfile.web               # Next.js frontend
├── pyproject.toml               # Python dependencies and config
├── .env.example                 # Template for environment variables
└── .github/
    └── workflows/
        └── ci.yml               # Lint, test, build, eval quality gate
```

---

## Conventions

### Backend (Python)
- **Pydantic everywhere**: All request/response schemas, all LLM output schemas, all config. If data crosses a boundary, it goes through a Pydantic model.
- **Type hints** on all function signatures. No `Any` unless truly unavoidable.
- **Docstrings teach**: Module-level docstrings include "Interview talking points" sections explaining the *why* behind design decisions. Function docstrings only where intent isn't obvious from name + types.
- **Tests mirror source**: `src/documents/chunker.py` → `tests/unit/documents/test_chunker.py`
- **All LLM calls** go through a thin client wrapper for testability and observability. Never call the Anthropic API directly from business logic.
- **All LLM calls** are decorated with `@observe` for Langfuse tracing. No untraced calls.
- **Router → Service → Model** pattern: routers handle HTTP, services handle business logic, models handle persistence. Routers never touch the database directly.

### Frontend (Next.js / TypeScript)
- **App Router** with React Server Components by default. Client components (`"use client"`) only when interactivity (event handlers, hooks, state) is needed.
- **TypeScript strict mode**. No `any` types.
- **Tailwind CSS** for all styling. No CSS modules or styled-components.
- **API client**: All backend calls go through `web/src/lib/api.ts` — typed functions matching the FastAPI endpoints.
- **Each pillar page** follows a consistent layout:
  1. **Title + explanation**: What this pillar teaches and why it matters (2-3 sentences)
  2. **Interactive demo**: The hands-on component where users experiment
  3. **Behind the scenes**: Expandable section showing what the backend is doing, with code snippets and architectural notes
  4. **Key trade-offs**: Cards highlighting the decisions made and alternatives considered
- **Components are colocated** with their pages unless reused across multiple pages.

### ADRs
- Format: `docs/adrs/NNN-title.md` with sections: Status, Context, Options Considered, Decision, Rationale, Consequences
- Every significant architectural decision gets an ADR *before* code is written
- ADRs are referenced from relevant code via comments: `# See ADR-005 for why LangGraph over CrewAI`

### Git
- Atomic commits: one logical change per commit
- Commit message format: imperative mood, explain the *why* not just the *what*
- Example: `Add semantic chunker with section detection` not `updated chunker.py`
- Build each pillar as a sequence of commits that tells a story

---

## Build Order (Roadmap)

Build in this order. Each phase should be fully working before moving to the next.

### Phase 0: Project Skeleton
- Initialise repo, CLAUDE.md, README.md
- pyproject.toml with all Python dependencies
- Docker Compose: Postgres + pgvector
- FastAPI app skeleton with health check
- Next.js app scaffold with Tailwind, root layout, navigation
- `.env.example` with all required env vars documented
- CI pipeline: lint + type check + test (initially empty)

### Phase 1: Document Processing & Chunking (Pillar 1)
- SQLAlchemy models for Document and Chunk (with pgvector column)
- Semantic chunker: regex-based section detection, token-aware splitting
- Naive chunker: simple fixed-size for comparison
- FastAPI endpoints: upload document, get chunks, compare strategies
- Frontend page: upload interface, chunk visualiser, strategy toggle
- Unit tests for both chunkers

### Phase 2: Embeddings & Retrieval (Pillar 2)
- Voyage AI embedding client with `@observe` tracing
- pgvector storage: store embeddings, similarity search
- Support multiple distance metrics (cosine, euclidean, dot product)
- FastAPI endpoints: embed text, search similar, compare metrics
- Frontend page: embed + search interface, metric comparison, score visualisation
- Unit tests for embedder, integration tests for pgvector search

### Phase 3: RAG Pipeline (Pillar 3)
- Reranker (LLM-based reranking of retrieved chunks)
- RAG pipeline orchestrator: retrieve → rerank → build prompt → generate
- Each stage returns intermediate results for UI visibility
- FastAPI endpoints: run RAG pipeline with step-by-step results
- Frontend page: JD input, pipeline stage visualiser, expandable results at each step
- Integration tests for full pipeline

### Phase 4: Agentic Workflow (Pillar 4)
- LangGraph state machine: RecruitmentState, nodes, conditional routing
- Node functions: parse_cv, match_candidate, route_candidate, screen, reject, outreach
- State serialisation for frontend consumption (state at each step)
- FastAPI endpoints: run workflow, get execution trace with state per node
- Frontend page: graph visualiser (React Flow), step-through execution, state inspector
- Unit tests for each node, integration test for full graph

### Phase 5: Observability & Cost (Pillar 5)
- Langfuse tracing on all LLM calls and pipeline steps (should already be partially done from earlier phases)
- Cost calculation: token counts × model pricing per trace
- Langfuse prompt management: create versioned prompts, serve at runtime
- FastAPI endpoints: fetch traces, cost summaries, latency breakdowns
- Frontend page: trace explorer, cost dashboard, latency waterfall, token usage charts
- Ensure all previous pillars are fully traced

### Phase 6: Evaluation Pipeline (Pillar 6)
- Golden dataset: hand-labelled CV/JD pairs with expected match outcomes
- Retrieval metrics: precision@k, recall@k, MRR
- LLM-as-judge: faithfulness and relevance scoring
- Evaluation runner: scores pipeline against golden set, pushes to Langfuse
- FastAPI endpoints: trigger eval run, get results, get historical metrics
- Frontend page: run evaluation, metrics dashboard, drill into failures, trend charts
- Eval tests in CI as quality gate

### Phase 7: Guardrails & Safety (Pillar 7)
- PII detection (regex patterns for email, phone, NI numbers, addresses)
- Faithfulness scoring via LLM-as-judge
- Budget enforcement (per-request token/cost limits)
- Guardrail validator orchestrating all layers
- FastAPI endpoints: test guardrails, submit text for checking
- Frontend page: interactive guardrail tester, example pass/fail cases, toggle layers
- Unit tests for each guardrail

### Phase 8: Prompt Engineering & Management (Pillar 8)
- Prompt template system with variable injection
- Langfuse prompt versioning integration
- A/B comparison runner: same input, different prompt versions
- FastAPI endpoints: list prompts, get versions, run comparison
- Frontend page: prompt editor, version history, side-by-side output comparison
- Unit tests for template rendering

### Phase 9: Structured Outputs & Validation (Pillar 9)
- Pydantic models for all expected LLM output schemas
- Parse → validate → retry pipeline with error feedback
- Configurable retry count and strategy
- FastAPI endpoints: run structured output demo, show raw vs parsed
- Frontend page: schema viewer, live demo with success/failure cases, retry visualisation
- Unit tests for parser and retry logic

### Phase 10: Error Handling & Fallbacks (Pillar 10)
- Retry with exponential backoff
- Fallback chains (primary model → fallback model)
- Circuit breaker pattern
- Timeout management (per-step, per-request)
- FastAPI endpoints: simulate failures, show fallback behaviour
- Frontend page: failure simulator, fallback chain visualisation, circuit breaker state
- Unit tests for retry, fallback, and circuit breaker logic

### Phase 11: Polish & Integration
- README.md with setup guide, architecture overview, pillar index
- Architecture diagram in `docs/architecture.md`
- Ensure all ADRs are written and cross-referenced from code
- CI pipeline: lint, type check, unit tests, integration tests, eval quality gate
- Docker Compose: all three services running together
- Seed data script for quick demo setup
- Final pass: ensure every module has teaching-quality docstrings

---

## Commands

```bash
# Backend
cd src && uvicorn main:app --reload --port 8000       # Run API server
pytest tests/unit -v                                    # Run unit tests
pytest tests/integration -v                             # Run integration tests (needs DB)
python -m scripts.run_eval                              # Run evaluation pipeline

# Frontend
cd web && npm run dev                                   # Run Next.js dev server
cd web && npm run build                                 # Production build
cd web && npm run lint                                  # Lint TypeScript

# Infrastructure
docker compose up -d                                    # Start Postgres + pgvector
docker compose up                                       # Start all services (db + api + web)
docker compose down                                     # Stop all services

# Quality
ruff check src/ tests/                                  # Python linting
ruff format src/ tests/                                 # Python formatting
mypy src/                                               # Type checking
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/workshop

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Voyage AI (Embeddings)
VOYAGE_API_KEY=pa-...

# Langfuse (Observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# App
APP_ENV=development
LOG_LEVEL=INFO
```

---

## Important Notes

- This is a **teaching platform and portfolio piece**. Every decision should be explainable. If you can't explain why something is built a certain way, redesign it until you can.
- The frontend is **interactive documentation**, not a production product. Functional and clean, not pixel-perfect. Clarity over polish.
- **Code annotations are a deliverable**. Docstrings with "Interview talking points" are as important as the code itself.
- Each pillar's frontend page should be self-contained enough that someone could use just that page to understand the concept.
- ADRs are written *before* implementation. The ADR explains the options considered and why we chose what we chose. This mirrors real senior engineering practice and gives interview talking points.
- All LLM calls must be traced via Langfuse. No untraced calls. This is non-negotiable for the observability story.

