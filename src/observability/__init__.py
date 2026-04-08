"""
Pillar 5: Observability & Cost Management (Langfuse)

Provides tracing, cost tracking, and latency analysis for every AI operation.
The `@observe` decorator wraps functions with Langfuse tracing — every LLM call,
embedding request, and pipeline stage is traced with token counts and costs.

This pillar is cross-cutting: it instruments code across all other pillars.
The observability module itself provides:
- Langfuse client initialisation and configuration
- Cost calculation utilities
- API endpoints for fetching traces, costs, and latency data

Interview talking points:
- Why is observability non-negotiable? Because AI systems are expensive and
  non-deterministic. Without tracing, you can't debug a bad response, you can't
  answer "how much does this cost?", and you can't detect quality regression.
- Why Langfuse over OpenTelemetry? Langfuse is LLM-native — it understands
  tokens, costs, and prompt versions. OTel would require building all that
  instrumentation from scratch. See ADR-005.
- What's the overhead? ~1ms per span, sent asynchronously. Negligible for
  AI workloads where LLM calls take 500ms–5s.

See ADR-005 for the full observability decision.
"""
