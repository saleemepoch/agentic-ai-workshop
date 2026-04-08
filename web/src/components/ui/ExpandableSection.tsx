"use client";

import { useState, ReactNode } from "react";

interface ExpandableSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function ExpandableSection({ title, defaultOpen = false, children }: ExpandableSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-3 text-left hover:bg-surface-hover transition-colors"
      >
        <span className="text-sm font-semibold text-foreground">{title}</span>
        <svg
          className={`h-4 w-4 text-muted transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="border-t border-border p-5">{children}</div>}
    </div>
  );
}
