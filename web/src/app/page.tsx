import Link from "next/link";

const pillars = [
  {
    number: 1,
    title: "Document Processing & Chunking",
    description: "Semantic vs naive chunking, token-aware splitting, section detection.",
    href: "/chunking",
  },
  {
    number: 2,
    title: "Embeddings & Retrieval",
    description: "Voyage AI embeddings, pgvector search, distance metric comparison.",
    href: "/embeddings",
  },
  {
    number: 3,
    title: "RAG Pipeline",
    description: "End-to-end retrieval-augmented generation with reranking and token budgeting.",
    href: "/rag",
  },
  {
    number: 4,
    title: "Agentic Workflow",
    description: "LangGraph state machines, conditional routing, step-through execution.",
    href: "/agents",
  },
  {
    number: 5,
    title: "Observability & Cost",
    description: "Langfuse tracing, per-request cost tracking, latency analysis.",
    href: "/observability",
    priority: true,
  },
  {
    number: 6,
    title: "Evaluation Pipeline",
    description: "Golden datasets, precision/recall/MRR, LLM-as-judge scoring.",
    href: "/evaluation",
    priority: true,
  },
  {
    number: 7,
    title: "Guardrails & Safety",
    description: "Layered guardrails, PII detection, faithfulness scoring, budget enforcement.",
    href: "/guardrails",
    priority: true,
  },
  {
    number: 8,
    title: "Prompt Engineering",
    description: "Versioned templates, A/B comparison, prompt design patterns.",
    href: "/prompts",
    priority: true,
  },
  {
    number: 9,
    title: "Structured Outputs",
    description: "Pydantic LLM schemas, parse-validate-retry pipelines.",
    href: "/structured",
  },
  {
    number: 10,
    title: "Error Handling & Fallbacks",
    description: "Retry strategies, fallback chains, circuit breakers, graceful degradation.",
    href: "/resilience",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Agentic AI Workshop
        </h1>
        <p className="mt-3 text-lg text-muted max-w-2xl">
          An interactive teaching platform for agentic AI, RAG systems, and production
          AI engineering. Each pillar below covers a core concept with working code
          and hands-on demos.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {pillars.map((pillar) => (
          <Link
            key={pillar.href}
            href={pillar.href}
            className="group relative rounded-xl border border-border bg-surface p-5 transition-all hover:border-accent hover:bg-surface-hover"
          >
            <div className="flex items-start gap-4">
              <span
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-bold ${
                  pillar.priority
                    ? "bg-accent text-white"
                    : "bg-surface-hover text-muted group-hover:bg-accent-soft group-hover:text-accent"
                }`}
              >
                {pillar.number}
              </span>
              <div>
                <h2 className="font-semibold text-foreground group-hover:text-accent transition-colors">
                  {pillar.title}
                </h2>
                <p className="mt-1 text-sm text-muted">{pillar.description}</p>
              </div>
            </div>
            {pillar.priority && (
              <span className="absolute right-4 top-4 rounded-full bg-accent-soft px-2 py-0.5 text-xs font-medium text-accent">
                Priority
              </span>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
