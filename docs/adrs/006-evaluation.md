# ADR-006: Evaluation Pipeline

## Status
Accepted

## Context

AI systems are non-deterministic — the same input can produce different outputs across runs. Without evaluation, you can't answer:
- "Is the system getting better or worse?"
- "Did that prompt change actually improve quality?"
- "Which retrieval failures are most common?"

We need a repeatable evaluation pipeline with quantitative metrics that runs against a known-good dataset.

## Options Considered

### Golden Dataset Design
**Option A: Small, hand-labelled (4–5 pairs)**
- Manually curate CV/JD pairs with expected match outcomes, retrieval expectations, and generation quality
- **Pro**: High quality labels, covers diverse scenarios intentionally, feasible to maintain
- **Con**: Small sample size

**Option B: Large, auto-generated (50+ pairs)**
- Use an LLM to generate labelled pairs
- **Pro**: More data, better statistical power
- **Con**: Circular — using an LLM to evaluate an LLM system. Labels may be unreliable

### Metrics

**Retrieval metrics** (quantify how well we find the right chunks):
- **Precision@k**: Of the k chunks retrieved, how many are relevant?
- **Recall@k**: Of all relevant chunks, how many did we retrieve?
- **MRR (Mean Reciprocal Rank)**: How high does the first relevant result rank?

**Generation metrics** (quantify how good the LLM output is):
- **Faithfulness**: Is the response grounded in the retrieved context? (Not hallucinated)
- **Relevance**: Does the response actually answer the query?

## Decision

**Option A** (small, hand-labelled dataset) with both retrieval and generation metrics.

## Rationale

- A small, carefully curated dataset catches the important failure modes. We intentionally include edge cases (overqualified candidate, transferable skills, seniority mismatch) that a random dataset might miss.
- Hand labels are trustworthy. When a test fails, you know the label is correct — the system is wrong, not the test.
- LLM-as-judge for generation metrics (faithfulness, relevance) gives us automated quality scoring without human review on every run.
- Results are persisted to the database, enabling trend tracking over time. The frontend shows whether changes improve or degrade quality.

## Consequences

- The golden dataset must be maintained as the system evolves (e.g., if we change the chunking strategy, retrieval expectations may shift).
- LLM-as-judge adds cost per eval run (~5 Claude calls for faithfulness scoring, ~5 for relevance).
- Eval runs are triggered manually or via CI — not on every request.
- Results are stored in memory in the eval router for trend tracking. Persisting to the database is a future enhancement.

## Threshold Alignment

A subtle but important coupling: the golden dataset's score ranges and outcome labels must agree with the routing thresholds in `src/agents/nodes.py:route_candidate`. We learned this the hard way when an early version had:

- `route_candidate`: score ≥ 0.7 = strong, 0.4–0.7 = partial, < 0.4 = no_match
- A golden case with `expected_match_range=(0.3, 0.7)` and `expected_outcome="partial_match"`

A score of 0.32 fell *inside* the expected range but produced `no_match` per the routing function, so the test failed for confusing reasons. The 0.30–0.40 dead zone meant the dataset and the router disagreed about what counted as a partial match.

The fix was to align both layers on **0.65 / 0.30**:

- `score >= 0.65` → strong_match (route to screen)
- `0.30 <= score < 0.65` → partial_match (route to review/screen)
- `score < 0.30` → no_match (route to reject)

These thresholds live in `src/agents/nodes.py` (`route_candidate`) and `src/evaluation/runner.py` (`_determine_outcome`). Changing one without the other reintroduces the dead zone, so they should be treated as a single decision.

## Golden Dataset Cases

Five hand-labelled cases. Each has an expected score range, expected outcome, and a description that explains *why* it's labelled that way. Score ranges were retuned alongside the threshold alignment.

1. **Clear Match**: Senior Python backend engineer CV ↔ Senior Backend Engineer JD. Expected score `0.7–1.0`, outcome `strong_match`. Tests the easy case.
2. **Clear Non-Match**: Marketing coordinator CV ↔ Senior Backend Engineer JD. Expected score `0.0–0.3`, outcome `no_match`. Tests that wildly mismatched candidates score low.
3. **Overqualified Candidate**: Staff engineer with 15 years FAANG experience ↔ Junior developer JD at a small consultancy. Expected score `0.10–0.35`, outcome `no_match`. Tests that the seniority mismatch dominates the technical-skill overlap. The technical fundamentals lift the score above zero, but the JD's "0–2 years" requirement is hard-violated.
4. **Transferable Skills**: Senior Python data scientist ↔ Senior Python backend engineer. Expected score `0.40–0.65`, outcome `partial_match`. Tests that the model credits transferable fundamentals (language, distributed systems, production ML deployment) even when the exact domain differs. This is the case that motivated the explicit "credit transferable skills" rubric in the `score_match` prompt.
5. **Seniority Gap**: Junior developer with 1 year experience ↔ Staff engineer role. Expected score `0.0–0.3`, outcome `no_match`. The mirror of case 3: the candidate is too junior, not too senior.
