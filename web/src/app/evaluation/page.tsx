"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { EvalRunResult, GoldenCase } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { MetricCard } from "@/components/ui/MetricCard";
import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

export default function EvaluationPage() {
  const [golden, setGolden] = useState<GoldenCase[]>([]);
  const [result, setResult] = useState<EvalRunResult | null>(null);
  const [history, setHistory] = useState<EvalRunResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.evaluation.golden().then((d) => setGolden(d.cases)).catch(() => setGolden([]));
    api.evaluation.history().then((h) => setHistory(h.runs)).catch(() => setHistory([]));
  }, []);

  async function runEval() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.evaluation.run();
      setResult(r);
      const h = await api.evaluation.history();
      setHistory(h.runs);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={6}
        title="Evaluation Pipeline"
        description="Hand-labelled golden dataset, retrieval metrics (precision/recall/MRR), and LLM-as-judge scoring. The only way to know if your AI system is getting better or worse over time."
        priority
      />

      <div className="space-y-6">
        <Card title="Golden Dataset" subtitle={`${golden.length} hand-labelled CV/JD pairs`}>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {golden.map((c) => (
              <div key={c.id} className="rounded-lg border border-border bg-background p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-foreground">{c.scenario}</span>
                  <Badge variant={c.expected_outcome === "strong_match" ? "success" : c.expected_outcome === "no_match" ? "error" : "warning"}>
                    {c.expected_outcome}
                  </Badge>
                </div>
                <p className="text-xs text-muted">{c.description}</p>
                <p className="mt-2 text-xs text-muted font-mono">
                  Expected score: {c.expected_match_range[0]} – {c.expected_match_range[1]}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <div className="flex items-center gap-3">
          <Button onClick={runEval} disabled={loading}>
            {loading ? "Running evaluation..." : "Run Full Evaluation"}
          </Button>
          <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
          <span className="text-xs text-muted">Runs all golden cases through the agent workflow + LLM-as-judge. Takes ~1-3 mins.</span>
        </div>

        {result && (
          <>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard
                label="Score accuracy"
                value={`${(result.aggregate_metrics.score_accuracy * 100).toFixed(0)}%`}
                hint={`${result.aggregate_metrics.scores_in_expected_range}/${result.aggregate_metrics.total_cases} in expected range`}
                variant={result.aggregate_metrics.score_accuracy >= 0.8 ? "success" : "warning"}
              />
              <MetricCard
                label="Outcome accuracy"
                value={`${(result.aggregate_metrics.outcome_accuracy * 100).toFixed(0)}%`}
                hint={`${result.aggregate_metrics.outcomes_correct}/${result.aggregate_metrics.total_cases} correct`}
                variant={result.aggregate_metrics.outcome_accuracy >= 0.8 ? "success" : "warning"}
              />
              <MetricCard
                label="Avg faithfulness"
                value={result.aggregate_metrics.avg_faithfulness.toFixed(2)}
                hint="LLM-as-judge"
              />
              <MetricCard
                label="Avg relevance"
                value={result.aggregate_metrics.avg_relevance.toFixed(2)}
                hint="LLM-as-judge"
              />
            </div>

            <Card title="Per-Case Results" subtitle="Drill into each test case">
              <div className="space-y-2">
                {result.case_results.map((c) => (
                  <div
                    key={c.case_id}
                    className={`rounded-lg border p-3 ${
                      c.outcome_correct
                        ? "border-green-500/30 bg-green-500/5"
                        : "border-red-500/30 bg-red-500/5"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-foreground">{c.scenario}</span>
                        <Badge variant={c.outcome_correct ? "success" : "error"}>
                          {c.outcome_correct ? "PASS" : "FAIL"}
                        </Badge>
                      </div>
                      <span className="text-xs text-muted font-mono">{c.duration_ms.toFixed(0)}ms</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-muted">Score:</span>{" "}
                        <span className="font-mono text-foreground">{c.match_score.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-muted">Expected:</span>{" "}
                        <span className="font-mono text-foreground">{c.expected_range[0]}-{c.expected_range[1]}</span>
                      </div>
                      <div>
                        <span className="text-muted">Faithful:</span>{" "}
                        <span className="font-mono text-foreground">{c.faithfulness_score.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-muted">Relevant:</span>{" "}
                        <span className="font-mono text-foreground">{c.relevance_score.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}

        {history.length > 0 && (
          <Card title="Evaluation History" subtitle={`${history.length} previous runs — track quality trends`}>
            <div className="space-y-2">
              {history.slice().reverse().map((h) => (
                <div key={h.run_id} className="flex items-center justify-between rounded border border-border bg-background p-2 text-xs">
                  <span className="font-mono text-foreground">{h.run_id}</span>
                  <div className="flex gap-3">
                    <span className="text-muted">
                      Acc: <span className="text-foreground font-mono">{(h.aggregate_metrics.outcome_accuracy * 100).toFixed(0)}%</span>
                    </span>
                    <span className="text-muted">
                      Faith: <span className="text-foreground font-mono">{h.aggregate_metrics.avg_faithfulness.toFixed(2)}</span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        <ExpandableSection title="Behind the scenes — evaluation methodology">
          <div className="space-y-3 text-sm text-muted">
            <p>
              <span className="text-foreground font-semibold">Golden dataset:</span> 5 hand-labelled CV/JD pairs
              covering clear match, clear mismatch, overqualified, transferable skills, and seniority gap.
              Each case has an expected score range and expected outcome.
            </p>
            <p>
              <span className="text-foreground font-semibold">Metrics:</span> Score accuracy (did the score fall
              in the expected range?), outcome accuracy (did the routing decision match expectations?),
              faithfulness and relevance (LLM-as-judge scores).
            </p>
            <p>
              <span className="text-foreground font-semibold">Why LLM-as-judge?</span> Manual quality review
              doesn&rsquo;t scale. Using Claude to score faithfulness and relevance gives you automated quality gates
              that can run in CI.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/evaluation/runner.py</code>, <code>src/evaluation/golden_dataset.py</code>, and ADR-006.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
