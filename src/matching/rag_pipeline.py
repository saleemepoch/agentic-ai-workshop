"""
End-to-end RAG pipeline: retrieve → rerank → build prompt → generate.

This is the centrepiece of Pillar 3. Each stage is independently observable
and returns intermediate results for the frontend's step-by-step visualiser.

The pipeline demonstrates several production concerns:
1. **Token budgeting**: The context window has a fixed size. We allocate tokens
   for system prompt, retrieved context, and generation. If retrieved chunks
   exceed the context budget, we trim from the lowest-ranked chunk up.
2. **Reranking**: Raw retrieval scores are refined by an LLM judge that reads
   the actual text, not just vector distances.
3. **Staged execution**: Each stage is timed, token-counted, and returns its
   result. This enables the observability story (Pillar 5) and the frontend
   step-through experience.

Interview talking points:
- Why return intermediate results? Debuggability. In production, when a RAG
  response is wrong, you need to know *which stage* failed — was retrieval
  bad? Was reranking wrong? Was the prompt poorly constructed? Staged results
  let you pinpoint the problem.
- Why token budgeting? Because stuffing all retrieved chunks into the prompt
  is a common mistake. It wastes tokens on low-relevance content, can exceed
  the context window, and degrades generation quality. Budget forces you to
  prioritise.

See ADR-003 for pipeline design decisions.
"""

import time

import anthropic
import tiktoken
from langfuse import observe

from src.config import settings
from src.matching.embedder import embedding_client
from src.matching.reranker import reranker
from src.matching.retriever import search_similar_chunks
from src.matching.schemas import RAGPipelineResponse, RAGStageResult

from sqlalchemy.ext.asyncio import AsyncSession

_encoder = tiktoken.get_encoding("cl100k_base")

# Token budget defaults
SYSTEM_PROMPT_BUDGET = 500
CONTEXT_BUDGET = 3000
# Output tokens dominate generation latency. Capping at 500 keeps responses
# concise (3-4 short sections) and roughly halves the wall-clock time vs 1000.
# Trade-off: slightly less detail in the final answer, but for the matching
# use case the structured Match Summary / Strengths / Gaps / Recommendation
# format works well within this budget.
GENERATION_BUDGET = 500

SYSTEM_PROMPT = """You are a recruitment matching assistant. You analyse candidate CVs against job descriptions to provide detailed match assessments.

Given the retrieved context below, provide a thorough analysis of how well the candidate(s) match the requirements. Be specific — reference particular skills, experience, and qualifications from the context.

Structure your response as:
1. **Match Summary**: Overall assessment (strong match, partial match, weak match)
2. **Strengths**: Specific skills/experience that align with requirements
3. **Gaps**: Requirements not met or partially met
4. **Recommendation**: Proceed to interview, need more info, or pass"""


def _count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


class RAGPipeline:
    """Orchestrates the full RAG pipeline with staged results."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    @observe(name="rag_pipeline")
    async def run(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 5,
        distance_metric: str = "cosine",
        doc_type: str | None = None,
    ) -> RAGPipelineResponse:
        """Execute the full RAG pipeline and return staged results.

        Stages:
        1. Embed query
        2. Retrieve similar chunks
        3. Rerank chunks by relevance
        4. Build token-budgeted prompt
        5. Generate response
        """
        stages: list[RAGStageResult] = []
        total_tokens = 0
        pipeline_start = time.perf_counter()

        # --- Stage 1: Embed Query ---
        stage_start = time.perf_counter()
        query_vector = embedding_client.embed_query(query)
        stages.append(RAGStageResult(
            stage="embed_query",
            description="Convert query text to embedding vector via Voyage AI",
            data={
                "query": query,
                "dimensions": len(query_vector),
                "model": embedding_client.model,
            },
            duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
        ))

        # --- Stage 2: Retrieve ---
        stage_start = time.perf_counter()
        retrieved = await search_similar_chunks(
            session, query_vector, top_k, distance_metric, doc_type
        )
        stages.append(RAGStageResult(
            stage="retrieve",
            description=f"Search pgvector for top-{top_k} similar chunks using {distance_metric} distance",
            data={
                "distance_metric": distance_metric,
                "top_k": top_k,
                "results_count": len(retrieved),
                "results": [
                    {
                        "chunk_id": r["chunk_id"],
                        "document_title": r["document_title"],
                        "similarity": round(r["similarity"], 4),
                        "content_preview": r["content"][:150] + "...",
                    }
                    for r in retrieved
                ],
            },
            duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
        ))

        if not retrieved:
            return RAGPipelineResponse(
                query=query,
                stages=stages,
                final_output="No relevant documents found. Please upload and embed documents first.",
                total_duration_ms=round((time.perf_counter() - pipeline_start) * 1000, 2),
                total_tokens=0,
                total_cost=0.0,
            )

        # --- Stage 3: Rerank ---
        stage_start = time.perf_counter()
        reranked = await reranker.rerank(query, retrieved)
        stages.append(RAGStageResult(
            stage="rerank",
            description="Score each chunk for relevance using Claude as judge, re-sort by score",
            data={
                "reranked_results": [
                    {
                        "chunk_id": r["chunk_id"],
                        "document_title": r["document_title"],
                        "original_similarity": round(r["similarity"], 4),
                        "rerank_score": r["rerank_score"],
                        "rerank_reasoning": r["rerank_reasoning"],
                    }
                    for r in reranked
                ],
            },
            duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
        ))

        # --- Stage 4: Build Prompt ---
        stage_start = time.perf_counter()
        system_tokens = _count_tokens(SYSTEM_PROMPT)
        query_tokens = _count_tokens(query)

        # Fill context budget with top-ranked chunks
        context_chunks: list[str] = []
        context_tokens = 0
        for chunk in reranked:
            chunk_tokens = _count_tokens(chunk["content"])
            if context_tokens + chunk_tokens > CONTEXT_BUDGET:
                break
            context_chunks.append(chunk["content"])
            context_tokens += chunk_tokens

        context_text = "\n\n---\n\n".join(context_chunks)
        user_prompt = f"Query: {query}\n\nRetrieved Context:\n{context_text}"

        stages.append(RAGStageResult(
            stage="build_prompt",
            description="Construct token-budgeted prompt: fit top chunks into context window",
            data={
                "system_prompt_tokens": system_tokens,
                "context_tokens": context_tokens,
                "query_tokens": query_tokens,
                "total_prompt_tokens": system_tokens + context_tokens + query_tokens,
                "chunks_included": len(context_chunks),
                "chunks_excluded": len(reranked) - len(context_chunks),
                "context_budget": CONTEXT_BUDGET,
                "generation_budget": GENERATION_BUDGET,
            },
            duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
        ))

        # --- Stage 5: Generate ---
        stage_start = time.perf_counter()
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=GENERATION_BUDGET,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        final_output = response.content[0].text
        gen_input_tokens = response.usage.input_tokens
        gen_output_tokens = response.usage.output_tokens
        total_tokens = gen_input_tokens + gen_output_tokens

        # Approximate cost (Claude Sonnet pricing)
        input_cost = gen_input_tokens * 3.0 / 1_000_000  # $3/M input tokens
        output_cost = gen_output_tokens * 15.0 / 1_000_000  # $15/M output tokens
        total_cost = input_cost + output_cost

        stages.append(RAGStageResult(
            stage="generate",
            description="Generate response via Claude, grounded in retrieved context",
            data={
                "model": "claude-sonnet-4-20250514",
                "input_tokens": gen_input_tokens,
                "output_tokens": gen_output_tokens,
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "total_cost_usd": round(total_cost, 6),
            },
            duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
        ))

        return RAGPipelineResponse(
            query=query,
            stages=stages,
            final_output=final_output,
            total_duration_ms=round((time.perf_counter() - pipeline_start) * 1000, 2),
            total_tokens=total_tokens,
            total_cost=round(total_cost, 6),
        )


# Singleton
rag_pipeline = RAGPipeline()
