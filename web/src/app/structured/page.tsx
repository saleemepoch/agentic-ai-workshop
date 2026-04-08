"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ParseResultResponse, SchemaInfo } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

const SAMPLE_PROMPTS: Record<string, string> = {
  candidate_profile: `Parse this CV into structured fields:

Jane Doe — Senior Software Engineer
8 years of Python experience. Senior Engineer at CloudScale Inc 2020-2024 leading microservices migration.
BSc Computer Science, MIT, 2016. Skills: Python, Go, Kubernetes, PostgreSQL.`,
  match_assessment: `Score how well this candidate matches the job:

Candidate: Senior Python engineer with 8 years distributed systems experience.
Job: Senior Backend Engineer requiring Python and microservices.

Provide score (0.0-1.0), reasoning, strengths, and gaps.`,
  outreach_email: `Draft an outreach email for Jane Doe for the Senior Backend Engineer role at TechVentures.
Mention her Python expertise and microservices background.`,
};

export default function StructuredPage() {
  const [schemas, setSchemas] = useState<SchemaInfo[]>([]);
  const [selected, setSelected] = useState<string>("candidate_profile");
  const [prompt, setPrompt] = useState<string>(SAMPLE_PROMPTS.candidate_profile);
  const [result, setResult] = useState<ParseResultResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.structured.schemas().then((d) => setSchemas(d.schemas)).catch(() => setSchemas([]));
  }, []);

  useEffect(() => {
    if (SAMPLE_PROMPTS[selected]) {
      setPrompt(SAMPLE_PROMPTS[selected]);
    }
  }, [selected]);

  async function runParse() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.structured.parse({ schema_name: selected, prompt });
      setResult(r);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  const selectedSchema = schemas.find((s) => s.name === selected);

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={9}
        title="Structured Outputs & Validation"
        description="LLMs return free text by default. The parse-validate-retry pipeline turns that into typed Pydantic models. When validation fails, the error feedback goes back into the next attempt — most failures recover within 2 retries."
      />

      <div className="space-y-6">
        <Card title="Output Schemas" subtitle={`${schemas.length} Pydantic schemas available`}>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
            {schemas.map((s) => (
              <button
                key={s.name}
                onClick={() => setSelected(s.name)}
                className={`rounded-lg border p-3 text-left transition-colors ${
                  selected === s.name
                    ? "border-accent bg-accent-soft"
                    : "border-border bg-background hover:bg-surface-hover"
                }`}
              >
                <div className="text-sm font-semibold text-foreground">{s.model_name}</div>
                <div className="text-xs text-muted">{s.name}</div>
              </button>
            ))}
          </div>
        </Card>

        {selectedSchema && (
          <ExpandableSection title={`${selectedSchema.model_name} JSON Schema`}>
            <CodeBlock>{JSON.stringify(selectedSchema.json_schema, null, 2)}</CodeBlock>
          </ExpandableSection>
        )}

        <Card title="Prompt" subtitle="The user prompt sent to Claude — schema description is appended automatically">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:border-accent focus:outline-none"
          />
          <div className="mt-3">
            <Button onClick={runParse} disabled={loading || !prompt.trim()}>
              {loading ? "Parsing..." : "Run Parse Pipeline"}
            </Button>
            <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
          </div>
        </Card>

        {result && (
          <>
            <div className="flex items-center gap-3">
              <Badge variant={result.success ? "success" : "error"}>
                {result.success ? "PARSED" : "FAILED"}
              </Badge>
              <span className="text-xs text-muted">
                {result.total_attempts} attempt(s) · {result.total_input_tokens + result.total_output_tokens} tokens
              </span>
            </div>

            <Card title="Parse Attempts" subtitle="Each retry includes the previous error as feedback">
              <div className="space-y-3">
                {result.attempts.map((a) => (
                  <div
                    key={a.attempt}
                    className={`rounded-lg border p-3 ${
                      a.success
                        ? "border-green-500/30 bg-green-500/5"
                        : "border-red-500/30 bg-red-500/5"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={a.success ? "success" : "error"}>Attempt {a.attempt}</Badge>
                      </div>
                      <span className="text-xs text-muted font-mono">
                        {a.input_tokens + a.output_tokens} tokens
                      </span>
                    </div>
                    {a.error && (
                      <div className="text-xs text-red-500 mb-2">Error: {a.error}</div>
                    )}
                    <ExpandableSection title="Raw response">
                      <CodeBlock>{a.raw_response}</CodeBlock>
                    </ExpandableSection>
                  </div>
                ))}
              </div>
            </Card>

            {result.parsed && (
              <Card title="Validated Output" subtitle="Parsed and validated against the Pydantic schema">
                <CodeBlock>{JSON.stringify(result.parsed, null, 2)}</CodeBlock>
              </Card>
            )}
          </>
        )}

        <ExpandableSection title="Behind the scenes — parse-validate-retry pipeline">
          <div className="space-y-3 text-sm text-muted">
            <ol className="list-decimal list-inside space-y-1">
              <li>Send the user prompt + JSON schema to Claude</li>
              <li>Strip markdown code fences if present, parse JSON</li>
              <li>Validate against Pydantic model</li>
              <li>On failure: build a retry prompt that includes the validation error verbatim</li>
              <li>Repeat up to <code>max_retries</code> times (default 2 = 3 total attempts)</li>
            </ol>
            <p>
              <span className="text-foreground font-semibold">Why include the error?</span> Because LLMs can
              correct their own mistakes when told what went wrong. The success rate of retry-with-feedback is
              dramatically higher than retry-with-same-prompt.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/structured/parser.py</code>, <code>src/structured/output_models.py</code>, and ADR-009.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
