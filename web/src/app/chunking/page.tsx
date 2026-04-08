"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ChunkingComparisonResponse, DocumentResponse } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { MetricCard } from "@/components/ui/MetricCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

const SAMPLE_TEXT = `SUMMARY
Senior software engineer with 8 years of experience building scalable backend systems in Python and Go.

EXPERIENCE
Senior Engineer at CloudScale Inc, 2020-2024. Led the migration of a monolithic application to microservices, reducing deployment time by 70%. Designed and implemented a real-time event processing pipeline handling 500K events per second using Kafka.

Software Engineer at DataFlow Ltd, 2016-2020. Built REST APIs serving 2M daily active users using Django and FastAPI. Implemented caching layer with Redis that reduced database load by 60%.

EDUCATION
BSc Computer Science, University of Edinburgh, 2016. First Class Honours.

SKILLS
Python, Go, Kubernetes, PostgreSQL, Kafka, Redis, Docker, AWS, Terraform, gRPC.`;

export default function ChunkingPage() {
  const [text, setText] = useState(SAMPLE_TEXT);
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [comparison, setComparison] = useState<ChunkingComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [maxTokens, setMaxTokens] = useState(150);

  useEffect(() => {
    api.documents.list().then(setDocs).catch(() => setDocs([]));
  }, []);

  async function runComparison() {
    setLoading(true);
    setError(null);
    setComparison(null);
    try {
      const doc = await api.documents.create({
        title: `Chunking demo ${new Date().toISOString()}`,
        content: text,
        doc_type: "cv",
      });
      const result = await api.documents.compare(doc.id, { max_tokens: maxTokens, overlap_tokens: 30 });
      setComparison(result);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  const colours = [
    "bg-blue-500/10 border-blue-500/30",
    "bg-green-500/10 border-green-500/30",
    "bg-purple-500/10 border-purple-500/30",
    "bg-yellow-500/10 border-yellow-500/30",
    "bg-pink-500/10 border-pink-500/30",
    "bg-cyan-500/10 border-cyan-500/30",
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={1}
        title="Document Processing & Chunking"
        description="Chunking quality directly affects retrieval quality. Compare semantic (section-aware) and naive (fixed-size) strategies side-by-side. Watch what each one does at the section boundaries."
      />

      <div className="space-y-6">
        <Card title="Document Input" subtitle="Paste a CV or use the sample. Adjust max tokens to see how chunking changes.">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
            className="w-full rounded-lg border border-border bg-background p-3 font-mono text-xs text-foreground focus:border-accent focus:outline-none"
          />
          <div className="mt-4 flex flex-wrap items-end gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted">Max tokens per chunk</span>
              <input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
                className="w-24 rounded border border-border bg-background px-2 py-1 text-sm"
                min={50}
                max={500}
              />
            </label>
            <Button onClick={runComparison} disabled={loading || !text.trim()}>
              {loading ? "Chunking..." : "Compare Strategies"}
            </Button>
            <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
          </div>
        </Card>

        {comparison && (
          <>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard label="Semantic chunks" value={comparison.semantic_count} variant="success" />
              <MetricCard label="Naive chunks" value={comparison.naive_count} variant="warning" />
              <MetricCard label="Semantic avg" value={comparison.semantic_avg_tokens} unit="tokens" />
              <MetricCard label="Naive avg" value={comparison.naive_avg_tokens} unit="tokens" />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card title="Semantic Chunker" subtitle="Section-aware, sentence-bounded">
                <div className="space-y-2">
                  {comparison.semantic_chunks.map((chunk, idx) => (
                    <div
                      key={chunk.id}
                      className={`rounded-lg border p-3 ${colours[idx % colours.length]}`}
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <Badge variant="success">#{chunk.chunk_index + 1}</Badge>
                        <span className="text-xs text-muted">{chunk.token_count} tokens</span>
                      </div>
                      <p className="text-xs text-foreground whitespace-pre-wrap">{chunk.content}</p>
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Naive Chunker" subtitle="Fixed-size, no awareness">
                <div className="space-y-2">
                  {comparison.naive_chunks.map((chunk, idx) => (
                    <div
                      key={chunk.id}
                      className={`rounded-lg border p-3 ${colours[idx % colours.length]}`}
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <Badge variant="warning">#{chunk.chunk_index + 1}</Badge>
                        <span className="text-xs text-muted">{chunk.token_count} tokens</span>
                      </div>
                      <p className="text-xs text-foreground whitespace-pre-wrap">{chunk.content}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </>
        )}

        <ExpandableSection title="Behind the scenes — how the chunkers work">
          <div className="space-y-4 text-sm text-muted">
            <div>
              <p className="font-semibold text-foreground mb-1">Semantic chunker</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Detect section boundaries via regex (markdown headings, ALL CAPS, colon-terminated labels)</li>
                <li>Split text into sections at heading positions</li>
                <li>For each section: if it fits in <code>max_tokens</code>, keep it whole. Otherwise split at sentence boundaries with overlap.</li>
                <li>Never merge content across section boundaries — overlap stays within a section.</li>
              </ol>
            </div>
            <div>
              <p className="font-semibold text-foreground mb-1">Naive chunker</p>
              <p>Splits by raw token count with optional overlap. No section awareness, no sentence detection. Demonstrates why semantic chunking matters: the same content gets fragmented at arbitrary positions, mixing skills with education.</p>
            </div>
            <div className="rounded-lg border border-border bg-code-bg p-3">
              <p className="text-xs">Token counts use <code>tiktoken</code> with <code>cl100k_base</code> encoding. See <code>src/documents/chunker.py</code> and ADR-001.</p>
            </div>
          </div>
        </ExpandableSection>

        {docs.length > 0 && (
          <ExpandableSection title={`${docs.length} document(s) in database`}>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {docs.slice(0, 12).map((d) => (
                <div key={d.id} className="rounded border border-border bg-background p-2 text-xs">
                  <div className="font-semibold text-foreground truncate">{d.title}</div>
                  <div className="text-muted">{d.doc_type.toUpperCase()} · {d.chunks.length} chunks</div>
                </div>
              ))}
            </div>
          </ExpandableSection>
        )}
      </div>
    </div>
  );
}
