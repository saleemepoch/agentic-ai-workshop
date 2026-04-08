"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PromptComparisonResponse, PromptDetail, PromptSummary } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

const SAMPLE_VARIABLES: Record<string, Record<string, string>> = {
  match_scorer: {
    candidate: "Senior Python engineer with 8 years of distributed systems experience.",
    job: "Senior Backend Engineer requiring 5+ years Python and microservices.",
  },
  cv_parser: {
    cv_text: "Jane Doe — Senior Engineer at Google 2020-2024. BSc Stanford 2020. Python, Go.",
  },
  outreach_email: {
    candidate_name: "Jane Doe",
    job_title: "Senior Backend Engineer",
    strengths: "Python, microservices, distributed systems",
    reasoning: "Strong technical match with relevant experience",
  },
};

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const [selectedName, setSelectedName] = useState<string>("");
  const [detail, setDetail] = useState<PromptDetail | null>(null);
  const [versionA, setVersionA] = useState<number>(1);
  const [versionB, setVersionB] = useState<number>(2);
  const [comparison, setComparison] = useState<PromptComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.prompts
      .list()
      .then((d) => {
        setPrompts(d.prompts);
        if (d.prompts.length > 0) setSelectedName(d.prompts[0].name);
      })
      .catch(() => setPrompts([]));
  }, []);

  useEffect(() => {
    if (!selectedName) return;
    api.prompts.get(selectedName).then(setDetail).catch(() => setDetail(null));
  }, [selectedName]);

  async function compare() {
    if (!selectedName) return;
    setLoading(true);
    setError(null);
    setComparison(null);
    try {
      const variables = SAMPLE_VARIABLES[selectedName] || {};
      const r = await api.prompts.compare({
        name: selectedName,
        version_a: versionA,
        version_b: versionB,
        variables,
      });
      setComparison(r);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={8}
        title="Prompt Engineering & Management"
        description="Prompts as first-class engineering artefacts: versioned, testable, reviewable. Local YAML templates with git as the audit trail. Run two versions side-by-side to A/B test changes."
        priority
      />

      <div className="space-y-6">
        <Card title="Available Prompts" subtitle={`${prompts.length} prompt template(s)`}>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
            {prompts.map((p) => (
              <button
                key={p.name}
                onClick={() => setSelectedName(p.name)}
                className={`rounded-lg border p-3 text-left transition-colors ${
                  selectedName === p.name
                    ? "border-accent bg-accent-soft"
                    : "border-border bg-background hover:bg-surface-hover"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-foreground">{p.name}</span>
                  <Badge>{p.version_count} versions</Badge>
                </div>
                <p className="text-xs text-muted">{p.description}</p>
              </button>
            ))}
          </div>
        </Card>

        {detail && (
          <>
            <Card title={`${detail.name} — Versions`} subtitle="Each version is a separate template with notes">
              <div className="space-y-3">
                {detail.versions.map((v) => (
                  <div key={v.version} className="rounded-lg border border-border bg-background p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="info">v{v.version}</Badge>
                        <span className="text-xs text-muted">{v.created}</span>
                      </div>
                    </div>
                    <p className="text-xs text-muted mb-2">{v.notes}</p>
                    <CodeBlock>{v.template}</CodeBlock>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="A/B Comparison" subtitle="Run the same input through two versions, compare outputs">
              <div className="flex flex-wrap items-end gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-muted">Version A</span>
                  <select
                    value={versionA}
                    onChange={(e) => setVersionA(Number(e.target.value))}
                    className="rounded border border-border bg-background px-2 py-1 text-sm"
                  >
                    {detail.versions.map((v) => (
                      <option key={v.version} value={v.version}>v{v.version}</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-muted">Version B</span>
                  <select
                    value={versionB}
                    onChange={(e) => setVersionB(Number(e.target.value))}
                    className="rounded border border-border bg-background px-2 py-1 text-sm"
                  >
                    {detail.versions.map((v) => (
                      <option key={v.version} value={v.version}>v{v.version}</option>
                    ))}
                  </select>
                </label>
                <Button onClick={compare} disabled={loading || versionA === versionB}>
                  {loading ? "Running..." : "Compare"}
                </Button>
                <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
              </div>
            </Card>

            {comparison && (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card title={`Version ${comparison.version_a.version}`} subtitle={comparison.version_a.notes}>
                  <div className="text-xs text-muted mb-2">
                    {comparison.version_a.input_tokens} in / {comparison.version_a.output_tokens} out tokens
                  </div>
                  <div className="rounded-lg border border-border bg-background p-3 text-sm text-foreground whitespace-pre-wrap">
                    {comparison.version_a.output}
                  </div>
                </Card>
                <Card title={`Version ${comparison.version_b.version}`} subtitle={comparison.version_b.notes}>
                  <div className="text-xs text-muted mb-2">
                    {comparison.version_b.input_tokens} in / {comparison.version_b.output_tokens} out tokens
                  </div>
                  <div className="rounded-lg border border-border bg-background p-3 text-sm text-foreground whitespace-pre-wrap">
                    {comparison.version_b.output}
                  </div>
                </Card>
              </div>
            )}
          </>
        )}

        <ExpandableSection title="Behind the scenes — local YAML versioning">
          <div className="space-y-3 text-sm text-muted">
            <p>
              Prompt templates live in <code>src/prompts/templates/*.yaml</code>. Each file contains multiple
              versions with notes and a template body. Variable injection uses Python&rsquo;s <code>str.format()</code>.
            </p>
            <p>
              <span className="text-foreground font-semibold">Why local YAML over Langfuse Prompt Management?</span>
              {" "}Teaching value. YAML files are obvious and inspectable. Git history is the audit trail. For
              teams that want hot-swap without redeploy, Langfuse is documented as the production alternative.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/prompts/loader.py</code>, <code>src/prompts/registry.py</code>, and ADR-008.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
