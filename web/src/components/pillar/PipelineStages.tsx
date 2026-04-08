"use client";

import { useState, ReactNode } from "react";

export interface PipelineStage {
  name: string;
  label: string;
  description?: string;
  duration_ms?: number;
  status?: "pending" | "active" | "complete" | "error";
  details?: ReactNode;
}

interface PipelineStagesProps {
  stages: PipelineStage[];
}

const statusColors = {
  pending: "border-border bg-surface text-muted",
  active: "border-accent bg-accent-soft text-accent animate-pulse",
  complete: "border-green-500 bg-green-500/10 text-green-500",
  error: "border-red-500 bg-red-500/10 text-red-500",
};

export function PipelineStages({ stages }: PipelineStagesProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <div className="space-y-2">
      {stages.map((stage, idx) => {
        const status = stage.status || "complete";
        const expanded = expandedIndex === idx;
        return (
          <div
            key={`${stage.name}-${idx}`}
            className={`rounded-xl border transition-all ${statusColors[status]}`}
          >
            <button
              onClick={() => setExpandedIndex(expanded ? null : idx)}
              className="flex w-full items-center justify-between p-4 text-left"
            >
              <div className="flex items-center gap-4">
                <span className="flex h-7 w-7 items-center justify-center rounded-full border border-current text-xs font-bold">
                  {idx + 1}
                </span>
                <div>
                  <div className="font-semibold text-foreground">{stage.label}</div>
                  {stage.description && (
                    <div className="text-xs text-muted mt-0.5">{stage.description}</div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {stage.duration_ms !== undefined && (
                  <span className="text-xs text-muted font-mono">
                    {stage.duration_ms.toFixed(0)}ms
                  </span>
                )}
                {stage.details && (
                  <svg
                    className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </div>
            </button>
            {expanded && stage.details && (
              <div className="border-t border-current/20 p-4 bg-background/50">{stage.details}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
