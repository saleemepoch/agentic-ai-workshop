"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { GuardrailFullResponse, PIICheckResponse } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

const PII_EXAMPLES = [
  { label: "Clean", text: "Senior backend engineer with 8 years of Python experience and a strong background in distributed systems." },
  { label: "Email leak", text: "Contact the candidate at jane.doe@example.com to schedule an interview." },
  { label: "NI number", text: "Submitted NI number AB 12 34 56 C with their application." },
  { label: "Multiple PII", text: "Reach out at john@test.com or call 07700 900123 — postcode SW1A 1AA." },
];

const FULL_CHECK_EXAMPLES = [
  {
    label: "Faithful response",
    response: "The candidate has 8 years of Python backend experience and led a microservices migration at CloudScale.",
    context: "Senior engineer at CloudScale Inc, 2020-2024. Led microservices migration. 8 years of Python.",
    query: "Does the candidate have backend experience?",
  },
  {
    label: "Hallucinated response",
    response: "The candidate has 20 years of Python experience and was the CTO of Google.",
    context: "Senior engineer at CloudScale Inc, 2020-2024. 8 years experience.",
    query: "Does the candidate have backend experience?",
  },
];

export default function GuardrailsPage() {
  const [piiText, setPiiText] = useState(PII_EXAMPLES[0].text);
  const [piiResult, setPiiResult] = useState<PIICheckResponse | null>(null);
  const [fullExample, setFullExample] = useState(FULL_CHECK_EXAMPLES[0]);
  const [fullResult, setFullResult] = useState<GuardrailFullResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function runPii() {
    setLoading(true);
    setError(null);
    try {
      setPiiResult(await api.guardrails.checkPII(piiText));
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function runFullCheck() {
    setLoading(true);
    setError(null);
    try {
      const r = await api.guardrails.checkFull({
        response_text: fullExample.response,
        context: fullExample.context,
        query: fullExample.query,
        input_tokens: 200,
        output_tokens: 100,
        retrieval_scores: [0.85, 0.7, 0.6],
        enable_layer_3: true,
        layer_3_sample_rate: 1.0,
      });
      setFullResult(r);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={7}
        title="Guardrails & Safety"
        description="Layered, cost-proportional checks. Layer 1 (sync, free): PII + budget. Layer 2 (cheap): retrieval relevance. Layer 3 (expensive, sampled): LLM-as-judge faithfulness. Fail-fast — cheaper checks short-circuit the expensive ones."
        priority
      />

      <div className="space-y-6">
        <Card title="Layer 1: PII Detection" subtitle="Regex-based detection — runs on every request, free">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {PII_EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => setPiiText(ex.text)}
                  className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted hover:border-accent hover:text-accent"
                >
                  {ex.label}
                </button>
              ))}
            </div>
            <textarea
              value={piiText}
              onChange={(e) => setPiiText(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:border-accent focus:outline-none"
            />
            <Button onClick={runPii} disabled={loading || !piiText.trim()}>
              {loading ? "Checking..." : "Run PII Check"}
            </Button>
            <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
          </div>

          {piiResult && (
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-3">
                <Badge variant={piiResult.passed ? "success" : "error"}>
                  {piiResult.passed ? "PASS" : "FAIL"}
                </Badge>
                <span className="text-sm text-muted">{piiResult.count} item(s) detected</span>
              </div>
              {piiResult.matches.length > 0 && (
                <div className="space-y-1">
                  {piiResult.matches.map((m, i) => (
                    <div key={i} className="flex items-center gap-3 rounded border border-red-500/30 bg-red-500/5 p-2 text-xs">
                      <Badge variant="error">{m.type}</Badge>
                      <code className="text-foreground font-mono">{m.value}</code>
                    </div>
                  ))}
                  <div className="mt-2 text-xs text-muted">Redacted version:</div>
                  <CodeBlock>{piiResult.redacted}</CodeBlock>
                </div>
              )}
            </div>
          )}
        </Card>

        <Card title="Full Pipeline (All 3 Layers)" subtitle="Layer 1 → Layer 2 → Layer 3 with fail-fast">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {FULL_CHECK_EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => setFullExample(ex)}
                  className={`rounded-full border px-3 py-1 text-xs ${
                    fullExample.label === ex.label
                      ? "border-accent bg-accent-soft text-accent"
                      : "border-border bg-background text-muted hover:border-accent"
                  }`}
                >
                  {ex.label}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-1 gap-3">
              <div>
                <div className="text-xs text-muted mb-1">Query</div>
                <div className="rounded border border-border bg-background p-2 text-xs text-foreground">{fullExample.query}</div>
              </div>
              <div>
                <div className="text-xs text-muted mb-1">Retrieved context</div>
                <div className="rounded border border-border bg-background p-2 text-xs text-foreground">{fullExample.context}</div>
              </div>
              <div>
                <div className="text-xs text-muted mb-1">LLM response (to validate)</div>
                <div className="rounded border border-border bg-background p-2 text-xs text-foreground">{fullExample.response}</div>
              </div>
            </div>
            <Button onClick={runFullCheck} disabled={loading}>
              {loading ? "Running guardrails..." : "Run All Layers"}
            </Button>
          </div>

          {fullResult && (
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-3">
                <Badge variant={fullResult.passed ? "success" : "error"}>
                  Overall: {fullResult.passed ? "PASS" : "FAIL"}
                </Badge>
                <span className="text-xs text-muted">Layers run: {fullResult.layers_run.join(", ") || "none"}</span>
              </div>
              {fullResult.flags.length > 0 && (
                <div className="rounded border border-red-500/30 bg-red-500/5 p-3">
                  <div className="text-xs text-muted mb-2">Flags raised</div>
                  {fullResult.flags.map((f, i) => (
                    <div key={i} className="text-xs text-red-500">• {f}</div>
                  ))}
                </div>
              )}
              <ExpandableSection title="Layer 1 results (sync, free)">
                <CodeBlock>{JSON.stringify(fullResult.layer_1_results, null, 2)}</CodeBlock>
              </ExpandableSection>
              {Object.keys(fullResult.layer_2_results).length > 0 && (
                <ExpandableSection title="Layer 2 results (async, cheap)">
                  <CodeBlock>{JSON.stringify(fullResult.layer_2_results, null, 2)}</CodeBlock>
                </ExpandableSection>
              )}
              {Object.keys(fullResult.layer_3_results).length > 0 && (
                <ExpandableSection title="Layer 3 results (LLM judge, sampled)">
                  <CodeBlock>{JSON.stringify(fullResult.layer_3_results, null, 2)}</CodeBlock>
                </ExpandableSection>
              )}
            </div>
          )}
        </Card>

        <ExpandableSection title="Behind the scenes — cost-proportional layered guardrails">
          <div className="space-y-3 text-sm text-muted">
            <p>
              <span className="text-foreground font-semibold">Why layered?</span> Not all checks cost the same.
              Regex PII detection is free. LLM-as-judge faithfulness costs ~$0.005 per check. You can&rsquo;t afford
              to run expensive checks on every request.
            </p>
            <p>
              <span className="text-foreground font-semibold">Fail-fast:</span> If Layer 1 catches PII, Layers 2
              and 3 don&rsquo;t run. The cheapest check that catches the issue is the only check that runs.
            </p>
            <p>
              <span className="text-foreground font-semibold">Sampling:</span> Layer 3 runs on a configurable
              percentage of requests (default 10%). You get statistical confidence in quality without paying
              for every check.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/guardrails/validator.py</code> and ADR-007. Off-the-shelf frameworks like
              Guardrails AI and NVIDIA NeMo Guardrails are documented as the production alternative.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
