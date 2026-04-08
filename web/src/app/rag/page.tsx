"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { RAGPipelineResponse } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { MetricCard } from "@/components/ui/MetricCard";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";
import { PipelineStages, PipelineStage } from "@/components/pillar/PipelineStages";

const SAMPLE_QUERY = `Looking for a senior backend engineer with strong Python skills, experience building distributed systems, and familiarity with Kubernetes. Must have led microservices migrations or large refactoring projects.`;

export default function RagPage() {
  const [query, setQuery] = useState(SAMPLE_QUERY);
  const [topK, setTopK] = useState(5);
  const [docType, setDocType] = useState<"cv" | "jd" | "">("cv");
  const [result, setResult] = useState<RAGPipelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function runPipeline() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.rag.run({
        query,
        top_k: topK,
        distance_metric: "cosine",
        doc_type: docType || null,
      });
      setResult(response);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  const stages: PipelineStage[] = result
    ? result.stages.map((s) => ({
        name: s.stage,
        label: s.stage.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        description: s.description,
        duration_ms: s.duration_ms,
        status: "complete" as const,
        details: <CodeBlock>{JSON.stringify(s.data, null, 2)}</CodeBlock>,
      }))
    : [];

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={3}
        title="RAG Pipeline"
        description="Retrieval-augmented generation, broken open. Watch query embedding → vector search → LLM reranking → token-budgeted prompt construction → generation. Click any stage to see what it produced."
      />

      <div className="space-y-6">
        <Card title="Query" subtitle="The pipeline retrieves chunks matching this query, reranks them, then generates a grounded response">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={5}
            className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:border-accent focus:outline-none"
          />
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted">Top K</span>
              <input
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-20 rounded border border-border bg-background px-2 py-1 text-sm"
                min={1}
                max={10}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted">Filter by type</span>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value as "cv" | "jd" | "")}
                className="rounded border border-border bg-background px-2 py-1 text-sm"
              >
                <option value="">All</option>
                <option value="cv">CVs only</option>
                <option value="jd">JDs only</option>
              </select>
            </label>
            <Button onClick={runPipeline} disabled={loading || !query.trim()}>
              {loading ? "Running pipeline..." : "Run RAG Pipeline"}
            </Button>
          </div>
        </Card>

        {error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

        {result && (
          <>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard label="Total duration" value={(result.total_duration_ms / 1000).toFixed(2)} unit="s" />
              <MetricCard label="Total tokens" value={result.total_tokens.toLocaleString()} />
              <MetricCard label="Total cost" value={`$${result.total_cost.toFixed(4)}`} variant="warning" />
              <MetricCard label="Stages" value={result.stages.length} />
            </div>

            <Card title="Pipeline Stages" subtitle="Click any stage to expand its result data">
              <PipelineStages stages={stages} />
            </Card>

            <Card title="Final Generated Response" subtitle="LLM output grounded in retrieved context">
              <div className="rounded-lg bg-code-bg border border-border p-4 text-sm text-foreground whitespace-pre-wrap">
                {result.final_output}
              </div>
            </Card>
          </>
        )}

        <ExpandableSection title="Behind the scenes — RAG pipeline architecture">
          <div className="space-y-4 text-sm text-muted">
            <ol className="list-decimal list-inside space-y-2">
              <li>
                <span className="text-foreground font-semibold">Embed query</span> — Voyage AI converts the query
                text into a 1024-dim vector. Query embeddings differ from document embeddings (input_type=query).
              </li>
              <li>
                <span className="text-foreground font-semibold">Retrieve</span> — pgvector cosine search returns
                the top-k most similar chunks from the database.
              </li>
              <li>
                <span className="text-foreground font-semibold">Rerank</span> — Claude scores each chunk for
                actual relevance to the query (0-10). Re-sorts by score. Embedding similarity is a rough proxy;
                an LLM understanding the text is more accurate.
              </li>
              <li>
                <span className="text-foreground font-semibold">Build prompt</span> — Token budgeting fits the
                top-ranked chunks into the context window without exceeding the budget. Lower-ranked chunks are
                dropped first.
              </li>
              <li>
                <span className="text-foreground font-semibold">Generate</span> — Claude generates the final
                response, grounded in the retrieved context. Cost is tracked per call.
              </li>
            </ol>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/matching/rag_pipeline.py</code> and ADR-003 for the design rationale.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
