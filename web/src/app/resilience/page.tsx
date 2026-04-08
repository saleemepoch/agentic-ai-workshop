"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  CircuitBreakerState,
  FallbackDemoResponse,
  RetryDemoResponse,
} from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExpandableSection } from "@/components/ui/ExpandableSection";
import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { PillarHeader } from "@/components/pillar/PillarHeader";

export default function ResiliencePage() {
  const [retryFailN, setRetryFailN] = useState(2);
  const [retryMax, setRetryMax] = useState(4);
  const [retryResult, setRetryResult] = useState<RetryDemoResponse | null>(null);

  const [fallbackUntil, setFallbackUntil] = useState(2);
  const [fallbackResult, setFallbackResult] = useState<FallbackDemoResponse | null>(null);

  const [breakers, setBreakers] = useState<Record<string, CircuitBreakerState>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function loadBreakers() {
    try {
      const r = await api.resilience.breakerState();
      setBreakers(r.breakers);
    } catch {
      setBreakers({});
    }
  }

  useEffect(() => {
    loadBreakers();
  }, []);

  async function runRetry() {
    setLoading(true);
    setError(null);
    try {
      setRetryResult(
        await api.resilience.demoRetry({
          fail_first_n: retryFailN,
          max_attempts: retryMax,
          base_delay: 0.2,
        }),
      );
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function runFallback() {
    setLoading(true);
    setError(null);
    try {
      setFallbackResult(
        await api.resilience.demoFallback({
          providers: ["primary_anthropic", "secondary_anthropic", "tertiary_haiku"],
          fail_until_index: fallbackUntil,
        }),
      );
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function tripBreaker(fail: boolean) {
    setLoading(true);
    setError(null);
    try {
      await api.resilience.demoCircuitBreaker({ service: "demo_service", fail });
      await loadBreakers();
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function resetBreakers() {
    await api.resilience.breakerReset();
    await loadBreakers();
  }

  const breakerStateColour = (state: string) => {
    if (state === "closed") return "success";
    if (state === "half_open") return "warning";
    return "error";
  };

  return (
    <div className="mx-auto max-w-6xl">
      <PillarHeader
        number={10}
        title="Error Handling & Fallbacks"
        description="Production AI systems fail. Retry handles transient errors. Fallback chains handle provider outages. Circuit breakers stop calls to clearly-broken services. Built from scratch — no library magic, all visible internals."
      />

      <div className="space-y-6">
        <Card title="Retry with Exponential Backoff" subtitle="Simulates a function that fails N times then succeeds">
          <div className="flex flex-wrap items-end gap-3 mb-4">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted">Fail first N attempts</span>
              <input
                type="number"
                value={retryFailN}
                onChange={(e) => setRetryFailN(Number(e.target.value))}
                className="w-20 rounded border border-border bg-background px-2 py-1 text-sm"
                min={0}
                max={5}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted">Max attempts</span>
              <input
                type="number"
                value={retryMax}
                onChange={(e) => setRetryMax(Number(e.target.value))}
                className="w-20 rounded border border-border bg-background px-2 py-1 text-sm"
                min={1}
                max={10}
              />
            </label>
            <Button onClick={runRetry} disabled={loading}>
              Run Retry
            </Button>
          </div>

          {retryResult && (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <Badge variant={retryResult.success ? "success" : "error"}>
                  {retryResult.success ? "SUCCESS" : "FAILED"}
                </Badge>
                <span className="text-xs text-muted">
                  {retryResult.total_attempts} attempt(s) over {retryResult.total_duration_seconds.toFixed(2)}s
                </span>
              </div>
              {retryResult.attempts.map((a) => (
                <div
                  key={a.attempt}
                  className={`rounded-lg border p-2 ${
                    a.success ? "border-green-500/30 bg-green-500/5" : "border-red-500/30 bg-red-500/5"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Badge variant={a.success ? "success" : "error"}>Attempt {a.attempt}</Badge>
                      <span className="text-muted">delay {a.delay_before.toFixed(2)}s</span>
                    </div>
                    <span className="text-muted">{a.error || "ok"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Fallback Chain" subtitle="Try providers in order, return first success">
          <div className="flex flex-wrap items-end gap-3 mb-4">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-muted">Fail until provider index</span>
              <input
                type="number"
                value={fallbackUntil}
                onChange={(e) => setFallbackUntil(Number(e.target.value))}
                className="w-20 rounded border border-border bg-background px-2 py-1 text-sm"
                min={0}
                max={3}
              />
            </label>
            <Button onClick={runFallback} disabled={loading}>
              Run Fallback
            </Button>
          </div>

          {fallbackResult && (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <Badge variant={fallbackResult.success ? "success" : "error"}>
                  {fallbackResult.success ? `Used: ${fallbackResult.provider_used}` : "ALL FAILED"}
                </Badge>
                <span className="text-xs text-muted">{fallbackResult.fallback_count} fallbacks</span>
              </div>
              {fallbackResult.attempts.map((a, i) => (
                <div
                  key={i}
                  className={`rounded-lg border p-2 ${
                    a.success ? "border-green-500/30 bg-green-500/5" : "border-red-500/30 bg-red-500/5"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground">{a.provider}</span>
                    <span className="text-muted">{a.error || "success"} ({a.duration_ms.toFixed(0)}ms)</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Circuit Breaker" subtitle="Click 'Trip' 3 times to open the circuit, then 'Recover' after 5s">
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <Button onClick={() => tripBreaker(true)} disabled={loading} variant="secondary">
              Trip (fail call)
            </Button>
            <Button onClick={() => tripBreaker(false)} disabled={loading}>
              Recover (success call)
            </Button>
            <Button onClick={resetBreakers} disabled={loading} variant="ghost" size="sm">
              Reset all
            </Button>
            <div className="w-full">{error !== null && <ErrorBanner error={error} onDismiss={() => setError(null)} />}</div>
          </div>

          <div className="space-y-2">
            {Object.entries(breakers).length === 0 && (
              <p className="text-xs text-muted text-center py-4">No breakers yet. Click trip/recover.</p>
            )}
            {Object.entries(breakers).map(([name, b]) => (
              <div key={name} className="rounded-lg border border-border bg-background p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-foreground">{name}</span>
                  <Badge variant={breakerStateColour(b.state)}>{b.state.toUpperCase()}</Badge>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs text-muted">
                  <div>Failures: <span className="text-foreground font-mono">{b.failure_count}</span></div>
                  <div>Threshold: <span className="text-foreground font-mono">{b.config.failure_threshold}</span></div>
                  <div>Cooldown left: <span className="text-foreground font-mono">{b.cooldown_remaining_seconds.toFixed(1)}s</span></div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <ExpandableSection title="Behind the scenes — resilience patterns">
          <div className="space-y-3 text-sm text-muted">
            <p>
              <span className="text-foreground font-semibold">Retry with backoff:</span> Doubles the delay on
              each attempt with random jitter to avoid thundering herd. Use for transient failures (5xx,
              timeouts). Don&rsquo;t retry on permanent failures (4xx, validation).
            </p>
            <p>
              <span className="text-foreground font-semibold">Fallback chain:</span> Ordered list of providers.
              Try each until one succeeds. Records which provider was used so the team knows when degraded
              service is in effect.
            </p>
            <p>
              <span className="text-foreground font-semibold">Circuit breaker:</span> Three states. Closed
              passes calls through. Open rejects all calls (no wasted retries). Half-open allows one test call
              to check recovery. Per-service state — a failing Voyage AI doesn&rsquo;t trip the Anthropic breaker.
            </p>
            <div className="rounded-lg border border-border bg-code-bg p-3 text-xs">
              See <code>src/resilience/retry.py</code>, <code>circuit_breaker.py</code>, <code>fallback.py</code>,
              and ADR-010. All built from scratch (~150 lines total) so the patterns are visible.
            </div>
          </div>
        </ExpandableSection>
      </div>
    </div>
  );
}
