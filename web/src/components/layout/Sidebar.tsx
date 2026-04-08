"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const pillars = [
  { href: "/chunking", label: "Document Processing", number: 1, icon: "doc" },
  { href: "/embeddings", label: "Embeddings & Retrieval", number: 2, icon: "vec" },
  { href: "/rag", label: "RAG Pipeline", number: 3, icon: "rag" },
  { href: "/agents", label: "Agentic Workflow", number: 4, icon: "agent" },
  { href: "/observability", label: "Observability & Cost", number: 5, icon: "obs", priority: true },
  { href: "/evaluation", label: "Evaluation Pipeline", number: 6, icon: "eval", priority: true },
  { href: "/guardrails", label: "Guardrails & Safety", number: 7, icon: "guard", priority: true },
  { href: "/prompts", label: "Prompt Engineering", number: 8, icon: "prompt", priority: true },
  { href: "/structured", label: "Structured Outputs", number: 9, icon: "struct" },
  { href: "/resilience", label: "Error Handling", number: 10, icon: "res" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-sidebar-border bg-sidebar-bg overflow-y-auto">
      <div className="p-4">
        <Link href="/" className="block mb-6">
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider">Pillars</h2>
        </Link>
        <nav className="space-y-1">
          {pillars.map((pillar) => {
            const active = pathname === pillar.href;
            return (
              <Link
                key={pillar.href}
                href={pillar.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-accent-soft text-accent font-medium"
                    : "text-muted hover:bg-surface-hover hover:text-foreground"
                }`}
              >
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded text-xs font-bold ${
                    active
                      ? "bg-accent text-white"
                      : pillar.priority
                        ? "bg-accent-soft text-accent"
                        : "bg-surface-hover text-muted"
                  }`}
                >
                  {pillar.number}
                </span>
                <span className="truncate">{pillar.label}</span>
                {pillar.priority && !active && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
