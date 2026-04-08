import { HTMLAttributes } from "react";

type Variant = "default" | "success" | "warning" | "error" | "info";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const variantClasses: Record<Variant, string> = {
  default: "bg-surface-hover text-muted",
  success: "bg-green-500/15 text-green-500",
  warning: "bg-yellow-500/15 text-yellow-500",
  error: "bg-red-500/15 text-red-500",
  info: "bg-accent-soft text-accent",
};

export function Badge({ variant = "default", className = "", children, ...props }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
