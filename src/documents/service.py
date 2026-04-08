"""
Document service: business logic for document CRUD and chunking.

Follows the Router → Service → Model pattern. The service layer contains
business logic — routers handle HTTP, models handle persistence, and
the service sits between them orchestrating operations.

Interview talking points:
- Why a service layer? It keeps routers thin and testable. You can test
  chunking logic without HTTP. You can swap the API framework without
  touching business logic. It's the same pattern used in production
  microservices.
"""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.documents.chunker import semantic_chunk
from src.documents.models import Chunk, ChunkStrategy, Document, DocumentType
from src.documents.naive_chunker import naive_chunk
from src.documents.schemas import ChunkingComparisonResponse, ChunkResponse


def compute_content_hash(content: str) -> str:
    """SHA256 of the whitespace-normalised content.

    Used by the agent to dedupe identical CVs across runs without re-chunking.
    Whitespace normalisation prevents trivial diffs (trailing newlines, indent
    changes) from defeating the dedup.
    """
    normalised = " ".join(content.split())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


async def create_document(
    session: AsyncSession,
    title: str,
    content: str,
    doc_type: str,
) -> Document:
    """Create and persist a new document."""
    document = Document(
        title=title,
        content=content,
        doc_type=DocumentType(doc_type),
        content_hash=compute_content_hash(content),
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def get_or_create_by_hash(
    session: AsyncSession,
    title: str,
    content: str,
    doc_type: str,
) -> tuple[Document, bool]:
    """Find an existing document by content hash, or create a new one.

    Returns:
        Tuple of (document, created) where `created` is True if a new
        document was inserted, False if an existing one was returned.

    This is the dedup primitive the agent uses on CV ingestion. Same CV
    content → same document_id → no re-chunking or re-embedding cost.
    """
    h = compute_content_hash(content)
    result = await session.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.content_hash == h)
        .where(Document.doc_type == DocumentType(doc_type))
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing, False

    document = Document(
        title=title,
        content=content,
        doc_type=DocumentType(doc_type),
        content_hash=h,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    # Re-fetch with chunks eager-loaded so callers can inspect existing chunks
    document = await get_document(session, document.id)
    assert document is not None
    return document, True


async def get_document(session: AsyncSession, document_id: int) -> Document | None:
    """Fetch a document by ID with its chunks."""
    result = await session.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    )
    return result.scalar_one_or_none()


async def list_documents(session: AsyncSession) -> list[Document]:
    """List all documents with their chunks eagerly loaded.

    Eager loading prevents lazy-load issues when serialising in async
    response handlers — the chunks relationship would otherwise trigger
    a sync DB call inside a Pydantic validator.
    """
    result = await session.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def chunk_document(
    session: AsyncSession,
    document_id: int,
    strategy: str = "semantic",
    max_tokens: int = 256,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """Chunk a document using the specified strategy and persist the chunks.

    Removes any existing chunks with the same strategy before creating new ones,
    so re-chunking is idempotent.
    """
    document = await get_document(session, document_id)
    if document is None:
        raise ValueError(f"Document {document_id} not found")

    # Remove existing chunks with this strategy
    existing = [c for c in document.chunks if c.strategy == strategy]
    for chunk in existing:
        await session.delete(chunk)

    # Generate new chunks
    if strategy == "semantic":
        raw_chunks = semantic_chunk(document.content, max_tokens, overlap_tokens)
    else:
        raw_chunks = naive_chunk(document.content, max_tokens, overlap_tokens)

    # Persist chunks
    chunk_strategy = ChunkStrategy(strategy)
    db_chunks: list[Chunk] = []
    for raw in raw_chunks:
        chunk = Chunk(
            document_id=document_id,
            content=str(raw["content"]),
            chunk_index=int(raw["chunk_index"]),
            token_count=int(raw["token_count"]),
            strategy=chunk_strategy,
        )
        session.add(chunk)
        db_chunks.append(chunk)

    await session.commit()
    for chunk in db_chunks:
        await session.refresh(chunk)

    return db_chunks


async def compare_strategies(
    session: AsyncSession,
    document_id: int,
    max_tokens: int = 256,
    overlap_tokens: int = 50,
) -> ChunkingComparisonResponse:
    """Chunk a document with both strategies and return a comparison.

    This is the key teaching endpoint — users see both strategies
    side-by-side on the same document.
    """
    semantic_chunks = await chunk_document(
        session, document_id, "semantic", max_tokens, overlap_tokens
    )
    naive_chunks = await chunk_document(
        session, document_id, "naive", max_tokens, overlap_tokens
    )

    document = await get_document(session, document_id)
    assert document is not None

    def to_response(chunk: Chunk) -> ChunkResponse:
        return ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            strategy=chunk.strategy,
            has_embedding=chunk.embedding is not None,
        )

    semantic_responses = [to_response(c) for c in semantic_chunks]
    naive_responses = [to_response(c) for c in naive_chunks]

    semantic_avg = (
        sum(c.token_count for c in semantic_chunks) / len(semantic_chunks)
        if semantic_chunks
        else 0.0
    )
    naive_avg = (
        sum(c.token_count for c in naive_chunks) / len(naive_chunks)
        if naive_chunks
        else 0.0
    )

    return ChunkingComparisonResponse(
        document_id=document.id,
        document_title=document.title,
        semantic_chunks=semantic_responses,
        naive_chunks=naive_responses,
        semantic_count=len(semantic_chunks),
        naive_count=len(naive_chunks),
        semantic_avg_tokens=round(semantic_avg, 1),
        naive_avg_tokens=round(naive_avg, 1),
    )
