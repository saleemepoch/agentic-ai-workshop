"""
Pillar 7: Guardrails & Safety

Layered guardrails with cost-proportional checking:

- **Layer 1 (sync, zero-cost)**: PII detection, budget enforcement, timeout, schema validation
- **Layer 2 (async, low-cost)**: retrieval relevance scoring, context utilisation
- **Layer 3 (LLM-as-judge, sampled)**: faithfulness, completeness

Run cheap checks on every request. Run expensive checks only when cheaper
checks pass and only on a sample. This is how production systems balance
safety against cost.

Interview talking points:
- Why layered? Because not all checks cost the same. Regex PII detection is
  free; LLM-as-judge faithfulness costs ~$0.01 per check. You can't afford
  to run the expensive checks on every request, so you use them as a
  statistical sampling layer.
- Why fail-fast? If Layer 1 catches PII, you never run Layers 2 or 3.
  The cheapest check that catches the issue is the only check that runs.
  This is the same principle as short-circuit evaluation in code.
- Why not Guardrails AI / NeMo Guardrails? Off-the-shelf frameworks hide
  the internals — you can't teach what you can't see. See ADR-007.

See ADR-007 for the layered guardrails design.
"""
