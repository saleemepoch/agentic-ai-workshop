"""
pgvector similarity search with configurable distance metrics.

Retrieves the most similar chunks to a query vector from the database.
Supports three distance metrics for teaching purposes:
- Cosine distance (default): direction-based similarity
- Euclidean distance: geometric distance in vector space
- Inner product: alignment including magnitude

Interview talking points:
- Why support multiple metrics? Teaching. For normalised embeddings (like
  Voyage AI's output), cosine and dot product produce identical rankings.
  Showing this builds intuition about what these metrics actually measure.
- Why top-k retrieval? You can't feed the entire database to the LLM.
  Top-k retrieval selects the most relevant chunks within a token budget.
  The k parameter is a trade-off: too low misses relevant context, too
  high wastes tokens on irrelevant content.
- What about HNSW indexes? For our dataset size, exact search is fine.
  At scale (100K+ vectors), you'd add an HNSW index for approximate
  nearest neighbour search — trading slight accuracy for major speed gains.

See ADR-002 for vector storage decisions.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.documents.models import Chunk


# pgvector operators for each distance metric
DISTANCE_OPERATORS = {
    "cosine": "<=>",       # Cosine distance (1 - cosine_similarity)
    "euclidean": "<->",    # L2 distance
    "inner_product": "<#>", # Negative inner product (for ORDER BY ASC)
}


async def search_similar_chunks(
    session: AsyncSession,
    query_vector: list[float],
    top_k: int = 5,
    distance_metric: str = "cosine",
    doc_type: str | None = None,
    document_id: int | None = None,
) -> list[dict]:
    """Find the most similar chunks to a query vector.

    Args:
        session: Database session.
        query_vector: The query embedding vector (1024 dimensions).
        top_k: Number of results to return.
        distance_metric: One of "cosine", "euclidean", "inner_product".
        doc_type: Optional filter by document type ("cv" or "jd").
        document_id: Optional filter to a specific source document. Used by
            the agent's match_candidate node to retrieve only chunks belonging
            to the candidate being evaluated.

    Returns:
        List of dicts with chunk data and similarity score, ordered by relevance.
    """
    operator = DISTANCE_OPERATORS.get(distance_metric)
    if operator is None:
        raise ValueError(
            f"Unknown distance metric: {distance_metric}. "
            f"Supported: {list(DISTANCE_OPERATORS.keys())}"
        )

    # Build the query with pgvector distance operator
    vector_str = f"[{','.join(str(v) for v in query_vector)}]"

    where_clause = "c.embedding IS NOT NULL"
    if doc_type:
        where_clause += f" AND d.doc_type = '{doc_type}'"
    if document_id is not None:
        where_clause += f" AND c.document_id = {int(document_id)}"

    query = text(f"""
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.chunk_index,
            c.token_count,
            c.strategy,
            d.title as document_title,
            d.doc_type,
            c.embedding {operator} :vector AS distance
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE {where_clause}
        ORDER BY c.embedding {operator} :vector ASC
        LIMIT :top_k
    """)

    result = await session.execute(
        query,
        {"vector": vector_str, "top_k": top_k},
    )
    rows = result.fetchall()

    return [
        {
            "chunk_id": row.id,
            "document_id": row.document_id,
            "content": row.content,
            "chunk_index": row.chunk_index,
            "token_count": row.token_count,
            "strategy": row.strategy,
            "document_title": row.document_title,
            "doc_type": row.doc_type,
            "distance": float(row.distance),
            "similarity": _distance_to_similarity(float(row.distance), distance_metric),
        }
        for row in rows
    ]


async def compare_distance_metrics(
    session: AsyncSession,
    query_vector: list[float],
    top_k: int = 5,
    doc_type: str | None = None,
) -> dict[str, list[dict]]:
    """Run the same query with all three distance metrics and return results.

    This is the key teaching endpoint for Pillar 2 — users see how different
    metrics rank the same chunks differently (or identically, for normalised vectors).
    """
    results = {}
    for metric in DISTANCE_OPERATORS:
        results[metric] = await search_similar_chunks(
            session, query_vector, top_k, metric, doc_type
        )
    return results


def _distance_to_similarity(distance: float, metric: str) -> float:
    """Convert a distance value to a similarity score (0-1 range).

    Different metrics have different scales:
    - Cosine: distance is 1 - cosine_similarity, so similarity = 1 - distance
    - Euclidean: distance is unbounded, we normalise with 1 / (1 + distance)
    - Inner product: pgvector returns negative inner product, similarity = -distance
    """
    if metric == "cosine":
        return max(0.0, 1.0 - distance)
    elif metric == "euclidean":
        return 1.0 / (1.0 + distance)
    elif metric == "inner_product":
        return max(0.0, -distance)
    return 0.0
