"""
Pillar 9: Structured Outputs & Validation

Reliable typed data from LLMs via Pydantic schemas + parse-validate-retry pipeline.

LLMs return free text by default. For production, you need structured data.
This pillar shows how to:
1. Define expected output schemas as Pydantic models
2. Send schema descriptions to the LLM in the prompt
3. Parse responses and validate against the schema
4. Retry with error feedback when validation fails

Interview talking points:
- Why not use Anthropic's tool use mode? Because the parse-validate-retry
  pattern is universal — even with tool use you still need validation.
  Teaching the underlying pattern transfers across providers.
- Why retry with error feedback? Because LLMs can correct their own mistakes
  when told what went wrong. Including the validation error in the retry
  prompt has dramatically higher success rates than just retrying with the
  same prompt.
- How many retries? Default 2 (3 total attempts). More than that and you're
  usually wasting tokens — if it can't be fixed in 3 attempts, the prompt
  itself is wrong.

See ADR-009 for the structured outputs decision.
"""
