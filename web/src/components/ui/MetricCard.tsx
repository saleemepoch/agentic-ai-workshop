interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  hint?: string;
  variant?: "default" | "success" | "warning" | "error";
}

const variantClasses = {
  default: "border-border",
  success: "border-green-500/50",
  warning: "border-yellow-500/50",
  error: "border-red-500/50",
};

export function MetricCard({ label, value, unit, hint, variant = "default" }: MetricCardProps) {
  return (
    <div className={`rounded-xl border bg-surface p-4 ${variantClasses[variant]}`}>
      <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="text-2xl font-bold text-foreground">{value}</span>
        {unit && <span className="text-sm text-muted">{unit}</span>}
      </div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}
