import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="flex h-14 items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-lg font-bold text-foreground">Agentic AI Workshop</span>
        </Link>
        <div className="flex items-center gap-4">
          <a
            href="/health"
            className="text-sm text-muted hover:text-foreground transition-colors"
          >
            API
          </a>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
