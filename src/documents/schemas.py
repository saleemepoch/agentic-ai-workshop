"""
Pydantic schemas for document and chunk API request/response models.

These schemas define the API contract. The frontend TypeScript types
mirror these schemas for full-stack type safety.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Request schema for creating a new document."""

    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Full document text")
    doc_type: str = Field(
        ..., pattern="^(cv|jd)$", description="Document type: 'cv' or 'jd'"
    )


class ChunkResponse(BaseModel):
    """Response schema for a single chunk."""

    id: int
    document_id: int
    content: str
    chunk_index: int
    token_count: int
    strategy: str
    has_embedding: bool

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    """Response schema for a document with its chunks."""

    id: int
    title: str
    content: str
    doc_type: str
    created_at: datetime
    chunks: list[ChunkResponse] = []

    model_config = {"from_attributes": True}


class ChunkingRequest(BaseModel):
    """Request schema for chunking a document."""

    strategy: str = Field(
        default="semantic",
        pattern="^(semantic|naive)$",
        description="Chunking strategy: 'semantic' or 'naive'",
    )
    max_tokens: int = Field(
        default=256,
        ge=50,
        le=2048,
        description="Maximum tokens per chunk",
    )
    overlap_tokens: int = Field(
        default=50,
        ge=0,
        le=200,
        description="Token overlap between consecutive chunks",
    )


class ChunkingComparisonResponse(BaseModel):
    """Response schema comparing two chunking strategies on the same document."""

    document_id: int
    document_title: str
    semantic_chunks: list[ChunkResponse]
    naive_chunks: list[ChunkResponse]
    semantic_count: int
    naive_count: int
    semantic_avg_tokens: float
    naive_avg_tokens: float
