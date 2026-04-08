# ADR-003: RAG Pipeline Design

## Status
Accepted

## Context

The RAG pipeline (Pillar 3) is the core of the workshop — it ties together document chunking (Pillar 1), embeddings and retrieval (Pillar 2), and LLM generation. The pipeline must:

1. Be transparent: each stage returns intermediate results for the frontend to display
2. Be token-aware: respect the LLM's context window budget
3. Include reranking: raw retrieval results are good but not optimal

## Options Considered

### Reranking Strategy

**Option A: LLM-based reranking (Claude)**
- Send each retrieved chunk + query to Claude with a scoring prompt
- Score each chunk 0–10 for relevance, re-sort by score
- **Pro**: High quality. The LLM understands semantic relevance deeply.
- **Con**: Expensive (one LLM call per chunk). Adds latency.

**Option B: Cross-encoder reranking (e.g., Cohere Rerank)**
- Dedicated reranking API optimised for relevance scoring
- **Pro**: Purpose-built, fast, cheaper than full LLM calls.
- **Con**: Another API dependency and provider to manage.

**Option C: No reranking**
- Use retrieval scores directly.
- **Pro**: Simplest. No extra cost.
- **Con**: Embedding similarity is a rough proxy for relevance. The top-k retrieved chunks may include tangentially related content that ranks above actually relevant chunks.

### Prompt Construction

**Option D: Simple concatenation**
- Concatenate all retrieved chunks into the prompt.
- **Pro**: Simple.
- **Con**: May exceed context window. No prioritisation of chunks.

**Option E: Token-budgeted construction**
- Allocate a token budget for context. Fill from highest-ranked chunk down until budget is exhausted. Reserve tokens for system prompt and generation.
- **Pro**: Guarantees the prompt fits. Prioritises most relevant content.
- **Con**: Slightly more complex.

## Decision

**Option A** (LLM-based reranking) and **Option E** (token-budgeted prompt construction), with two performance refinements added after initial implementation:

1. **Reranking uses Claude Haiku, not Sonnet.** Reranking is a constrained scoring task with a tiny output (one number plus one sentence), which Haiku handles as well as Sonnet at ~3x the speed and ~1/4 the cost. Sonnet stays as the model for the final generation step where reasoning quality matters.

2. **Per-chunk reranking calls run in parallel via `asyncio.gather`.** The chunk scoring calls are independent — running them sequentially wastes 80% of the wall-clock time. With top_k=5, parallel reranking takes ~250ms vs sequential ~4s.

## Rationale

### Why LLM-based reranking
- Teaching value: it demonstrates that retrieval is just the first filter. Reranking is where quality comes from. The evaluation pipeline (Pillar 6) quantifies the improvement.
- Using Claude for reranking keeps the provider count at three (Anthropic, Voyage AI, Langfuse). Adding Cohere would complicate the setup for marginal benefit at our scale.
- After the Haiku + parallelisation refinements, the cost-per-rerank dropped from ~$0.025 (5 sequential Sonnet calls) to ~$0.0075 (5 parallel Haiku calls) and latency dropped from ~4s to ~250ms.

### Why Haiku for reranking, Sonnet for generation
- Different tasks deserve different model fits. Reranking is structured judgment with a tiny output ("score this 0-10"); generation is open-ended text production where Sonnet's depth shows.
- Generation is the place where the user actually sees model quality. Cheaping out there would visibly degrade the demo. Reranking is invisible plumbing where Haiku is sufficient.

### Why parallel reranking
- The independence of per-chunk scoring is structural — there's no information dependency between chunks. Sequential execution was wasted wall time, not a correctness requirement.
- Parallelisation means latency stays roughly constant as `top_k` grows (bounded by the slowest single call). Sequential execution made latency scale linearly with `top_k`.

### Why token-budgeted prompt construction
- Context window management is a critical production skill that most tutorials skip. Building it explicitly teaches users to think about token budgets — how much space for context vs generation, what happens when you stuff too much in, why truncation order matters.
- The budget is configurable: system prompt tokens + context tokens + generation tokens = total budget. Each is visible in the frontend.

### Generation budget tuning
- Output tokens dominate generation latency. The default `max_tokens` was lowered from 1000 to 500 after observing that the structured Match Summary / Strengths / Gaps / Recommendation format works comfortably within 500 tokens, and the latency saving (~3-5s on long answers) is meaningful.

## Consequences

- **Latency**: end-to-end RAG drops from ~25s (original sync Sonnet rerank + 1000-token generation) to ~12s (parallel Haiku rerank + 500-token generation), with no quality regression observed.
- **Cost**: per-request RAG cost drops from ~$0.04 to ~$0.015. The reranker accounts for most of the saving.
- **Code complexity**: the reranker is now async (`AsyncAnthropic` client + `asyncio.gather`), which means the RAG pipeline must `await` it. This propagates async-ness through the pipeline.
- **Format robustness**: Haiku is more literal about following format instructions and tends to wrap JSON in markdown code fences even when asked not to. The shared `parse_llm_json` helper (`src/utils/llm_json.py`) strips fences before parsing — see the discussion under ADR-009.
- The pipeline returns intermediate results at every stage, which increases response payload size but enables the step-by-step frontend visualisation.

## Pipeline Stages

1. **Embed query** → Voyage AI → query vector (~200ms)
2. **Retrieve** → pgvector similarity search → top-k chunks with scores (~50ms)
3. **Rerank** → Haiku scores each chunk in parallel, re-sorted by score (~250ms total)
4. **Build prompt** → token budgeting: fit top chunks into context window (~5ms)
5. **Generate** → Sonnet generates response grounded in retrieved context (~8-12s, dominated by output tokens)

Each stage is independently observable (Langfuse span) and returns its result for frontend display.
