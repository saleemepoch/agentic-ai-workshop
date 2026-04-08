# Architecture — Agentic AI Workshop

> C4 model documentation. Four levels of zoom, from system context down to code.
> All diagrams use Mermaid. Each level includes explanatory text for teaching purposes.

---

## Level 1: System Context

**What this shows**: The workshop platform as a single box, the humans who use it, and the external services it depends on. This is the "elevator pitch" diagram — anyone should understand it in 30 seconds.

```mermaid
graph TB
    User["👤 Developer / Learner<br/><i>Explores agentic AI concepts<br/>through interactive demos</i>"]

    Workshop["🏗️ Agentic AI Workshop<br/><i>Teaching platform for agentic AI,<br/>RAG, and production AI engineering</i>"]

    Claude["🤖 Claude API<br/><i>Anthropic LLM<br/>Generation, scoring, judging</i>"]
    Voyage["🧭 Voyage AI<br/><i>Text embeddings<br/>for semantic search</i>"]
    Langfuse["📊 Langfuse Cloud<br/><i>Observability, tracing,<br/>cost tracking</i>"]

    User -->|"Interacts with UI:<br/>uploads docs, runs pipelines,<br/>explores traces"| Workshop
    Workshop -->|"LLM calls: generation,<br/>reranking, judging,<br/>structured outputs"| Claude
    Workshop -->|"Embedding requests:<br/>text → vectors"| Voyage
    Workshop -->|"Sends traces, costs,<br/>fetches prompt versions"| Langfuse

    style Workshop fill:#1e293b,stroke:#3b82f6,stroke-width:3px,color:#e2e8f0
    style User fill:#0f172a,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Claude fill:#0f172a,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style Voyage fill:#0f172a,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style Langfuse fill:#0f172a,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
```

**Key decisions at this level**:
- Three external AI services, each with a distinct responsibility. No single vendor lock-in for all capabilities.
- Claude handles all generative tasks (matching, screening, outreach, judging). We chose a single LLM provider for consistency in the teaching narrative, though the fallback system (Pillar 10) demonstrates multi-provider resilience.
- Voyage AI is dedicated to embeddings — separated from the LLM provider because embedding-specialised models outperform general-purpose LLMs at vector representation (see ADR-002).
- Langfuse is the observability backbone — every LLM call is traced, costed, and auditable. This is non-negotiable for the production AI engineering story.

---

## Level 2: Container Diagram

**What this shows**: The major deployable units (containers) that make up the workshop platform, how they communicate, and what technology each uses. This is the diagram you'd draw on a whiteboard when onboarding a new team member.

```mermaid
graph TB
    User["👤 Developer / Learner"]

    subgraph Workshop Platform
        Web["🌐 Web Application<br/><i>Next.js · TypeScript · Tailwind</i><br/><br/>Interactive pillar pages,<br/>pipeline visualisers,<br/>agent graph animation,<br/>metrics dashboards"]

        API["⚡ API Server<br/><i>FastAPI · Python 3.12+</i><br/><br/>Business logic for all 10 pillars,<br/>LLM orchestration, RAG pipeline,<br/>agent workflows, guardrails"]

        DB["🗄️ Database<br/><i>PostgreSQL · pgvector</i><br/><br/>Documents, chunks,<br/>vector embeddings,<br/>evaluation results"]
    end

    Claude["🤖 Claude API"]
    Voyage["🧭 Voyage AI"]
    Langfuse["📊 Langfuse Cloud"]

    User -->|"HTTPS · Browser"| Web
    Web -->|"REST · JSON<br/>Typed API client"| API
    API -->|"SQLAlchemy async<br/>asyncpg driver"| DB
    API -->|"anthropic SDK<br/>Generation + Judging"| Claude
    API -->|"voyageai SDK<br/>Embed text → vectors"| Voyage
    API -->|"langfuse SDK<br/>Traces, costs, prompts"| Langfuse

    style Web fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style API fill:#1e293b,stroke:#3b82f6,stroke-width:3px,color:#e2e8f0
    style DB fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#e2e8f0
    style User fill:#0f172a,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Claude fill:#0f172a,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style Voyage fill:#0f172a,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style Langfuse fill:#0f172a,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
```

**Key decisions at this level**:
- **Three containers, not a monolith**: Postgres, API, and Web are independently deployable via Docker Compose. This mirrors real-world architecture without over-engineering (no Kubernetes, no service mesh).
- **FastAPI as the API layer**: Async-native, automatic OpenAPI docs, Pydantic-first validation. The API is the single source of truth — the frontend never calls external services directly. See ADR-002.
- **PostgreSQL + pgvector**: One database for both relational data (documents, eval results) and vector search. Avoids the complexity of a separate vector database (Pinecone, Weaviate) while teaching the same concepts. See ADR-003.
- **Next.js App Router**: Server Components by default for fast initial loads, Client Components only where interactivity is needed (demos, animations). The frontend is interactive documentation, not a production SaaS.
- **Communication**: Web → API is REST/JSON via a typed TypeScript client. API → DB is SQLAlchemy async. API → external services use their respective Python SDKs.

---

## Level 3: Component Diagram

**What this shows**: The internal modules within the API server — each mapping to a pillar of the workshop. This is how a developer navigates the codebase.

```mermaid
graph TB
    subgraph "API Server (FastAPI)"

        subgraph "Core"
            Main["main.py<br/><i>App entry, CORS, lifespan,<br/>router mounting</i>"]
            Config["config.py<br/><i>Pydantic Settings,<br/>env var management</i>"]
            Database["database.py<br/><i>SQLAlchemy async engine,<br/>session factory</i>"]
        end

        subgraph "Pillar 1: Documents"
            DocRouter["router.py"]
            DocService["service.py"]
            Chunker["chunker.py<br/><i>Semantic chunking</i>"]
            NaiveChunker["naive_chunker.py<br/><i>Fixed-size chunking</i>"]
            DocModels["models.py<br/><i>Document, Chunk</i>"]
        end

        subgraph "Pillar 2–3: Matching & RAG"
            MatchRouter["router.py"]
            MatchService["service.py"]
            Embedder["embedder.py<br/><i>Voyage AI client</i>"]
            Retriever["retriever.py<br/><i>pgvector search</i>"]
            Reranker["reranker.py<br/><i>LLM-based reranking</i>"]
            RAG["rag_pipeline.py<br/><i>Retrieve → Rerank →<br/>Prompt → Generate</i>"]
        end

        subgraph "Pillar 4: Agents"
            AgentRouter["router.py"]
            State["state.py<br/><i>RecruitmentState</i>"]
            Nodes["nodes.py<br/><i>Parse, Match, Route,<br/>Screen, Outreach</i>"]
            Graph["graph.py<br/><i>LangGraph StateGraph</i>"]
            Tools["tools.py<br/><i>Agent tools</i>"]
        end

        subgraph "Pillar 5: Observability ⭐"
            ObsRouter["router.py"]
            Tracing["tracing.py<br/><i>Langfuse @observe</i>"]
            Cost["cost.py<br/><i>Token counting,<br/>cost calculation</i>"]
            Prompts["prompts.py<br/><i>Langfuse prompt mgmt</i>"]
        end

        subgraph "Pillar 6: Evaluation ⭐"
            EvalRouter["router.py"]
            GoldenDS["golden_dataset.py<br/><i>Labelled CV/JD pairs</i>"]
            Metrics["metrics.py<br/><i>Precision, Recall, MRR</i>"]
            LLMJudge["llm_judge.py<br/><i>Faithfulness scoring</i>"]
            Runner["runner.py<br/><i>Eval orchestrator</i>"]
        end

        subgraph "Pillar 7: Guardrails ⭐"
            GuardRouter["router.py"]
            PII["pii.py<br/><i>PII detection</i>"]
            Faithful["faithfulness.py<br/><i>LLM-as-judge</i>"]
            Budget["budget.py<br/><i>Budget enforcement</i>"]
            Validator["validator.py<br/><i>Layer orchestrator</i>"]
        end

        subgraph "Pillar 8: Prompts ⭐"
            PromptRouter["router.py"]
            Templates["templates.py<br/><i>YAML templates,<br/>variable injection</i>"]
            Registry["registry.py<br/><i>Versioning, A/B runner</i>"]
        end

        subgraph "Pillar 9: Structured"
            StructRouter["router.py"]
            OutputModels["output_models.py<br/><i>Pydantic LLM schemas</i>"]
            Parser["parser.py<br/><i>Parse → Validate →<br/>Retry pipeline</i>"]
        end

        subgraph "Pillar 10: Resilience"
            ResRouter["router.py"]
            Retry["retry.py<br/><i>Exponential backoff</i>"]
            Fallback["fallback.py<br/><i>Provider fallback chain</i>"]
            CB["circuit_breaker.py<br/><i>Circuit breaker pattern</i>"]
        end
    end

    Main --> DocRouter & MatchRouter & AgentRouter & ObsRouter & EvalRouter & GuardRouter & PromptRouter & StructRouter & ResRouter
    DocRouter --> DocService --> Chunker & NaiveChunker & DocModels
    MatchRouter --> MatchService --> Embedder & Retriever & Reranker & RAG
    AgentRouter --> Graph --> Nodes --> Tools
    Nodes --> State

    Tracing -.->|"@observe decorates"| Embedder & Reranker & RAG & Nodes & LLMJudge & Parser & Faithful

    style Main fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#e2e8f0
    style Tracing fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#e2e8f0
```

**Key decisions at this level**:
- **Router → Service → Model**: Consistent layering. Routers handle HTTP concerns, services contain business logic, models handle persistence. No router ever touches the DB directly.
- **Tracing is cross-cutting**: The `@observe` decorator from `observability/tracing.py` wraps functions across all pillars. It's not isolated to Pillar 5 — it's woven through everything. Shown as dotted lines above.
- **Each pillar is a Python package**: Self-contained with its own router, service, schemas, and models. Pillars depend on each other where logical (Agents use Matching, Evaluation uses RAG) but avoid circular dependencies.
- **Guardrails orchestrator pattern**: `validator.py` orchestrates the three layers rather than each layer knowing about the others. This makes it easy to toggle layers, adjust sampling, and test in isolation.

---

## Level 4: Code Diagram

**What this shows**: Key classes, functions, and data flows within the most critical components. This level is selective — we zoom into the RAG pipeline, the agent graph, and the guardrails validator because these are the most architecturally interesting.

### 4a. RAG Pipeline — Internal Flow

```mermaid
graph LR
    Input["RAGRequest<br/><i>query: str<br/>top_k: int<br/>distance_metric: str</i>"]

    subgraph "rag_pipeline.py → run()"
        Embed["embed_query()<br/><i>Voyage AI<br/>query → vector</i>"]
        Retrieve["retrieve()<br/><i>pgvector search<br/>top_k candidates</i>"]
        Rerank["rerank()<br/><i>LLM scores each<br/>chunk for relevance</i>"]
        BuildPrompt["build_prompt()<br/><i>Token budgeting:<br/>fit top chunks into<br/>context window</i>"]
        Generate["generate()<br/><i>Claude API call<br/>with constructed prompt</i>"]
    end

    Output["RAGPipelineResponse<br/><i>stage_results: list<br/>final_output: str<br/>trace_id: str<br/>total_cost: float</i>"]

    Input --> Embed --> Retrieve --> Rerank --> BuildPrompt --> Generate --> Output

    style Embed fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Retrieve fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Rerank fill:#1e293b,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style BuildPrompt fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#e2e8f0
    style Generate fill:#1e293b,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
```

**Teaching points**:
- Each stage is independently observable (own Langfuse span) and returns intermediate results for the frontend.
- `build_prompt()` is where token budgeting happens: we measure how many tokens the retrieved chunks consume and trim to fit the model's context window. This is a critical production concern most tutorials skip.
- `rerank()` is an LLM call itself — it adds latency and cost, but dramatically improves relevance. The evaluation pipeline (Pillar 6) quantifies this improvement.

### 4b. Agent Graph — State Machine

```mermaid
stateDiagram-v2
    [*] --> ParseCV
    ParseCV --> ParseJD
    ParseJD --> MatchCandidate
    MatchCandidate --> RouteCandidate

    state RouteCandidate <<choice>>
    RouteCandidate --> ScreenCandidate: score ≥ 0.7\n(strong match)
    RouteCandidate --> ReviewCandidate: 0.4 ≤ score < 0.7\n(needs review)
    RouteCandidate --> RejectCandidate: score < 0.4\n(poor match)

    ScreenCandidate --> GenerateOutreach
    ReviewCandidate --> GenerateOutreach: approved
    ReviewCandidate --> RejectCandidate: declined

    GenerateOutreach --> [*]
    RejectCandidate --> [*]

    note right of MatchCandidate
        Uses RAG pipeline (Pillar 3)
        to score CV against JD.
        Score + reasoning stored in state.
    end note

    note right of RouteCandidate
        Conditional edge in LangGraph.
        Routing function inspects
        match_score in state.
    end note
```

**Teaching points**:
- Every node reads from and writes to `RecruitmentState` — a TypedDict that flows through the graph. The state at each step is serialised for the frontend's step-through debugger.
- Conditional routing is the core agentic concept: the graph makes decisions based on intermediate results, not a hardcoded sequence.
- Each node is a plain Python function decorated with `@observe`. No magic — just functions, state, and edges.

### 4c. Guardrails Validator — Layered Execution

```mermaid
graph TB
    Input["Input Text +<br/>Pipeline Context"]

    subgraph "Layer 1 — Synchronous · Zero Cost"
        PII["pii.detect()<br/><i>Regex: email, phone,<br/>NI number, address</i>"]
        BudgetCheck["budget.check()<br/><i>Token count ≤ limit?<br/>Cost ≤ budget?</i>"]
        Timeout["timeout.check()<br/><i>Elapsed < max?</i>"]
        Schema["schema.validate()<br/><i>Output matches<br/>Pydantic model?</i>"]
    end

    subgraph "Layer 2 — Asynchronous · Low Cost"
        Relevance["relevance.score()<br/><i>Retrieved chunks<br/>relevant to query?</i>"]
        ContextUtil["context.utilisation()<br/><i>Response uses<br/>provided context?</i>"]
    end

    subgraph "Layer 3 — LLM-as-Judge · Sampled"
        Faith["faithfulness.check()<br/><i>Response grounded<br/>in context? (0–1)</i>"]
        Complete["completeness.check()<br/><i>All key points<br/>addressed?</i>"]
        Sampling["sampling_gate()<br/><i>Run on N% of<br/>requests</i>"]
    end

    Result["GuardrailResult<br/><i>passed: bool<br/>layer_results: dict<br/>flags: list<br/>cost: float</i>"]

    Input --> PII & BudgetCheck & Timeout & Schema
    PII & BudgetCheck & Timeout & Schema -->|"All pass?"| Relevance & ContextUtil
    Relevance & ContextUtil -->|"All pass?"| Sampling
    Sampling -->|"Selected"| Faith & Complete
    Sampling -->|"Not selected"| Result
    Faith & Complete --> Result

    PII -->|"🚫 PII found"| Result
    BudgetCheck -->|"🚫 Over budget"| Result

    style PII fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style BudgetCheck fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Timeout fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Schema fill:#1e293b,stroke:#22d3ee,stroke-width:2px,color:#e2e8f0
    style Relevance fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#e2e8f0
    style ContextUtil fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#e2e8f0
    style Faith fill:#1e293b,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style Complete fill:#1e293b,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
    style Sampling fill:#1e293b,stroke:#a78bfa,stroke-width:2px,color:#e2e8f0
```

**Teaching points**:
- **Cost-proportional checking**: Layer 1 is free (regex, arithmetic), Layer 2 is cheap (embedding similarity), Layer 3 is expensive (LLM calls). We only spend more money when cheaper checks have passed.
- **Fail-fast**: If Layer 1 catches PII, we never run Layers 2 or 3. This is the same principle as short-circuit evaluation.
- **Sampling**: Layer 3 runs on a configurable percentage of requests (e.g., 10%). In production, you can't afford to LLM-judge every response — but you need enough coverage to catch systematic issues. The sampling rate is a tunable knob exposed in the API.

---

## Data Flow: End-to-End Request

**What this shows**: A single request flowing through the entire system — from user action to response. This ties all four C4 levels together.

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant W as Web (Next.js)
    participant A as API (FastAPI)
    participant DB as PostgreSQL
    participant V as Voyage AI
    participant C as Claude API
    participant L as Langfuse

    U->>W: Upload CV, select JD, click "Match"
    W->>A: POST /agents/run {cv_text, jd_text}

    Note over A,L: Trace started — all steps nested under parent span

    A->>L: Create trace (workflow start)

    rect rgb(30, 41, 59)
        Note over A: Node: parse_cv
        A->>C: Parse CV → structured output
        C-->>A: CandidateProfile (Pydantic)
        A->>L: Span: parse_cv (tokens, cost, latency)
    end

    rect rgb(30, 41, 59)
        Note over A: Node: parse_jd
        A->>C: Parse JD → structured output
        C-->>A: JobRequirements (Pydantic)
        A->>L: Span: parse_jd
    end

    rect rgb(30, 41, 59)
        Note over A: Node: match_candidate (RAG)
        A->>V: Embed JD requirements
        V-->>A: Query vector
        A->>DB: pgvector similarity search
        DB-->>A: Top-k CV chunks
        A->>C: Rerank chunks for relevance
        C-->>A: Reranked results
        A->>C: Generate match assessment
        C-->>A: MatchAssessment (score + reasoning)
        A->>L: Span: match_candidate (nested: embed, retrieve, rerank, generate)
    end

    rect rgb(30, 41, 59)
        Note over A: Node: route_candidate
        alt score ≥ 0.7
            Note over A: → screen_candidate → generate_outreach
            A->>C: Screen candidate
            A->>C: Draft outreach email
        else score < 0.4
            Note over A: → reject_candidate
        end
        A->>L: Span: route + downstream nodes
    end

    rect rgb(15, 23, 42)
        Note over A: Guardrails (post-processing)
        A->>A: Layer 1: PII check, budget check
        A->>A: Layer 2: relevance score
        opt Sampled (10%)
            A->>C: Layer 3: faithfulness judge
        end
        A->>L: Span: guardrails
    end

    A->>L: Close trace (total cost, total latency)
    A-->>W: WorkflowResponse {steps[], final_output, trace_id, cost}
    W-->>U: Render: graph animation, state inspector, results
```

**This diagram demonstrates**:
- Every external call is traced in Langfuse with token counts and costs
- The agent workflow (Pillar 4) internally uses the RAG pipeline (Pillar 3), which uses embeddings (Pillar 2) and documents (Pillar 1)
- Guardrails (Pillar 7) run as post-processing on the agent's output
- The frontend receives enough data to render the full step-through experience
- Structured outputs (Pillar 9) are used throughout — every LLM response is parsed into a Pydantic model
- Error handling (Pillar 10) wraps every external call (not shown for clarity, but retry/fallback/circuit-breaker surround each API call)
