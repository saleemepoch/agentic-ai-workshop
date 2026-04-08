import { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
}

export function Card({ title, subtitle, children, className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-border bg-surface ${className}`}
      {...props}
    >
      {(title || subtitle) && (
        <div className="border-b border-border px-5 py-3">
          {title && <h3 className="text-sm font-semibold text-foreground">{title}</h3>}
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
