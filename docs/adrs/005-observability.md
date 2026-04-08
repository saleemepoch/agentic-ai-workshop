# ADR-005: Observability & Cost Management

## Status
Accepted

## Context

Production AI systems are expensive and opaque. A single RAG request can involve multiple LLM calls (reranking, generation, judging), embedding API calls, and database queries. Without observability, you can't answer:
- "How much does a single match cost?"
- "Which pipeline stage is the bottleneck?"
- "Is the system getting slower over time?"
- "Did that prompt change improve or degrade quality?"

We need tracing, cost tracking, and latency analysis across every AI operation in the workshop.

## Options Considered

### Option A: Langfuse
- Purpose-built for LLM observability
- Trace hierarchy: traces → spans → generations (nested)
- Built-in cost tracking from token usage
- Prompt management and versioning
- Python decorator (`@observe`) for minimal-friction integration
- Cloud-hosted or self-hosted
- **Pro**: LLM-native, understands token costs, prompt versioning, evaluation integration
- **Con**: Another SaaS dependency (cloud version)

### Option B: OpenTelemetry + Jaeger/Grafana
- Industry-standard distributed tracing
- Vendor-neutral, works with any backend (Jaeger, Zipkin, Grafana Tempo)
- **Pro**: Industry standard, no AI-specific lock-in, free self-hosted
- **Con**: Not LLM-aware. Doesn't understand tokens, costs, or prompt versions natively. You'd need to build all AI-specific instrumentation yourself.

### Option C: LangSmith (LangChain)
- LangChain's native observability platform
- **Pro**: Tight LangGraph integration, automatic tracing
- **Con**: LangChain ecosystem lock-in. The workshop should teach general concepts, not vendor-specific tooling.

### Option D: Custom logging
- Structured JSON logs with token counts and timing
- **Pro**: No dependencies, full control
- **Con**: No UI, no trace hierarchy, no cost aggregation. Building a dashboard from scratch is out of scope.

## Decision

**Langfuse** (Option A), cloud-hosted.

## Rationale

- **LLM-native**: Langfuse understands the AI-specific concerns (tokens, costs, prompt versions) that generic tracing tools don't. This saves us from building custom instrumentation.
- **Decorator-based**: The `@observe` decorator wraps any function with tracing. Minimal code change to add observability to existing functions.
- **Cost tracking**: Langfuse automatically calculates costs from token usage and model pricing. This directly answers "how much does a match cost?" — a question every stakeholder asks.
- **Teaching value**: Langfuse's trace UI is immediately understandable. Clicking a trace shows the full call tree with timing and costs. This teaches what observability looks like in practice, not just in theory.
- **Cloud-hosted**: We use Langfuse Cloud to avoid adding another Docker container. The workshop's infrastructure story is already covered by Postgres/API/Web. API keys are sufficient.

## Consequences

- All LLM calls must be wrapped with `@observe` — this is a non-negotiable convention
- Langfuse adds ~1ms overhead per span (negligible for AI workloads)
- Cost tracking depends on Langfuse's model pricing database being up to date
- Traces are sent asynchronously to Langfuse Cloud — no impact on request latency
- The observability endpoints (`/observability/*`) proxy Langfuse data for the frontend rather than having the frontend call Langfuse directly

## Trace Hierarchy

```
Trace: "RAG Pipeline - match query"
├── Span: "embed_query" (Voyage AI)
│   └── tokens: 0 (embedding, not token-counted)
├── Span: "retrieve" (pgvector)
│   └── duration: 12ms
├── Span: "rerank" 
│   ├── Generation: "rerank_chunk_0" (Claude)
│   ├── Generation: "rerank_chunk_1" (Claude)
│   └── Generation: "rerank_chunk_2" (Claude)
├── Span: "build_prompt"
│   └── token_budget: {system: 500, context: 3000, generation: 1000}
└── Generation: "generate" (Claude)
    ├── input_tokens: 2100
    ├── output_tokens: 450
    └── cost: $0.0138
```

Each level provides visibility: trace = full request, span = pipeline stage, generation = individual LLM call.

## What We Track

1. **Per-request**: total cost, total latency, token breakdown, model used
2. **Per-stage**: latency, tokens, cost for each pipeline stage
3. **Aggregates**: average cost per match, P50/P95 latency, total spend
4. **Prompt versions**: which prompt version was used, enabling A/B comparison
