/**
 * Typed API client for the FastAPI backend.
 *
 * One method per endpoint. All methods are async and throw on non-2xx responses.
 */

import type {
  BudgetCheckResponse,
  ChunkingComparisonResponse,
  CircuitBreakerState,
  CostSummary,
  DocumentResponse,
  EmbeddingResponse,
  EvalRunResult,
  FallbackDemoResponse,
  GoldenCase,
  GraphStructureResponse,
  GuardrailFullResponse,
  HealthResponse,
  MetricComparisonResponse,
  ModelsResponse,
  ParseResultResponse,
  PIICheckResponse,
  PromptComparisonResponse,
  PromptDetail,
  PromptSummary,
  RAGPipelineResponse,
  RetryDemoResponse,
  SchemaInfo,
  SearchResponse,
  WorkflowResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(
      `Request failed: ${response.status}`,
      response.status,
      detail,
    );
  }

  return response.json() as Promise<T>;
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });

export const api = {
  // Common
  health: () => get<HealthResponse>("/health"),

  // Pillar 1: Documents
  documents: {
    list: () => get<DocumentResponse[]>("/documents"),
    get: (id: number) => get<DocumentResponse>(`/documents/${id}`),
    create: (data: { title: string; content: string; doc_type: "cv" | "jd" }) =>
      post<DocumentResponse>("/documents", data),
    chunk: (id: number, body: { strategy: "semantic" | "naive"; max_tokens?: number; overlap_tokens?: number }) =>
      post(`/documents/${id}/chunk`, body),
    compare: (id: number, body: { max_tokens?: number; overlap_tokens?: number }) =>
      post<ChunkingComparisonResponse>(`/documents/${id}/compare`, body),
  },

  // Pillar 2: Embeddings & Retrieval
  embeddings: {
    embed: (text: string, input_type: "document" | "query" = "document") =>
      post<EmbeddingResponse>("/embeddings/embed", { text, input_type }),
    search: (body: { query: string; top_k?: number; distance_metric?: string; doc_type?: string | null }) =>
      post<SearchResponse>("/embeddings/search", body),
    compareMetrics: (body: { query: string; top_k?: number; doc_type?: string | null }) =>
      post<MetricComparisonResponse>("/embeddings/compare-metrics", body),
    embedAll: () => post<{ embedded_count: number }>("/embeddings/embed-all", {}),
  },

  // Pillar 3: RAG
  rag: {
    run: (body: { query: string; top_k?: number; distance_metric?: string; doc_type?: string | null }) =>
      post<RAGPipelineResponse>("/embeddings/rag/run", body),
  },

  // Pillar 4: Agents
  agents: {
    run: (body: { cv_text: string; jd_text: string }) => post<WorkflowResponse>("/agents/run", body),
    graph: () => get<GraphStructureResponse>("/agents/graph"),
  },

  // Pillar 5: Observability
  observability: {
    traces: (limit = 20) => get<{ traces: unknown[]; total: number }>(`/observability/traces?limit=${limit}`),
    costSummary: () => get<CostSummary>("/observability/costs/summary"),
    models: () => get<ModelsResponse>("/observability/models"),
  },

  // Pillar 6: Evaluation
  evaluation: {
    run: () => post<EvalRunResult>("/evaluation/run"),
    results: () => get<EvalRunResult>("/evaluation/results"),
    history: () => get<{ runs: EvalRunResult[]; total_runs: number }>("/evaluation/results/history"),
    golden: () => get<{ cases: GoldenCase[]; total_cases: number }>("/evaluation/golden"),
  },

  // Pillar 7: Guardrails
  guardrails: {
    checkPII: (text: string) => post<PIICheckResponse>("/guardrails/check/pii", { text }),
    checkBudget: (body: { model: string; input_tokens: number; output_tokens: number; max_cost_usd?: number }) =>
      post<BudgetCheckResponse>("/guardrails/check/budget", body),
    checkFaithfulness: (body: { context: string; response: string }) =>
      post<{ score: number; reasoning: string; passed: boolean; threshold: number }>(
        "/guardrails/check/faithfulness", body,
      ),
    checkFull: (body: {
      response_text: string;
      query?: string;
      context?: string;
      input_tokens?: number;
      output_tokens?: number;
      retrieval_scores?: number[];
      enable_layer_3?: boolean;
      layer_3_sample_rate?: number;
    }) => post<GuardrailFullResponse>("/guardrails/check", body),
    config: () => get("/guardrails/config"),
  },

  // Pillar 8: Prompts
  prompts: {
    list: () => get<{ prompts: PromptSummary[]; total: number }>("/prompts"),
    get: (name: string) => get<PromptDetail>(`/prompts/${name}`),
    render: (name: string, body: { version?: number; variables: Record<string, string> }) =>
      post<{ name: string; version: number; rendered: string }>(`/prompts/${name}/render`, body),
    compare: (body: {
      name: string;
      version_a: number;
      version_b: number;
      variables: Record<string, string>;
    }) => post<PromptComparisonResponse>("/prompts/compare", body),
  },

  // Pillar 9: Structured Outputs
  structured: {
    schemas: () => get<{ schemas: SchemaInfo[]; total: number }>("/structured/schemas"),
    parse: (body: { schema_name: string; prompt: string; max_tokens?: number }) =>
      post<ParseResultResponse>("/structured/parse", body),
  },

  // Pillar 10: Resilience
  resilience: {
    demoRetry: (body: { fail_first_n: number; max_attempts: number; base_delay: number }) =>
      post<RetryDemoResponse>("/resilience/demo/retry", body),
    demoFallback: (body: { providers: string[]; fail_until_index: number }) =>
      post<FallbackDemoResponse>("/resilience/demo/fallback", body),
    demoCircuitBreaker: (body: { service: string; fail: boolean }) =>
      post<{ called: boolean; rejected_by_breaker: boolean; result?: string; error?: string; breaker_state: CircuitBreakerState }>(
        "/resilience/demo/circuit-breaker", body,
      ),
    breakerState: () => get<{ breakers: Record<string, CircuitBreakerState> }>("/resilience/circuit-breaker/state"),
    breakerReset: () => post("/resilience/circuit-breaker/reset"),
  },
};

export { ApiError };
