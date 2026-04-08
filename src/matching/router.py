"""
FastAPI router for embeddings, retrieval, and RAG endpoints.

Endpoints:
- POST /embeddings/embed     — Embed a text string (returns vector)
- POST /embeddings/embed-all — Embed all un-embedded chunks
- POST /embeddings/search    — Search for similar chunks
- POST /embeddings/compare-metrics — Compare distance metrics on same query
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.matching.embedder import embedding_client
from src.matching.schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    MetricComparisonResponse,
    RAGPipelineResponse,
    RAGRequest,
    SearchRequest,
    SearchResponse,
)
from src.matching.service import compare_metrics, embed_all_chunks, search
from src.matching.rag_pipeline import rag_pipeline

router = APIRouter()


@router.post("/embed", response_model=EmbeddingResponse)
async def embed_text(body: EmbeddingRequest) -> EmbeddingResponse:
    """Embed a text string and return the vector.

    Useful for understanding what embeddings look like and for
    testing the embedding client independently of storage.
    """
    if body.input_type == "query":
        vector = embedding_client.embed_query(body.text)
    else:
        vector = embedding_client.embed_text(body.text)

    return EmbeddingResponse(
        text=body.text,
        embedding=vector,
        dimensions=len(vector),
        input_type=body.input_type,
    )


@router.post("/embed-all")
async def embed_all(
    document_id: int | None = None,
    strategy: str = "semantic",
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Embed all un-embedded chunks in the database.

    Optionally filter by document ID and chunking strategy.
    Uses batch embedding for efficiency.
    """
    count = await embed_all_chunks(session, document_id, strategy)
    return {"embedded_count": count}


@router.post("/search", response_model=SearchResponse)
async def search_chunks(
    body: SearchRequest,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """Search for chunks similar to a query.

    Embeds the query, then searches pgvector for the nearest chunks
    using the specified distance metric.
    """
    return await search(
        session, body.query, body.top_k, body.distance_metric, body.doc_type
    )


@router.post("/compare-metrics", response_model=MetricComparisonResponse)
async def compare_distance_metrics_endpoint(
    body: SearchRequest,
    session: AsyncSession = Depends(get_session),
) -> MetricComparisonResponse:
    """Search with all three distance metrics and compare results.

    This is the key teaching endpoint — shows how cosine, euclidean,
    and inner product rank the same chunks differently (or identically,
    for normalised embeddings).
    """
    return await compare_metrics(session, body.query, body.top_k, body.doc_type)


# --- Pillar 3: RAG Pipeline ---


@router.post("/rag/run", response_model=RAGPipelineResponse)
async def run_rag_pipeline(
    body: RAGRequest,
    session: AsyncSession = Depends(get_session),
) -> RAGPipelineResponse:
    """Run the full RAG pipeline with step-by-step results.

    Executes: embed query → retrieve → rerank → build prompt → generate.
    Each stage returns intermediate results so the frontend can show
    what happened at every step.
    """
    return await rag_pipeline.run(
        session,
        query=body.query,
        top_k=body.top_k,
        distance_metric=body.distance_metric,
        doc_type=body.doc_type,
    )
