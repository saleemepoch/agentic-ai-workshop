"use client";

import { ApiError } from "@/lib/api";

interface ErrorBannerProps {
  error: unknown;
  onDismiss?: () => void;
}

interface ProviderError {
  provider: string;
  type: string;
  message: string;
  user_action: string | null;
}

function parseError(error: unknown): {
  title: string;
  message: string;
  action: string | null;
  variant: "error" | "warning";
} {
  if (error instanceof ApiError) {
    // Try to parse the structured provider error envelope
    try {
      const parsed = JSON.parse(error.detail) as { error?: ProviderError };
      const providerError = parsed.error;
      if (providerError && providerError.provider) {
        const providerLabel =
          providerError.provider === "anthropic"
            ? "Anthropic / Claude"
            : providerError.provider === "voyage_ai"
              ? "Voyage AI"
              : providerError.provider;
        const typeLabel = providerError.type
          .replace(/_/g, " ")
          .replace(/\b\w/g, (l) => l.toUpperCase());
        return {
          title: `${providerLabel}: ${typeLabel}`,
          message: providerError.message,
          action: providerError.user_action,
          variant: error.status === 429 ? "warning" : "error",
        };
      }
    } catch {
      // Not JSON, fall through to plain message
    }
    return {
      title: `Request failed (HTTP ${error.status})`,
      message: error.detail || error.message,
      action: null,
      variant: "error",
    };
  }

  if (error instanceof Error) {
    return {
      title: "Error",
      message: error.message,
      action: null,
      variant: "error",
    };
  }

  return {
    title: "Unknown error",
    message: String(error),
    action: null,
    variant: "error",
  };
}

export function ErrorBanner({ error, onDismiss }: ErrorBannerProps) {
  if (!error) return null;
  const { title, message, action, variant } = parseError(error);

  const colours =
    variant === "warning"
      ? {
          border: "border-yellow-500/40",
          bg: "bg-yellow-500/10",
          icon: "text-yellow-500",
          title: "text-yellow-500",
        }
      : {
          border: "border-red-500/40",
          bg: "bg-red-500/10",
          icon: "text-red-500",
          title: "text-red-500",
        };

  return (
    <div className={`rounded-xl border ${colours.border} ${colours.bg} p-4`}>
      <div className="flex items-start gap-3">
        <svg
          className={`h-5 w-5 shrink-0 ${colours.icon}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <div className="flex-1 min-w-0">
          <div className={`text-sm font-semibold ${colours.title}`}>{title}</div>
          <p className="mt-1 text-xs text-foreground whitespace-pre-wrap break-words">{message}</p>
          {action && (
            <div className="mt-3 rounded-lg border border-border bg-background/50 p-2 text-xs text-muted">
              <span className="font-semibold text-foreground">What to do: </span>
              {action}
            </div>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-muted hover:text-foreground transition-colors"
            aria-label="Dismiss"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
