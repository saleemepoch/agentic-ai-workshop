"""
Retrieval quality metrics: precision@k, recall@k, MRR.

These metrics quantify how well the retrieval step finds relevant chunks.
They're the standard metrics for information retrieval systems.

Interview talking points:
- Why precision AND recall? They measure different things. High precision
  means "what we retrieved was relevant." High recall means "we found
  everything that was relevant." You want both — a system that retrieves
  only one relevant chunk has perfect precision but terrible recall.
- What's MRR? Mean Reciprocal Rank measures how high the FIRST relevant
  result appears. MRR of 1.0 means the first result is always relevant.
  MRR of 0.5 means the first relevant result is typically second.
- Why @k? Because we only retrieve k chunks. Precision@5 measures
  relevance of the top 5 results, not the entire database.
"""


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Precision@k: fraction of top-k retrieved items that are relevant.

    Args:
        retrieved: Ordered list of retrieved item IDs/keys.
        relevant: Set of relevant item IDs/keys (ground truth).
        k: Number of top results to consider.

    Returns:
        Float between 0.0 and 1.0.
    """
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    relevant_in_top_k = sum(1 for item in top_k if item in relevant)
    return relevant_in_top_k / len(top_k)


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Recall@k: fraction of relevant items that appear in top-k results.

    Args:
        retrieved: Ordered list of retrieved item IDs/keys.
        relevant: Set of relevant item IDs/keys (ground truth).
        k: Number of top results to consider.

    Returns:
        Float between 0.0 and 1.0.
    """
    if not relevant:
        return 1.0  # If nothing is relevant, recall is trivially 1.0
    top_k = retrieved[:k]
    relevant_in_top_k = sum(1 for item in top_k if item in relevant)
    return relevant_in_top_k / len(relevant)


def mean_reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """MRR: reciprocal of the rank of the first relevant result.

    If the first relevant result is at position 1, MRR = 1.0.
    If at position 3, MRR = 0.333. If no relevant results, MRR = 0.0.

    Args:
        retrieved: Ordered list of retrieved item IDs/keys.
        relevant: Set of relevant item IDs/keys (ground truth).

    Returns:
        Float between 0.0 and 1.0.
    """
    for i, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / i
    return 0.0


def compute_retrieval_metrics(
    retrieved: list[str],
    relevant: set[str],
    k: int = 5,
) -> dict[str, float]:
    """Compute all retrieval metrics for a single query.

    Returns:
        Dict with precision_at_k, recall_at_k, and mrr.
    """
    return {
        f"precision@{k}": round(precision_at_k(retrieved, relevant, k), 4),
        f"recall@{k}": round(recall_at_k(retrieved, relevant, k), 4),
        "mrr": round(mean_reciprocal_rank(retrieved, relevant), 4),
    }
