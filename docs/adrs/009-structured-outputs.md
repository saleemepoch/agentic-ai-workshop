# ADR-009: Structured Outputs & Validation

## Status
Accepted

## Context

LLMs return free text by default. For most production use cases, you need typed, structured data: a parsed CV, a match assessment, a screening decision. Free text is unreliable — the LLM might add commentary, change field names, omit fields, or return malformed JSON.

We need a system that:
1. Tells the LLM what structure to return
2. Parses and validates the response
3. Handles malformed responses gracefully (retry with feedback)

## Options Considered

### Option A: Pydantic models + parse-validate-retry pipeline
- Define expected output schemas as Pydantic models
- Send the schema description to the LLM in the prompt
- Parse the response into the Pydantic model
- On validation failure, retry with the error message as feedback
- **Pro**: Type safety, clear schemas, automatic validation, retry recovers from transient failures
- **Con**: Each retry costs another LLM call

### Option B: Anthropic's tool use / structured output mode
- Use Claude's native tool calling to enforce a JSON schema
- **Pro**: Provider-enforced structure. Less likely to fail validation.
- **Con**: Provider-specific. Hides the parse/retry mechanics that we want to teach.

### Option C: Constrained generation (grammar-based)
- Use grammar-constrained decoding to force valid output
- **Pro**: Cannot produce invalid output
- **Con**: Not available in cloud LLM APIs. Only works with self-hosted models.

## Decision

**Option A** (Pydantic + parse-validate-retry).

## Rationale

- **Teaching value**: The parse-validate-retry pattern is the production-grade approach. Even with tool use, you still need validation and retry — providers can return tool calls with invalid arguments. The pattern is universal.
- **Provider agnostic**: Pydantic schemas work with any LLM provider. If we add a fallback to GPT or open-source models in Pillar 10, the same validation logic works.
- **Demonstrable failure modes**: We can deliberately trigger validation failures (e.g., a malformed schema in the prompt) to show the retry pipeline in action. This is a teaching feature.
- **Pydantic v2 is fast**: Validation overhead is microseconds. Not a performance concern.

## Consequences

- Each retry is another LLM call. The retry budget is configurable (default: 2 retries, total 3 attempts).
- The retry feedback prompt includes the validation error verbatim — the LLM uses this to fix its output.
- Schemas live in `src/structured/output_models.py` and are reused across pillars where applicable.
- The frontend can demonstrate the full flow: raw response → validation error → retry → success.

## Two-Tier Parsing: When to Use What

There are two ways to parse JSON from an LLM in this codebase, and they cover different needs:

### Tier 1: Lightweight — `src/utils/llm_json.py`

A small shared helper with `strip_code_fences()` and `parse_llm_json(text, fallback=None)`. Use this when:

- You don't need a full Pydantic schema for the output
- You're happy with a fallback value on parse failure (no retry)
- You're inside a hot path where retry latency would be unacceptable (e.g., the reranker)

This helper centralises the one fix that bites every LLM JSON caller: stripping markdown code fences. Haiku in particular tends to wrap output in ` ```json ... ``` ` even when explicitly asked not to. We had this bug in five places independently (reranker, score_match, extract_requirements, llm_judge.faithfulness, llm_judge.relevance) before extracting the helper. The lesson: any time you find yourself writing `json.loads(response.content[0].text)`, reach for `parse_llm_json` instead.

### Tier 2: Heavy-duty — `src/structured/parser.py`

The full parse-validate-retry pipeline with Pydantic schemas. Use this when:

- The output structure has constraints worth validating (field types, value ranges, required fields)
- Retry-with-error-feedback is worth the extra LLM calls
- The caller is interactive and can wait for the retry chain
- You want the full attempt history for debugging or display

The Pillar 9 frontend demo uses this tier to make the parse-validate-retry flow visible. Most production code in the workshop uses Tier 1 because the retry overhead isn't worth it for steps that already have a sensible fallback.

Both tiers use `strip_code_fences` under the hood — Tier 2 inherits the same robustness that Tier 1 provides.

## Retry Strategy

```
Attempt 1: Send prompt → Parse → Validate → ✓ → Return
                                          → ✗ → Continue

Attempt 2: Send prompt + error feedback → Parse → Validate → ✓ → Return
                                                            → ✗ → Continue

Attempt 3: Send prompt + last error → Parse → Validate → ✓ → Return
                                                       → ✗ → Raise
```

After 3 failed attempts, raise an exception. The caller can handle this via the resilience layer (Pillar 10).

## Output Schemas

- `CandidateProfile`: parsed CV with name, summary, experience, education, skills
- `JobRequirements`: parsed JD with title, responsibilities, requirements, nice-to-haves
- `MatchAssessment`: score, reasoning, strengths, gaps
- `ScreeningDecision`: decision, justification, screening questions
- `OutreachEmail`: subject, body, tone

Each schema is a Pydantic model with field constraints (min/max lengths, allowed values, etc.).
