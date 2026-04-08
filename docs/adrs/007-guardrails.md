# ADR-007: Guardrails & Safety

## Status
Accepted

## Context

AI systems can fail in ways that traditional software can't:
- **Hallucination**: making up facts not in the context
- **PII leakage**: exposing personal data in responses
- **Cost blowout**: a single request consuming the daily budget
- **Bias**: systematic unfairness in outputs
- **Context poisoning**: malicious input manipulating the model

These failures need detection and prevention at multiple layers. The challenge: each layer has a cost. Running an LLM-as-judge on every response is expensive. Running regex PII detection is essentially free. We need a strategy that proportions cost to risk.

## Options Considered

### Option A: Layered (cost-proportional) approach
Three layers, each more expensive than the last:
- **Layer 1 (sync, zero-cost)**: regex PII detection, budget enforcement, timeout, output schema validation
- **Layer 2 (async, low-cost)**: retrieval relevance scoring, context utilisation check
- **Layer 3 (LLM-as-judge, sampled)**: faithfulness check, completeness check — runs on a sample of requests

Run cheap checks on every request. Run expensive checks only when cheaper checks pass and only on a sample.

### Option B: Pipeline approach
All checks run on every request in a linear pipeline. Simple, but doesn't scale — running LLM-as-judge on every response is prohibitively expensive in production.

### Option C: Off-the-shelf framework
Use Guardrails AI or NVIDIA NeMo Guardrails. Less code to write, industry-standard tooling. But:
- Hides the internals — defeats the teaching purpose. You can't explain *how* guardrails work if a library does it for you.
- Adds an opinionated framework dependency.

## Decision

**Option A (layered, cost-proportional)**.

Option C (off-the-shelf framework) is documented as "considered but rejected because this is a teaching platform that needs visible internals."

## Rationale

- **Cost-proportional checking is the production pattern**. Showing users how to think about the cost of safety — not just whether to add guardrails, but where to spend the safety budget — is the most valuable lesson in this pillar.
- **Layered design is testable**. Each layer can be tested in isolation. Layer 1 has no dependencies, Layer 2 needs vector retrieval, Layer 3 needs an LLM. The boundaries are clear.
- **Sampling makes Layer 3 affordable**. Running LLM-as-judge on 10% of requests gives you statistical confidence that quality is holding without paying for every single check.
- **Fail-fast saves money**. If Layer 1 catches PII, we never run Layers 2 or 3. The cheapest check that catches the issue is the only check that runs.

## Failure Taxonomy

The guardrails address these failure modes:

| Failure | Layer | Detection |
|---------|-------|-----------|
| PII leakage | 1 | Regex (email, phone, NI number, address) |
| Cost blowout | 1 | Token count + pricing → budget check |
| Timeout | 1 | Per-request timer |
| Schema violation | 1 | Pydantic validation |
| Irrelevant retrieval | 2 | Embedding similarity threshold |
| Underused context | 2 | Token-overlap heuristic |
| Hallucination | 3 | LLM-as-judge faithfulness scoring |
| Incomplete answer | 3 | LLM-as-judge completeness scoring |

## Consequences

- The guardrails validator orchestrates all layers — a single entry point that's easy to enable/disable per request
- Layer 3 sampling rate is configurable (default 10%) — production teams tune this based on risk tolerance and budget
- Each layer returns structured results so the frontend can show what each layer found
- PII detection uses UK-specific patterns (NI numbers) plus international patterns (email, phone)
- Adding new guardrails means adding to one of the three layers, not creating a new system

## Architecture

```
Input + Pipeline Context
    ↓
┌───────────────────────────────────────┐
│ Layer 1 (sync, free)                  │
│ pii.detect() · budget.check()         │
│ timeout.check() · schema.validate()   │
└─────────────┬─────────────────────────┘
              ↓ (all pass?)
┌───────────────────────────────────────┐
│ Layer 2 (async, cheap)                │
│ relevance.score() · context.use()     │
└─────────────┬─────────────────────────┘
              ↓ (all pass?)
              ↓ sampling_gate (10%)
┌───────────────────────────────────────┐
│ Layer 3 (LLM judge, expensive)        │
│ faithfulness.check() · completeness   │
└─────────────┬─────────────────────────┘
              ↓
        GuardrailResult
```

If any layer fails, downstream layers don't run.
