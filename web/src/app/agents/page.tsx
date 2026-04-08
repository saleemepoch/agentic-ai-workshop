"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { GraphStructureResponse, WorkflowResponse } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { MetricCard } from "@/components/ui/MetricCard";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";
import { AgentGraph } from "@/components/pillar/AgentGraph";

const SAMPLE_CV = `SUMMARY
Senior software engineer with 8 years building distributed systems in Python.

EXPERIENCE
Senior Engineer at CloudScale, 2020-2024. Led microservices migration, reduced deployment time by 70%. Designed event-driven pipeline handling 500K events/sec.

Software Engineer at DataFlow, 2016-2020. Built REST APIs for 2M daily users with Django and FastAPI. Implemented Redis caching layer.

EDUCATION
BSc Computer Science, University of Edinburgh, 2016.

SKILLS
Python, Go, Kubernetes, PostgreSQL, Kafka, Redis, Docker, AWS, Terraform.`;

const SAMPLE_JD = `JOB TITLE
Senior Backend Engineer

COMPANY
TechVentures — Series B startup building developer tools.

RESPONSIBILITIES
Design scalable backend services. Lead technical architecture. Mentor junior engineers.

REQUIREMENTS
5+ years backend development. Strong Python skills. Distributed systems experience. Cloud infrastructure (AWS/GCP).

NICE TO HAVE
Kubernetes experience. Open source contributions.`;

export default function AgentsPage() {
  const [graph, setGraph] = useState<GraphStructureResponse | null>(null);
  const [cvText, setCvText] = useState(SAMPLE_CV);
  const [jdText, setJdText] = useState(SAMPLE_JD);
  const [result, setResult] = useState<WorkflowResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(-1);

  useEffect(() => {
    api.agents.graph().then(setGraph).catch(() => setGraph(null));
  }, []);

  async function runWorkflow() {
    setLoading(true);
    setError(null);
    setResult(null);
    setActiveStepIndex(-1);
    try {
      const response = await api.agents.run({ cv_text: cvText, jd_text: jdText });
      setResult(response);
      setActiveStepIndex(0);
      let i = 0;
      const interval = setInterval(() => {
        i++;
        if (i >= response.steps.length) {
          setActiveStepIndex(response.steps.length - 1);
          clearInterval(interval);
        } else {
          setActiveStepIndex(i);
        }
      }, 500);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  const visitedNodes = result
    ? result.steps.slice(0, activeStepIndex + 1).map((s) => s.node)
    : [];
  const activeNode = activeStepIndex >= 0 && result ? result.steps[activeStepIndex]?.node : null;

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={4}
        title="Agentic Workflow"
        description="LangGraph state machine. Each node is a function that reads from and writes to a typed state. Conditional routing based on intermediate results — that is what makes this 'agentic'."
      />

      <div className="space-y-6">
        {graph && (
          <Card title="Recruitment Workflow Graph" subtitle="Live state machine — runs animate through nodes">
            <AgentGraph
              graph={graph}
              activeNode={activeNode}
              visitedNodes={visitedNodes}
              routeDecision={result?.route_decision || null}
            />
          </Card>
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card title="Candidate CV" subtitle="The CV to evaluate">
            <textarea
              value={cvText}
              onChange={(e) => setCvText(e.target.value)}
              rows={10}
              className="w-full rounded-lg border border-border bg-background p-3 font-mono text-xs focus:border-accent focus:outline-none"
            />
          </Card>
          <Card title="Job Description" subtitle="The role to match against">
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={10}
              className="w-full rounded-lg border border-border bg-background p-3 font-mono text-xs focus:border-accent focus:outline-none"
            />
          </Card>
        </div>

        <div className="flex items-center gap-3">
          <Button onClick={runWorkflow} disabled={loading || !cvText || !jdText}>
            {loading ? "Running workflow..." : "Run Agent Workflow"}
          </Button>
          <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
        </div>

        {result && (
          <>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard
                label="Match score"
                value={result.match_score.toFixed(2)}
                variant={result.match_score >= 0.7 ? "success" : result.match_score >= 0.4 ? "warning" : "error"}
              />
              <MetricCard label="Route decision" value={result.route_decision} />
              <MetricCard label="Total tokens" value={result.total_tokens.toLocaleString()} />
              <MetricCard label="Cost" value={`$${result.total_cost.toFixed(4)}`} />
            </div>

            <Card title="Match Assessment" subtitle="LLM-generated evaluation of fit">
              <p className="text-sm text-foreground mb-4">{result.match_reasoning}</p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs text-muted uppercase tracking-wider mb-2">Strengths</p>
                  <ul className="space-y-1">
                    {result.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-foreground flex gap-2">
                        <span className="text-green-500">✓</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs text-muted uppercase tracking-wider mb-2">Gaps</p>
                  <ul className="space-y-1">
                    {result.gaps.map((g, i) => (
                      <li key={i} className="text-sm text-foreground flex gap-2">
                        <span className="text-yellow-500">!</span>
                        <span>{g}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </Card>

            <Card title="Execution Trace" subtitle="The agent picks the right tool for each step — regex, embedding, vector search, LLM, or pure logic">
              <div className="space-y-2">
                {result.steps.map((step, i) => {
                  const toolColours: Record<string, string> = {
                    regex: "bg-cyan-500/15 text-cyan-500",
                    embedding: "bg-purple-500/15 text-purple-500",
                    vector_search: "bg-amber-500/15 text-amber-500",
                    llm: "bg-blue-500/15 text-blue-500",
                    logic: "bg-slate-500/15 text-slate-400",
                  };
                  const toolClass = step.tool ? toolColours[step.tool] || "bg-surface-hover text-muted" : "bg-surface-hover text-muted";
                  return (
                    <button
                      key={i}
                      onClick={() => setActiveStepIndex(i)}
                      className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors ${
                        activeStepIndex === i
                          ? "border-accent bg-accent-soft"
                          : "border-border bg-background hover:bg-surface-hover"
                      }`}
                    >
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-hover text-xs font-bold text-foreground">
                        {i + 1}
                      </span>
                      {step.tool && (
                        <span className={`rounded px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider ${toolClass}`}>
                          {step.tool}
                        </span>
                      )}
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-foreground">{step.node}</div>
                        <div className="text-xs text-muted">{step.description}</div>
                      </div>
                      {step.decision && <Badge variant="info">{step.decision}</Badge>}
                      {typeof step.cost_usd === "number" && step.cost_usd > 0 && (
                        <span className="text-xs text-muted font-mono">${step.cost_usd.toFixed(4)}</span>
                      )}
                      <span className="text-xs text-muted font-mono">{step.duration_ms.toFixed(0)}ms</span>
                    </button>
                  );
                })}
              </div>
            </Card>

            {result.cv_was_cached && (
              <Card title="Dedup Hit">
                <p className="text-sm text-muted">
                  This CV was found by content hash — document <code>#{result.cv_document_id}</code> already
                  existed with chunks and embeddings. The agent reused them, skipping the chunk and embed steps
                  entirely. Run the same CV twice to see this optimisation in action.
                </p>
              </Card>
            )}

            {result.jd_requirements && result.jd_requirements.length > 0 && (
              <Card title="Extracted Requirements" subtitle="LLM consolidated these from across the JD sections">
                <ul className="space-y-1">
                  {result.jd_requirements.map((r, i) => (
                    <li key={i} className="text-sm text-foreground flex gap-2">
                      <span className="text-accent">→</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {result.retrieved_chunks && result.retrieved_chunks.length > 0 && (
              <Card title="Retrieved Evidence" subtitle="CV chunks pgvector retrieved as most relevant to the requirements">
                <div className="space-y-2">
                  {result.retrieved_chunks.map((c) => (
                    <div key={c.chunk_id} className="rounded-lg border border-border bg-background p-3">
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="info">chunk #{c.chunk_id}</Badge>
                        <span className="text-xs text-muted font-mono">
                          similarity {(c.similarity * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-xs text-foreground whitespace-pre-wrap">{c.content}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {result.outreach_email && (
              <Card title="Generated Outreach Email" subtitle="Pipeline output for strong matches">
                <div className="space-y-2">
                  <div className="text-xs text-muted">Subject</div>
                  <div className="text-sm font-semibold text-foreground">
                    {String(result.outreach_email.subject || "")}
                  </div>
                  <div className="text-xs text-muted mt-3">Body</div>
                  <div className="text-sm text-foreground whitespace-pre-wrap rounded-lg bg-code-bg border border-border p-3">
                    {String(result.outreach_email.body || "")}
                  </div>
                </div>
              </Card>
            )}

            {result.rejection_reason && (
              <Card title="Rejection Reason">
                <p className="text-sm text-foreground">{result.rejection_reason}</p>
              </Card>
            )}

            <ExpandableSection title="Parsed CV (structured)">
              <CodeBlock>{JSON.stringify(result.parsed_cv, null, 2)}</CodeBlock>
            </ExpandableSection>
            <ExpandableSection title="Parsed JD (structured)">
              <CodeBlock>{JSON.stringify(result.parsed_jd, null, 2)}</CodeBlock>
            </ExpandableSection>
          </>
        )}

        <ExpandableSection title="Behind the scenes — LangGraph state machine">
          <div className="space-y-3 text-sm text-muted">
            <p>
              Each node is a plain Python function that takes <code>RecruitmentState</code> (a TypedDict) and
              returns partial state updates. LangGraph merges them. The routing function inspects state
              (specifically <code>match_score</code>) and decides which node runs next.
            </p>
            <p>
              <span className="text-foreground font-semibold">Conditional routing</span> is the agentic concept:
              the graph makes runtime decisions, not just executing a hardcoded sequence. Score ≥ 0.4 routes to
              screening, score &lt; 0.4 routes to rejection.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/agents/graph.py</code>, <code>src/agents/nodes.py</code>, and ADR-004.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
