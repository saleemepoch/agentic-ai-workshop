"""
Matching service: business logic for embedding, retrieval, and search.

Orchestrates the embedding client and pgvector retriever.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.documents.models import Chunk
from src.matching.embedder import embedding_client
from src.matching.retriever import compare_distance_metrics, search_similar_chunks
from src.matching.schemas import (
    MetricComparisonResponse,
    SearchResponse,
    SearchResult,
)


async def embed_and_store_chunk(session: AsyncSession, chunk_id: int) -> list[float]:
    """Embed a single chunk and store the vector in the database."""
    result = await session.execute(select(Chunk).where(Chunk.id == chunk_id))
    chunk = result.scalar_one_or_none()
    if chunk is None:
        raise ValueError(f"Chunk {chunk_id} not found")

    vector = embedding_client.embed_text(chunk.content)

    await session.execute(
        update(Chunk).where(Chunk.id == chunk_id).values(embedding=vector)
    )
    await session.commit()
    return vector


async def embed_all_chunks(
    session: AsyncSession,
    document_id: int | None = None,
    strategy: str = "semantic",
) -> int:
    """Embed all un-embedded chunks, optionally filtered by document and strategy.

    Uses batch embedding for efficiency — sends multiple chunks in one API call.

    Returns the number of chunks embedded.
    """
    query = select(Chunk).where(Chunk.embedding.is_(None))
    if document_id is not None:
        query = query.where(Chunk.document_id == document_id)
    if strategy:
        query = query.where(Chunk.strategy == strategy)

    result = await session.execute(query)
    chunks = list(result.scalars().all())

    if not chunks:
        return 0

    # Batch embed for efficiency
    texts = [c.content for c in chunks]
    vectors = embedding_client.embed_batch(texts, input_type="document")

    # Store vectors
    for chunk, vector in zip(chunks, vectors):
        await session.execute(
            update(Chunk).where(Chunk.id == chunk.id).values(embedding=vector)
        )

    await session.commit()
    return len(chunks)


async def search(
    session: AsyncSession,
    query: str,
    top_k: int = 5,
    distance_metric: str = "cosine",
    doc_type: str | None = None,
) -> SearchResponse:
    """Embed a query and search for similar chunks."""
    query_vector = embedding_client.embed_query(query)

    results = await search_similar_chunks(
        session, query_vector, top_k, distance_metric, doc_type
    )

    return SearchResponse(
        query=query,
        distance_metric=distance_metric,
        results=[SearchResult(**r) for r in results],
        total_results=len(results),
    )


async def compare_metrics(
    session: AsyncSession,
    query: str,
    top_k: int = 5,
    doc_type: str | None = None,
) -> MetricComparisonResponse:
    """Search with all three distance metrics and return comparative results."""
    query_vector = embedding_client.embed_query(query)

    metric_results = await compare_distance_metrics(
        session, query_vector, top_k, doc_type
    )

    return MetricComparisonResponse(
        query=query,
        cosine=[SearchResult(**r) for r in metric_results["cosine"]],
        euclidean=[SearchResult(**r) for r in metric_results["euclidean"]],
        inner_product=[SearchResult(**r) for r in metric_results["inner_product"]],
    )
