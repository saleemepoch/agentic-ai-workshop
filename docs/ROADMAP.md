# Agentic AI Workshop — Roadmap

> Checklist-based roadmap. Tick items as completed. Pillars 5–8 are priority.

---

## Phase 0: Architecture & Foundation

### 0.1 — Architectural Documentation
- [x] C4 Level 1: System Context diagram (Mermaid) — users, external systems, workshop platform
- [x] C4 Level 2: Container diagram — API, Web, Postgres, Langfuse Cloud, Voyage AI, Claude API
- [x] C4 Level 3: Component diagram — internal modules per container (documents, matching, agents, etc.)
- [x] C4 Level 4: Code diagram — key classes/functions within critical components
- [x] Write `docs/architecture.md` combining all four C4 levels with explanatory text

### 0.2 — Project Skeleton
- [x] Initialise git repo
- [x] Create `pyproject.toml` with all Python dependencies (FastAPI, SQLAlchemy, asyncpg, pgvector, anthropic, voyageai, langgraph, langfuse, pydantic, pytest, ruff, mypy)
- [x] Create `.env.example` with all required environment variables documented
- [x] Create `.gitignore` (Python, Node, IDE, .env)
- [x] Create initial `README.md` (project overview, setup instructions, pillar index — flesh out later)

### 0.3 — Docker & Infrastructure
- [x] `docker-compose.yml` with three services: postgres (pgvector), api (Python), web (Next.js)
- [x] `Dockerfile` for Python API (multi-stage, slim)
- [x] `Dockerfile.web` for Next.js frontend
- [x] Postgres initialisation: enable pgvector extension
- [ ] Verify all three containers build and start cleanly

### 0.4 — FastAPI App Skeleton
- [x] `src/__init__.py`
- [x] `src/config.py` — Pydantic Settings loading from `.env`
- [x] `src/database.py` — SQLAlchemy async engine, session factory, pgvector setup
- [x] `src/main.py` — FastAPI app with CORS, lifespan (DB init), health check endpoint
- [ ] Verify `GET /health` returns 200 from within Docker

### 0.5 — Next.js App Scaffold
- [x] Initialise Next.js app in `web/` with TypeScript, Tailwind CSS, App Router
- [x] Configure `tailwind.config.ts` with dark mode (class strategy), professional colour palette
- [x] Root layout (`layout.tsx`): dark/light mode toggle, sidebar with pillar navigation
- [x] Home page (`page.tsx`): workshop overview, pillar cards linking to each section
- [x] `web/src/lib/api.ts` — typed API client skeleton (base URL, fetch wrapper)
- [x] `web/src/lib/types.ts` — shared TypeScript types (empty, populated per pillar)
- [x] Verify frontend builds and renders in Docker

### 0.6 — Test Infrastructure
- [x] `tests/__init__.py`, `tests/conftest.py` with shared fixtures (async DB session, test client)
- [x] `tests/unit/` and `tests/integration/` directory structure mirroring `src/`
- [x] Verify `pytest` runs with zero tests collected (no errors)

---

## Phase 1: Document Processing & Chunking (Pillar 1)

### 1.1 — ADR
- [x] Write `docs/adrs/001-document-processing.md` — chunking strategy decisions, semantic vs naive, token-aware splitting, trade-offs

### 1.2 — Backend Implementation
- [x] `src/documents/__init__.py`
- [x] `src/documents/models.py` — SQLAlchemy models: `Document` (id, title, content, doc_type, created_at), `Chunk` (id, document_id, content, chunk_index, token_count, strategy, embedding vector column)
- [x] `src/documents/schemas.py` — Pydantic schemas: `DocumentCreate`, `DocumentResponse`, `ChunkResponse`, `ChunkingComparisonResponse`
- [x] `src/documents/chunker.py` — Semantic chunker: section detection (headings, blank lines, topic shifts), token-aware splitting with configurable overlap
- [x] `src/documents/naive_chunker.py` — Naive fixed-size chunker (split by token count, no section awareness)
- [x] `src/documents/service.py` — CRUD: create document, chunk with chosen strategy, get chunks, compare strategies side-by-side
- [x] `src/documents/router.py` — Endpoints: `POST /documents`, `GET /documents/{id}/chunks`, `POST /documents/{id}/chunk`, `POST /documents/compare-strategies`
- [ ] Run Alembic or auto-create tables, verify document + chunk storage works

### 1.3 — Sample Data
- [ ] Create 10 realistic fictional CVs (mix: software engineer, data scientist, PM, designer, DevOps — varied seniority)
- [ ] Create 10 realistic fictional JDs matching the same role mix
- [ ] `scripts/seed_data.py` — script to load sample CVs and JDs into the database

### 1.4 — Tests
- [x] `tests/unit/documents/test_chunker.py` — semantic chunker: section detection, token limits, overlap, edge cases (empty doc, single section, very long section)
- [x] `tests/unit/documents/test_naive_chunker.py` — naive chunker: fixed-size splitting, boundary handling
- [ ] `tests/integration/documents/test_document_api.py` — upload document, retrieve chunks, compare strategies via API

---

## Phase 2: Embeddings & Retrieval (Pillar 2)

### 2.1 — ADR
- [x] Write `docs/adrs/002-embedding-model.md` — why Voyage AI, embedding dimensions, distance metric trade-offs (cosine vs euclidean vs dot product)

### 2.2 — Backend Implementation
- [x] `src/matching/__init__.py`
- [x] `src/matching/embedder.py` — Voyage AI client wrapper (lazy init) with batch embedding support
- [x] `src/matching/retriever.py` — pgvector similarity search with configurable distance metric (cosine, euclidean, dot product), top-k parameter
- [x] `src/matching/schemas.py` — Pydantic schemas: `EmbeddingRequest`, `SearchRequest`, `SearchResult`, `MetricComparisonResponse`
- [x] `src/matching/service.py` — embed and store chunks, similarity search, compare distance metrics on same query
- [x] `src/matching/router.py` — Endpoints: `POST /embeddings/embed`, `POST /embeddings/search`, `POST /embeddings/compare-metrics`
- [ ] Embed all sample data chunks and store vectors in pgvector

### 2.3 — Tests
- [x] `tests/unit/matching/test_embedder.py` — embedding client: input validation, batch handling (requires VOYAGE_API_KEY)
- [x] `tests/integration/matching/test_retrieval.py` — embed, store, search, verify ranking; compare distance metrics

---

## Phase 3: RAG Pipeline (Pillar 3)

### 3.1 — ADR
- [x] Write `docs/adrs/003-rag-pipeline.md` — pipeline stages, reranking strategy, context window budgeting, prompt construction approach

### 3.2 — Backend Implementation
- [x] `src/matching/reranker.py` — LLM-based reranking: score each retrieved chunk for relevance to query, re-sort
- [x] `src/matching/rag_pipeline.py` — orchestrator: retrieve → rerank → build prompt (with token budgeting) → generate via Claude; each stage returns intermediate results
- [x] Update `src/matching/schemas.py` — `RAGRequest`, `RAGStageResult`, `RAGPipelineResponse` (contains results at each stage)
- [x] Update `src/matching/router.py` — `POST /embeddings/rag/run` (full pipeline with stage-by-stage results)

### 3.3 — Tests
- [x] `tests/unit/matching/test_reranker.py` — reranker scoring, sort order, edge cases (requires ANTHROPIC_API_KEY)
- [x] `tests/integration/matching/test_rag_pipeline.py` — full pipeline run with real APIs: verify all stages return results, final generation is grounded

---

## Phase 4: Agentic Workflow — LangGraph (Pillar 4)

### 4.1 — ADR
- [x] Write `docs/adrs/004-agent-orchestration.md` — why LangGraph over CrewAI/AutoGen, state machine design, node responsibilities, conditional routing logic

### 4.2 — Backend Implementation
- [x] `src/agents/__init__.py`
- [x] `src/agents/state.py` — `RecruitmentState` TypedDict with full field set
- [x] `src/agents/nodes.py` — node functions: parse_cv, parse_jd, match_candidate, route_candidate, screen_candidate, reject_candidate, generate_outreach
- [x] `src/agents/tools.py` — placeholder (nodes call LLM directly; tool-calling pattern documented for future)
- [x] `src/agents/graph.py` — LangGraph StateGraph with conditional edges, compile, graph structure serialisation
- [x] `src/agents/schemas.py` — WorkflowRequest, WorkflowStepResult, WorkflowResponse, GraphStructureResponse
- [x] `src/agents/router.py` — POST /agents/run, GET /agents/graph

### 4.3 — Tests
- [x] `tests/unit/agents/test_nodes.py` — routing logic: 8 tests covering all score boundaries and edge cases (all passing)
- [x] `tests/integration/agents/test_workflow.py` — full graph execution: strong match → outreach, weak match → rejection, graph structure

---

## Phase 5: Observability & Cost Management (Pillar 5) ⭐ Priority

### 5.1 — ADR
- [x] Write `docs/adrs/005-observability.md` — why Langfuse, trace hierarchy design, cost tracking approach, what to measure and why

### 5.2 — Backend Implementation
- [x] `src/observability/__init__.py`
- [x] `src/observability/tracing.py` — Langfuse client (lazy init), @observe re-export, flush/shutdown
- [x] `src/observability/cost.py` — cost calculation with model pricing table, CostSummary aggregation
- [x] `src/observability/prompts.py` — Langfuse prompt management integration
- [x] `src/observability/router.py` — GET /traces, GET /traces/{id}, GET /costs/summary, GET /models, POST /costs/calculate
- [x] Retrofit `@observe` tracing on ALL LLM calls across Pillars 2–4 (embedder, reranker, RAG pipeline, all agent nodes)
- [x] Langfuse flush/shutdown wired into FastAPI lifespan

### 5.3 — Tests
- [x] `tests/unit/observability/test_cost.py` — 11 tests: pricing lookup, cost arithmetic, summary aggregation (all passing)
- [x] `tests/integration/observability/test_tracing.py` — trace endpoints, model pricing, cost calculation

---

## Phase 6: Evaluation Pipeline (Pillar 6) ⭐ Priority

### 6.1 — ADR
- [x] Write `docs/adrs/006-evaluation.md` — golden dataset design, metric selection, LLM-as-judge approach

### 6.2 — Backend Implementation
- [x] `src/evaluation/__init__.py`
- [x] `src/evaluation/golden_dataset.py` — 5 hand-labelled cases: clear match, clear mismatch, overqualified, transferable skills, seniority gap
- [x] `src/evaluation/metrics.py` — precision@k, recall@k, MRR with compute_retrieval_metrics helper
- [x] `src/evaluation/llm_judge.py` — faithfulness and relevance scoring with @observe tracing
- [x] `src/evaluation/runner.py` — evaluation runner: run pipeline, compute metrics, return EvalRunResult
- [x] `src/evaluation/router.py` — POST /evaluation/run, GET /results, GET /results/history, GET /golden
- [ ] `scripts/run_eval.py` — CLI wrapper for evaluation runner

### 6.3 — Tests
- [x] `tests/unit/evaluation/test_metrics.py` — 19 tests: precision, recall, MRR calculations (all passing)
- [ ] `tests/integration/evaluation/test_eval_runner.py` — full eval run with real APIs
- [ ] `tests/eval/test_quality_gate.py` — quality gate for CI

---

## Phase 7: Guardrails & Safety (Pillar 7) ⭐ Priority

### 7.1 — ADR
- [x] Write `docs/adrs/007-guardrails.md` — layered approach (Option A) with cost-proportional checking, failure taxonomy, Option C noted as rejected

### 7.2 — Backend Implementation
- [x] `src/guardrails/__init__.py`
- [x] `src/guardrails/pii.py` — PII detection: email, phone (UK + intl), NI number, postcode, credit card; detect/has/redact functions
- [x] `src/guardrails/budget.py` — per-request budget enforcement: token limits + cost limits with violations list
- [x] `src/guardrails/faithfulness.py` — LLM-as-judge faithfulness and completeness (reuses LLMJudge from evaluation)
- [x] `src/guardrails/validator.py` — orchestrator with fail-fast, deterministic sampling for Layer 3
- [x] `src/guardrails/router.py` — POST /check, POST /check/pii, POST /check/budget, POST /check/faithfulness, POST /check/completeness, GET /config

### 7.3 — Tests
- [x] `tests/unit/guardrails/test_pii.py` — 16 tests covering all PII types and redaction
- [x] `tests/unit/guardrails/test_budget.py` — 7 tests covering all budget violations
- [x] `tests/unit/guardrails/test_validator.py` — 8 tests covering orchestration, fail-fast, sampling
- [ ] `tests/integration/guardrails/test_guardrails_api.py` — integration via API with real LLM judge

---

## Phase 8: Prompt Engineering & Management (Pillar 8) ⭐ Priority

### 8.1 — ADR
- [x] Write `docs/adrs/008-prompt-management.md` — local YAML versioning, git as audit trail, Langfuse referenced as alternative

### 8.2 — Backend Implementation
- [x] `src/prompts/__init__.py`
- [x] `src/prompts/loader.py` — YAML loader, Prompt and PromptVersion dataclasses, variable injection, version selection
- [x] `src/prompts/templates/` — 3 seed prompts: match_scorer, cv_parser, outreach_email (each with 2 versions)
- [x] `src/prompts/registry.py` — caching registry, A/B comparison runner with @observe tracing
- [x] `src/prompts/router.py` — GET /prompts, GET /{name}, POST /{name}/render, POST /compare

### 8.3 — Tests
- [x] `tests/unit/prompts/test_templates.py` — 12 tests: loading, rendering, version selection, error cases (all passing)
- [ ] `tests/integration/prompts/test_prompt_comparison.py` — A/B comparison with real LLM

---

## Phase 9: Structured Outputs & Validation (Pillar 9)

### 9.1 — ADR
- [x] Write `docs/adrs/009-structured-outputs.md` — Pydantic + parse-validate-retry pipeline, retry feedback strategy

### 9.2 — Backend Implementation
- [x] `src/structured/__init__.py`
- [x] `src/structured/output_models.py` — 5 schemas: CandidateProfile, JobRequirements, MatchAssessment, ScreeningDecision, OutreachEmail
- [x] `src/structured/parser.py` — parse-validate-retry pipeline with error feedback, attempt history, @observe tracing
- [x] `src/structured/router.py` — GET /schemas, GET /schemas/{name}, POST /parse, POST /demo

### 9.3 — Tests
- [x] `tests/unit/structured/test_parser.py` — 17 tests: schemas, validation, parser logic (all passing)
- [ ] `tests/integration/structured/test_structured_api.py` — real LLM with retry behaviour

---

## Phase 10: Error Handling & Fallbacks (Pillar 10)

### 10.1 — ADR
- [x] Write `docs/adrs/010-error-handling.md` — retry, fallback, circuit breaker patterns; built from scratch for teaching value

### 10.2 — Backend Implementation
- [x] `src/resilience/__init__.py`
- [x] `src/resilience/retry.py` — exponential backoff with jitter, configurable retry-on, attempt history
- [x] `src/resilience/fallback.py` — ordered provider chain, records which provider succeeded
- [x] `src/resilience/circuit_breaker.py` — closed/open/half-open state machine, per-service registry
- [x] `src/resilience/router.py` — POST /demo/retry, /demo/fallback, /demo/circuit-breaker, GET /circuit-breaker/state, POST /circuit-breaker/reset

### 10.3 — Tests
- [x] `tests/unit/resilience/test_retry.py` — 9 tests: backoff calculation, success/failure paths, exception filtering
- [x] `tests/unit/resilience/test_circuit_breaker.py` — 8 tests: all state transitions, reset
- [x] `tests/unit/resilience/test_fallback.py` — 5 tests: success, fallback, all-fail, empty chain
- [ ] `tests/integration/resilience/test_resilience_api.py` — simulate failures via API

---

## Phase 11: Frontend

### 11.1 — Shared Components
- [x] Layout: Navbar (dark/light toggle), Sidebar (pillar navigation with priority indicators)
- [x] UI: Button, Card, Badge, CodeBlock, ExpandableSection, MetricCard
- [x] PipelineStages — reusable expandable stage visualiser
- [x] PillarHeader — consistent page heading with priority indicator
- [x] Dark mode CSS variables, class strategy, localStorage persistence
- [x] Typed API client (`web/src/lib/api.ts`) with all 10 pillar endpoints
- [x] Shared TypeScript types (`web/src/lib/types.ts`) mirroring Pydantic schemas

### 11.2 — Pillar 1: Chunking Page
- [x] Textarea input with sample CV
- [x] Strategy comparison (calls `/documents/{id}/compare`)
- [x] Colour-coded chunk visualiser with token counts
- [x] Side-by-side semantic vs naive comparison
- [x] Behind-the-scenes expandable explanation

### 11.3 — Pillar 2: Embeddings & Retrieval Page
- [x] Query input with sample queries
- [x] Embedding visualisation (first 32 dimensions as coloured cells)
- [x] Three-metric comparison (cosine, euclidean, inner product)
- [x] Top-K slider, embed-all button
- [x] Behind-the-scenes distance metric explanation

### 11.4 — Pillar 3: RAG Pipeline Page
- [x] Query input + filters (top_k, doc_type)
- [x] PipelineStages visualiser with all 5 stages expandable
- [x] Per-stage timing and JSON results
- [x] Final response display with cost/token metrics
- [x] Behind-the-scenes pipeline architecture

### 11.5 — Pillar 4: Agents Page
- [x] React Flow graph visualiser with state-based node colouring
- [x] Animated node traversal (active/visited highlighting)
- [x] Conditional edge highlighting based on routing decision
- [x] Step-through execution trace (click to inspect each step)
- [x] Match assessment, outreach email, parsed CV/JD displays
- [x] Behind-the-scenes LangGraph explanation

### 11.6 — Pillar 5: Observability Page ⭐
- [x] Cost dashboard (total, per-request, LLM vs embedding breakdown)
- [x] Model pricing table
- [x] Recent traces from Langfuse
- [x] Refresh button
- [x] Behind-the-scenes observability strategy

### 11.7 — Pillar 6: Evaluation Page ⭐
- [x] Golden dataset display (5 cases with descriptions)
- [x] "Run Evaluation" button triggers full pipeline run
- [x] Per-case results with pass/fail and scores
- [x] Aggregate metrics (score accuracy, outcome accuracy, faithfulness, relevance)
- [x] Evaluation history (trend tracking)
- [x] Behind-the-scenes methodology explanation

### 11.8 — Pillar 7: Guardrails Page ⭐
- [x] PII detection demo with example chips (clean, email leak, NI number, multiple PII)
- [x] Full pipeline check with faithful vs hallucinated examples
- [x] Per-layer results display (Layer 1 / 2 / 3) with fail-fast visualisation
- [x] Redacted text preview after PII detection
- [x] Behind-the-scenes cost-proportional checking explanation

### 11.9 — Pillar 8: Prompt Management Page ⭐
- [x] Prompt list with version count badges
- [x] Per-prompt version viewer with notes and templates
- [x] A/B version comparison with side-by-side LLM outputs
- [x] Token usage display per version
- [x] Behind-the-scenes local YAML versioning explanation

### 11.10 — Pillar 9: Structured Outputs Page
- [x] Schema picker (5 schemas) with JSON schema viewer
- [x] Editable prompt with samples per schema
- [x] Parse-validate-retry pipeline visualisation
- [x] Per-attempt display (raw response, errors, success status)
- [x] Validated output display
- [x] Behind-the-scenes pipeline explanation

### 11.11 — Pillar 10: Resilience Page
- [x] Retry demo with configurable failure count + max attempts
- [x] Per-attempt visualisation showing backoff delays
- [x] Fallback chain demo with provider list
- [x] Circuit breaker interactive controls (trip/recover/reset)
- [x] Live circuit breaker state display with cooldown
- [x] Behind-the-scenes patterns explanation

---

## Phase 12: Polish & Integration

### 12.1 — CI/CD
- [ ] GitHub Actions workflow: lint (ruff), type check (mypy), unit tests, integration tests
- [ ] Evaluation quality gate in CI (metrics must meet thresholds)
- [ ] Frontend: lint (ESLint), type check (tsc), build check

### 12.2 — Documentation
- [ ] Flesh out `README.md`: full setup guide, architecture overview, pillar index with descriptions, screenshots
- [ ] Verify all ADRs are complete and cross-referenced from code comments
- [ ] Verify all module-level docstrings have "Interview talking points" sections
- [ ] Review all "Behind the scenes" sections for accuracy and depth

### 12.3 — Demo Readiness
- [ ] `scripts/seed_data.py` — seed database with all sample CVs/JDs, embed and store vectors
- [ ] `scripts/demo.py` — quick demo script: runs key scenarios, prints results
- [ ] Verify full Docker Compose startup: `docker compose up` → all services healthy → frontend accessible
- [ ] End-to-end smoke test: upload document → chunk → embed → search → RAG → agent workflow → check traces → run eval

### 12.4 — Final Review
- [ ] Code review pass: remove dead code, ensure consistent patterns
- [ ] Verify dark/light mode works across all pages
- [ ] Test all interactive demos with sample data
- [ ] Verify all API endpoints have correct error responses
- [ ] Performance check: no obviously slow queries or unnecessary re-renders
