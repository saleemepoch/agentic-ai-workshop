"""
Pillar 8: Prompt Engineering & Management

Prompts as first-class engineering artefacts: versioned, testable, reviewable.

Local YAML-based prompt management. Each prompt lives in `templates/*.yaml`
with multiple versions, variable injection, and metadata. Versioning is via
git history — every prompt change is a commit with an author and message.

For teams that need remote prompt management (hot-swap without redeploy),
Langfuse Prompt Management is referenced in `src/observability/prompts.py`
as an alternative.

Interview talking points:
- Why local YAML over Langfuse? Teaching value. YAML files are obvious and
  inspectable — students can open them and read the prompt. No API call,
  no UI, no hidden state. Git history is the audit trail.
- Why versioning at all? Because prompt changes have non-obvious effects.
  Without versioning, when output quality changes, you can't tell if it's
  the model, the data, or the prompt. With versioning, you can pin a
  specific version and isolate the variable.
- How do you A/B test? Load two versions, run them through the same input,
  compare outputs side-by-side. The frontend renders the diff. The
  evaluation pipeline (Pillar 6) can score both versions against the
  golden dataset.

See ADR-008 for the prompt management decision.
"""
