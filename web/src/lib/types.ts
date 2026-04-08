// TypeScript types mirroring the FastAPI Pydantic schemas.
// Kept in sync manually with each pillar's schemas.py file.
// We don't use code generation to keep the workshop simple — students can read both sides.

// =============================================================================
// Pillar 1: Documents & Chunking
// =============================================================================

export interface ChunkResponse {
  id: number;
  document_id: number;
  content: string;
  chunk_index: number;
  token_count: number;
  strategy: "semantic" | "naive";
  has_embedding: boolean;
}

export interface DocumentResponse {
  id: number;
  title: string;
  content: string;
  doc_type: "cv" | "jd";
  created_at: string;
  chunks: ChunkResponse[];
}

export interface ChunkingComparisonResponse {
  document_id: number;
  document_title: string;
  semantic_chunks: ChunkResponse[];
  naive_chunks: ChunkResponse[];
  semantic_count: number;
  naive_count: number;
  semantic_avg_tokens: number;
  naive_avg_tokens: number;
}

// =============================================================================
// Pillar 2: Embeddings & Retrieval
// =============================================================================

export interface EmbeddingResponse {
  text: string;
  embedding: number[];
  dimensions: number;
  input_type: string;
}

export interface SearchResult {
  chunk_id: number;
  document_id: number;
  content: string;
  chunk_index: number;
  token_count: number;
  strategy: string;
  document_title: string;
  doc_type: string;
  distance: number;
  similarity: number;
}

export interface SearchResponse {
  query: string;
  distance_metric: string;
  results: SearchResult[];
  total_results: number;
}

export interface MetricComparisonResponse {
  query: string;
  cosine: SearchResult[];
  euclidean: SearchResult[];
  inner_product: SearchResult[];
}

// =============================================================================
// Pillar 3: RAG Pipeline
// =============================================================================

export interface RAGStageResult {
  stage: string;
  description: string;
  data: Record<string, unknown>;
  duration_ms: number;
}

export interface RAGPipelineResponse {
  query: string;
  stages: RAGStageResult[];
  final_output: string;
  total_duration_ms: number;
  total_tokens: number;
  total_cost: number;
}

// =============================================================================
// Pillar 4: Agentic Workflow
// =============================================================================

export interface WorkflowStepResult {
  node: string;
  description: string;
  duration_ms: number;
  decision: string | null;
  // "regex" | "embedding" | "vector_search" | "llm" | "logic"
  tool?: string | null;
  cost_usd?: number | null;
}

export interface RetrievedChunkResponse {
  chunk_id: number;
  document_id: number;
  content: string;
  similarity: number;
}

export interface WorkflowResponse {
  parsed_cv: Record<string, unknown>;
  parsed_jd: Record<string, unknown>;
  cv_document_id?: number | null;
  cv_was_cached?: boolean;
  jd_requirements?: string[];
  retrieved_chunks?: RetrievedChunkResponse[];
  match_score: number;
  match_reasoning: string;
  strengths: string[];
  gaps: string[];
  route_decision: string;
  screening_result: Record<string, unknown> | null;
  rejection_reason: string | null;
  outreach_email: Record<string, unknown> | null;
  steps: WorkflowStepResult[];
  total_tokens: number;
  total_cost: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "process" | "decision" | "terminal";
  tool?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface GraphStructureResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// =============================================================================
// Pillar 5: Observability
// =============================================================================

export interface ModelPricing {
  input_cost_per_m_tokens: number;
  output_cost_per_m_tokens: number;
}

export interface ModelsResponse {
  llm_models: Record<string, ModelPricing>;
  embedding_models: Record<string, number>;
}

export interface CostSummary {
  total_cost_usd: number;
  total_llm_cost_usd: number;
  total_embedding_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_embedding_tokens: number;
  request_count: number;
  avg_cost_per_request_usd: number;
}

// =============================================================================
// Pillar 6: Evaluation
// =============================================================================

export interface CaseResult {
  case_id: string;
  scenario: string;
  match_score: number;
  expected_range: number[];
  score_in_range: boolean;
  expected_outcome: string;
  actual_outcome: string;
  outcome_correct: boolean;
  faithfulness_score: number;
  relevance_score: number;
  duration_ms: number;
}

export interface EvalRunResult {
  run_id: string;
  timestamp: string;
  case_results: CaseResult[];
  aggregate_metrics: {
    total_cases: number;
    scores_in_expected_range: number;
    score_accuracy: number;
    outcomes_correct: number;
    outcome_accuracy: number;
    avg_faithfulness: number;
    avg_relevance: number;
  };
  total_duration_ms: number;
}

export interface GoldenCase {
  id: string;
  scenario: string;
  description: string;
  expected_match_range: number[];
  expected_outcome: string;
  expected_keywords: string[];
  cv_preview: string;
  jd_preview: string;
}

// =============================================================================
// Pillar 7: Guardrails
// =============================================================================

export interface PIIMatch {
  type: string;
  value: string;
  start: number;
  end: number;
}

export interface PIICheckResponse {
  passed: boolean;
  count: number;
  matches: PIIMatch[];
  redacted: string;
}

export interface BudgetCheckResponse {
  passed: boolean;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  config: {
    max_input_tokens: number;
    max_output_tokens: number;
    max_cost_usd: number;
  };
  violations: string[];
}

export interface GuardrailFullResponse {
  passed: boolean;
  layer_1_results: Record<string, unknown>;
  layer_2_results: Record<string, unknown>;
  layer_3_results: Record<string, unknown>;
  flags: string[];
  layers_run: string[];
  total_cost_usd: number;
}

// =============================================================================
// Pillar 8: Prompts
// =============================================================================

export interface PromptVersionMeta {
  version: number;
  created: string;
  notes: string;
  template?: string;
}

export interface PromptSummary {
  name: string;
  description: string;
  variables: string[];
  version_count: number;
  latest_version: number;
  versions: PromptVersionMeta[];
}

export interface PromptDetail extends PromptSummary {
  versions: Required<PromptVersionMeta>[];
}

export interface PromptComparisonResponse {
  prompt_name: string;
  version_a: {
    version: number;
    notes: string;
    rendered: string;
    output: string;
    input_tokens: number;
    output_tokens: number;
  };
  version_b: {
    version: number;
    notes: string;
    rendered: string;
    output: string;
    input_tokens: number;
    output_tokens: number;
  };
}

// =============================================================================
// Pillar 9: Structured Outputs
// =============================================================================

export interface ParseAttempt {
  attempt: number;
  raw_response: string;
  success: boolean;
  parsed: Record<string, unknown> | null;
  error: string | null;
  input_tokens: number;
  output_tokens: number;
}

export interface ParseResultResponse {
  success: boolean;
  parsed: Record<string, unknown> | null;
  attempts: ParseAttempt[];
  total_attempts: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

export interface SchemaInfo {
  name: string;
  model_name: string;
  description: string;
  json_schema: Record<string, unknown>;
}

// =============================================================================
// Pillar 10: Resilience
// =============================================================================

export interface RetryAttempt {
  attempt: number;
  delay_before: number;
  error: string | null;
  success: boolean;
}

export interface RetryDemoResponse {
  success: boolean;
  value: string | null;
  attempts: RetryAttempt[];
  total_attempts: number;
  final_error: string | null;
  total_duration_seconds: number;
}

export interface FallbackAttempt {
  provider: string;
  success: boolean;
  error: string | null;
  duration_ms: number;
}

export interface FallbackDemoResponse {
  success: boolean;
  provider_used: string | null;
  attempts: FallbackAttempt[];
  fallback_count: number;
}

export interface CircuitBreakerState {
  name: string;
  state: "closed" | "open" | "half_open";
  failure_count: number;
  success_count: number;
  config: {
    failure_threshold: number;
    cooldown_seconds: number;
    success_threshold: number;
  };
  cooldown_remaining_seconds: number;
}

// =============================================================================
// Common
// =============================================================================

export interface HealthResponse {
  status: string;
  service: string;
}
