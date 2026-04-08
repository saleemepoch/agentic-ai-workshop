"""
Pydantic schemas for embedding, retrieval, and RAG API models.
"""

from pydantic import BaseModel, Field


# --- Pillar 2: Embeddings & Retrieval ---

class EmbeddingRequest(BaseModel):
    """Request to embed text."""

    text: str = Field(..., min_length=1, description="Text to embed")
    input_type: str = Field(
        default="document",
        pattern="^(document|query)$",
        description="Embedding type: 'document' for storage, 'query' for search",
    )


class EmbeddingResponse(BaseModel):
    """Response with embedding vector and metadata."""

    text: str
    embedding: list[float]
    dimensions: int
    input_type: str


class SearchRequest(BaseModel):
    """Request to search for similar chunks."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    distance_metric: str = Field(
        default="cosine",
        pattern="^(cosine|euclidean|inner_product)$",
        description="Distance metric for similarity search",
    )
    doc_type: str | None = Field(
        default=None,
        pattern="^(cv|jd)$",
        description="Filter by document type",
    )


class SearchResult(BaseModel):
    """A single search result with similarity score."""

    chunk_id: int
    document_id: int
    content: str
    chunk_index: int
    token_count: int
    strategy: str
    document_title: str
    doc_type: str
    distance: float
    similarity: float


class SearchResponse(BaseModel):
    """Search results with metadata."""

    query: str
    distance_metric: str
    results: list[SearchResult]
    total_results: int


class MetricComparisonResponse(BaseModel):
    """Results from the same query using all three distance metrics."""

    query: str
    cosine: list[SearchResult]
    euclidean: list[SearchResult]
    inner_product: list[SearchResult]


# --- Pillar 3: RAG Pipeline ---

class RAGRequest(BaseModel):
    """Request to run the RAG pipeline."""

    query: str = Field(..., min_length=1, description="Query text (e.g., a job description)")
    top_k: int = Field(default=5, ge=1, le=20, description="Chunks to retrieve")
    distance_metric: str = Field(default="cosine", pattern="^(cosine|euclidean|inner_product)$")
    doc_type: str | None = Field(default=None, pattern="^(cv|jd)$")


class RAGStageResult(BaseModel):
    """Result from a single RAG pipeline stage."""

    stage: str
    description: str
    data: dict
    duration_ms: float


class RAGPipelineResponse(BaseModel):
    """Full RAG pipeline response with results from every stage."""

    query: str
    stages: list[RAGStageResult]
    final_output: str
    total_duration_ms: float
    total_tokens: int
    total_cost: float
