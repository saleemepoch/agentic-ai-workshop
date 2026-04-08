# ADR-008: Prompt Engineering & Management

## Status
Accepted

## Context

Prompts are first-class engineering artefacts. They drive model behaviour, change model output quality dramatically, and need to be:
- **Versioned**: so you can track which prompt produced which result
- **Testable**: so you can A/B compare changes before shipping them
- **Reviewable**: so prompt changes go through code review like any other change
- **Discoverable**: so engineers can find existing prompts before writing new ones

Treating prompts as ad-hoc strings scattered through the codebase causes the same problems as scattered configuration: drift, duplication, and "who changed this?" mysteries.

## Options Considered

### Option A: Local YAML/JSON templates with versioning in git
- Prompts live in `src/prompts/templates/*.yaml`
- Each file contains a named prompt with versions, variables, and metadata
- Versioning via git history (every change is a commit)
- A/B testing by loading two versions and comparing outputs
- **Pro**: Zero external dependencies. Versioning via git is free and audit-trail-friendly. Easy to review prompt changes via PR.
- **Con**: No remote hot-swap. Changes require a deploy.

### Option B: Langfuse Prompt Management
- Prompts stored and versioned in Langfuse cloud
- Hot-swap from Langfuse UI without redeploy
- A/B testing via Langfuse experiment features
- **Pro**: Remote management, no redeploy for prompt changes. Tight integration with Langfuse tracing.
- **Con**: External dependency on Langfuse for the prompt store. Engineering changes (new prompts, new variables) still require code changes.

### Option C: Database-backed prompt store
- Store prompts in PostgreSQL
- Build a custom UI for editing
- **Pro**: Full control, no vendor lock-in
- **Con**: Lots of code to write for a problem that's already solved by Options A and B.

## Decision

**Option A** (local YAML templates with git versioning) as the primary system.

Reference Option B (Langfuse) in code comments and documentation as the production alternative for teams that need remote prompt management.

## Rationale

- **Teaching value**: YAML templates are obvious and inspectable. Students can open the file and read the prompt — no UI, no API call, no hidden state. This is the most educational approach.
- **Git is the audit trail**: Every prompt change is a commit with an author, timestamp, and message. You can `git blame` a prompt change to see why it was made. This is more powerful than most prompt management UIs.
- **A/B testing without infrastructure**: Loading two versions of a prompt and running them side-by-side is just file I/O. No API calls to a prompt store. Tests are fast and deterministic.
- **Langfuse is documented as the production alternative**: The `src/observability/prompts.py` module already has the integration. Teams that want hot-swap can switch to Langfuse without rewriting business logic.

## Consequences

- Prompt changes require a code change (PR + merge + deploy). For most teams this is desirable — prompts are part of the product, not a runtime knob.
- The template format must support variable injection. Pydantic-style `{variable}` syntax keeps it simple and IDE-friendly.
- Multiple versions of a prompt live in the same file. The "current" version is the most recent one unless an explicit version is requested.
- A/B comparison runs both versions through the same input and returns both outputs side-by-side.

## Template Format

```yaml
name: match_scorer
description: Scores how well a candidate matches a job description
versions:
  - version: 1
    created: 2025-12-01
    template: |
      Score how well this candidate matches the job from 0 to 1.
      Candidate: {candidate}
      Job: {job}
  - version: 2
    created: 2025-12-15
    template: |
      You are a recruitment expert. Evaluate this match.
      Candidate: {candidate}
      Job: {job}
      Provide score (0-1), strengths, gaps, reasoning.
```

The latest version is the default. Tests and evaluation can pin to specific versions for reproducibility.
