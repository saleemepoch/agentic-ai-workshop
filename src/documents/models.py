"""
SQLAlchemy models for documents and chunks.

Interview talking points:
- Why store chunks separately from documents? Each chunk gets its own embedding vector.
  Retrieval operates on chunks, not whole documents. This is the fundamental unit of
  RAG — you retrieve chunks, not documents.
- Why a vector column on Chunk? pgvector stores embeddings directly in Postgres.
  No separate vector database needed. The embedding is nullable because chunking
  and embedding are separate pipeline stages — a chunk exists before it's embedded.
"""

from datetime import datetime
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class DocumentType(str, Enum):
    """Type of document — determines how it's used in matching."""

    CV = "cv"
    JOB_DESCRIPTION = "jd"


class ChunkStrategy(str, Enum):
    """Chunking strategy used to produce this chunk."""

    SEMANTIC = "semantic"
    NAIVE = "naive"


class Document(Base):
    """A document (CV or job description) uploaded into the system.

    Documents are the raw input. They are chunked into smaller pieces
    for embedding and retrieval. A single document produces multiple chunks.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(String(20), nullable=False)
    # SHA256 of the normalised content. Nullable for documents created before
    # the column was added. Used for deduplication when the agent ingests a
    # CV — same content → same document → no re-chunking or re-embedding.
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title='{self.title}' type={self.doc_type}>"


class Chunk(Base):
    """A chunk of text extracted from a document.

    Each chunk is a semantically meaningful unit of text, sized to fit within
    embedding model token limits. The embedding vector is stored directly in
    Postgres via pgvector for similarity search.

    The strategy field records which chunker produced this chunk, enabling
    side-by-side comparison of chunking strategies on the same document.
    """

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    strategy: Mapped[ChunkStrategy] = mapped_column(String(20), nullable=False)

    # 1024 dimensions for Voyage AI voyage-3 model embeddings
    # Nullable because chunking happens before embedding
    embedding = mapped_column(Vector(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return (
            f"<Chunk id={self.id} doc_id={self.document_id} "
            f"index={self.chunk_index} strategy={self.strategy} "
            f"tokens={self.token_count}>"
        )
