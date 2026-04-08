interface PillarHeaderProps {
  number: number;
  title: string;
  description: string;
  priority?: boolean;
}

export function PillarHeader({ number, title, description, priority }: PillarHeaderProps) {
  return (
    <div className="mb-8 border-b border-border pb-6">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold ${
            priority ? "bg-accent text-white" : "bg-surface-hover text-muted"
          }`}
        >
          {number}
        </span>
        <h1 className="text-2xl font-bold text-foreground">{title}</h1>
        {priority && (
          <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-medium text-accent">
            Priority Pillar
          </span>
        )}
      </div>
      <p className="mt-3 text-muted max-w-3xl">{description}</p>
    </div>
  );
}
