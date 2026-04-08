interface CodeBlockProps {
  children: string;
  language?: string;
  className?: string;
}

export function CodeBlock({ children, language, className = "" }: CodeBlockProps) {
  return (
    <pre
      className={`overflow-x-auto rounded-lg bg-code-bg p-4 text-xs text-foreground border border-border ${className}`}
    >
      {language && (
        <div className="text-muted text-[10px] uppercase tracking-wider mb-2">{language}</div>
      )}
      <code className="font-mono whitespace-pre-wrap break-words">{children}</code>
    </pre>
  );
}
