"""
Pillar 6: Evaluation Pipeline

Measures and tracks AI system quality over time using a golden dataset
and quantitative metrics. The pipeline runs the full RAG/matching flow
against known-good test cases and scores the results.

Key components:
- Golden dataset: hand-labelled CV/JD pairs with expected outcomes
- Retrieval metrics: precision@k, recall@k, MRR
- LLM-as-judge: faithfulness and relevance scoring
- Evaluation runner: orchestrates runs, persists results

Interview talking points:
- Why a golden dataset? Non-deterministic systems need deterministic tests.
  The golden dataset is the ground truth — when a test fails, you know the
  system regressed, not that the test is wrong.
- Why LLM-as-judge? Manual quality review doesn't scale. Using Claude to
  score faithfulness and relevance gives you automated quality gates that
  can run in CI.
- Why persist results? To track trends. A single eval run tells you "it's
  working now." Persisted results tell you "it's been getting better/worse
  since Tuesday." That's the difference between testing and monitoring.

See ADR-006 for the evaluation pipeline design.
"""
