"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { CostSummary, ModelsResponse } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { MetricCard } from "@/components/ui/MetricCard";
import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

export default function ObservabilityPage() {
  const [cost, setCost] = useState<CostSummary | null>(null);
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [traces, setTraces] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [c, m, t] = await Promise.all([
        api.observability.costSummary(),
        api.observability.models(),
        api.observability.traces(20),
      ]);
      setCost(c);
      setModels(m);
      setTraces(t.traces);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={5}
        title="Observability & Cost Management"
        description="Every LLM call is traced via Langfuse with token counts and costs. Without observability, you can't answer 'how much does a single match cost?' or 'which stage is the bottleneck?'"
        priority
      />

      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button onClick={loadAll} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </Button>
          <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
        </div>

        {cost && (
          <>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard
                label="Total cost"
                value={`$${cost.total_cost_usd.toFixed(4)}`}
                variant="warning"
                hint="Across all traced requests"
              />
              <MetricCard
                label="Avg per request"
                value={`$${cost.avg_cost_per_request_usd.toFixed(6)}`}
              />
              <MetricCard
                label="Total requests"
                value={cost.request_count}
              />
              <MetricCard
                label="Tokens consumed"
                value={(cost.total_input_tokens + cost.total_output_tokens).toLocaleString()}
              />
            </div>

            <Card title="Cost Breakdown" subtitle="LLM cost vs embedding cost">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <div className="text-xs text-muted uppercase tracking-wider mb-2">LLM (generation, judging)</div>
                  <div className="text-2xl font-bold text-foreground">${cost.total_llm_cost_usd.toFixed(6)}</div>
                  <div className="text-xs text-muted mt-1">
                    {cost.total_input_tokens.toLocaleString()} in / {cost.total_output_tokens.toLocaleString()} out
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase tracking-wider mb-2">Embeddings</div>
                  <div className="text-2xl font-bold text-foreground">${cost.total_embedding_cost_usd.toFixed(6)}</div>
                  <div className="text-xs text-muted mt-1">
                    {cost.total_embedding_tokens.toLocaleString()} tokens
                  </div>
                </div>
              </div>
            </Card>
          </>
        )}

        {models && (
          <Card title="Model Pricing" subtitle="Per-million-token pricing for cost calculations">
            <div className="space-y-2">
              {Object.entries(models.llm_models).map(([name, p]) => (
                <div key={name} className="flex items-center justify-between rounded-lg border border-border bg-background p-3">
                  <div>
                    <div className="text-sm font-semibold text-foreground">{name}</div>
                    <div className="text-xs text-muted">LLM</div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="text-foreground">${p.input_cost_per_m_tokens}/M input</div>
                    <div className="text-muted">${p.output_cost_per_m_tokens}/M output</div>
                  </div>
                </div>
              ))}
              {Object.entries(models.embedding_models).map(([name, price]) => (
                <div key={name} className="flex items-center justify-between rounded-lg border border-border bg-background p-3">
                  <div>
                    <div className="text-sm font-semibold text-foreground">{name}</div>
                    <div className="text-xs text-muted">Embedding</div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="text-foreground">${price}/M tokens</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        <Card title="Recent Traces" subtitle={`${traces.length} traces from Langfuse`}>
          {traces.length === 0 ? (
            <p className="text-sm text-muted text-center py-4">
              No traces yet. Run something on the RAG or Agents pages to generate traces.
            </p>
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {traces.map((t, i) => {
                const trace = t as Record<string, unknown>;
                return (
                  <div key={String(trace.id) || i} className="rounded border border-border bg-background p-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground">{String(trace.name) || "trace"}</span>
                      <span className="text-muted font-mono">{String(trace.timestamp || "").slice(0, 19)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        <ExpandableSection title="Behind the scenes — observability strategy">
          <div className="space-y-3 text-sm text-muted">
            <p>
              All LLM calls and pipeline stages are wrapped with Langfuse&rsquo;s <code>@observe</code> decorator.
              That gives us a trace tree per request: each retrieve, rerank, embed, and generate is its own span
              with timing and token counts.
            </p>
            <p>
              <span className="text-foreground font-semibold">Cost-proportional thinking:</span> Cheap operations
              (regex, arithmetic) are free. LLM calls cost real money. Tracking per-operation cost lets you find
              and fix the expensive parts.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/observability/tracing.py</code>, <code>src/observability/cost.py</code>, and ADR-005.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
