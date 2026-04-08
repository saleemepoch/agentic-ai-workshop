"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { MetricComparisonResponse, SearchResult } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

const SAMPLE_QUERIES = [
  "Senior Python backend developer with API experience",
  "Data scientist with machine learning expertise",
  "UX designer for B2B SaaS products",
  "DevOps engineer with Kubernetes experience",
];

function ResultRow({ result, rank }: { result: SearchResult; rank: number }) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge variant="info">#{rank}</Badge>
          <span className="text-xs font-semibold text-foreground truncate">{result.document_title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted">d={result.distance.toFixed(4)}</span>
          <Badge variant={result.similarity > 0.7 ? "success" : result.similarity > 0.4 ? "warning" : "default"}>
            {(result.similarity * 100).toFixed(1)}%
          </Badge>
        </div>
      </div>
      <p className="text-xs text-muted line-clamp-2">{result.content}</p>
    </div>
  );
}

export default function EmbeddingsPage() {
  const [query, setQuery] = useState(SAMPLE_QUERIES[0]);
  const [results, setResults] = useState<MetricComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [embedding, setEmbedding] = useState<number[] | null>(null);
  const [topK, setTopK] = useState(5);

  async function runSearch() {
    setLoading(true);
    setError(null);
    try {
      const [embedResult, compareResult] = await Promise.all([
        api.embeddings.embed(query, "query"),
        api.embeddings.compareMetrics({ query, top_k: topK }),
      ]);
      setEmbedding(embedResult.embedding.slice(0, 32));
      setResults(compareResult);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function embedAll() {
    setLoading(true);
    try {
      const result = await api.embeddings.embedAll();
      alert(`Embedded ${result.embedded_count} chunks. Now run a search.`);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={2}
        title="Embeddings & Retrieval"
        description="Text becomes a 1024-dimensional vector. Similar text produces similar vectors. Compare three distance metrics on the same query — for normalised embeddings, cosine and dot product produce identical rankings."
      />

      <div className="space-y-6">
        <Card title="Search Query" subtitle="Query text gets embedded then matched against stored chunks">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => setQuery(q)}
                  className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted hover:border-accent hover:text-accent transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-accent focus:outline-none"
              placeholder="Enter a search query"
            />
            <div className="flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-xs text-muted">Top K</span>
                <input
                  type="number"
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="w-20 rounded border border-border bg-background px-2 py-1 text-sm"
                  min={1}
                  max={20}
                />
              </label>
              <Button onClick={runSearch} disabled={loading || !query.trim()}>
                {loading ? "Searching..." : "Search"}
              </Button>
              <Button variant="secondary" onClick={embedAll} disabled={loading}>
                Embed all chunks
              </Button>
              <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
            </div>
          </div>
        </Card>

        {embedding && (
          <Card title="Query Embedding" subtitle="First 32 of 1024 dimensions">
            <div className="grid grid-cols-8 gap-1 md:grid-cols-16">
              {embedding.map((v, i) => {
                const intensity = Math.abs(v) * 5;
                const colour = v >= 0
                  ? `rgba(59, 130, 246, ${Math.min(intensity, 1)})`
                  : `rgba(239, 68, 68, ${Math.min(intensity, 1)})`;
                return (
                  <div
                    key={i}
                    className="aspect-square rounded text-[8px] flex items-center justify-center font-mono text-foreground"
                    style={{ backgroundColor: colour }}
                    title={`dim ${i}: ${v.toFixed(4)}`}
                  >
                    {v.toFixed(2)}
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-muted">
              Each cell is one dimension. Blue = positive, red = negative, intensity = magnitude. The full vector has 1024 dimensions and is L2-normalised by Voyage AI.
            </p>
          </Card>
        )}

        {results && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {(["cosine", "euclidean", "inner_product"] as const).map((metric) => (
              <Card key={metric} title={metric.replace("_", " ").toUpperCase()} subtitle={`Top ${topK} results`}>
                <div className="space-y-2">
                  {results[metric].map((r, idx) => (
                    <ResultRow key={r.chunk_id} result={r} rank={idx + 1} />
                  ))}
                  {results[metric].length === 0 && (
                    <p className="text-xs text-muted text-center py-4">No results. Try &ldquo;Embed all chunks&rdquo; first.</p>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}

        <ExpandableSection title="Behind the scenes — distance metrics explained">
          <div className="space-y-4 text-sm text-muted">
            <p>
              <span className="text-foreground font-semibold">Cosine similarity</span> measures the angle between
              two vectors, ignoring magnitude. Best default for normalised embeddings (which Voyage AI produces).
              Range: -1 to 1 (we convert distance = 1 - similarity).
            </p>
            <p>
              <span className="text-foreground font-semibold">Euclidean distance</span> measures the geometric
              distance between two points in vector space. Sensitive to magnitude. Range: 0 to ∞.
            </p>
            <p>
              <span className="text-foreground font-semibold">Inner product (dot product)</span> measures
              alignment including magnitude. Equivalent to cosine for normalised vectors.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3">
              <p className="text-xs">
                Key insight: for normalised embeddings, cosine and inner product produce <em>identical rankings</em>.
                You&rsquo;ll see this in the results — the ordering is the same. See ADR-002 for the embedding model decision.
              </p>
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
