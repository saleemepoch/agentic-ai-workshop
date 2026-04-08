"""
FastAPI router for document processing endpoints.

Endpoints:
- POST /documents           — Upload a new document
- GET  /documents           — List all documents
- GET  /documents/{id}      — Get a document with its chunks
- POST /documents/{id}/chunk — Chunk a document with a chosen strategy
- POST /documents/{id}/compare — Compare chunking strategies side-by-side
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.documents.schemas import (
    ChunkingComparisonResponse,
    ChunkingRequest,
    ChunkResponse,
    DocumentCreate,
    DocumentResponse,
)
from src.documents.service import (
    chunk_document,
    compare_strategies,
    create_document,
    get_document,
    list_documents,
)

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    body: DocumentCreate,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Upload a new document (CV or JD)."""
    doc = await create_document(session, body.title, body.content, body.doc_type)
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        doc_type=doc.doc_type,
        created_at=doc.created_at,
        chunks=[],
    )


@router.get("", response_model=list[DocumentResponse])
async def list_all_documents(
    session: AsyncSession = Depends(get_session),
) -> list[DocumentResponse]:
    """List all documents."""
    docs = await list_documents(session)
    return [
        DocumentResponse(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            doc_type=doc.doc_type,
            created_at=doc.created_at,
            chunks=[
                ChunkResponse(
                    id=c.id,
                    document_id=c.document_id,
                    content=c.content,
                    chunk_index=c.chunk_index,
                    token_count=c.token_count,
                    strategy=c.strategy,
                    has_embedding=c.embedding is not None,
                )
                for c in doc.chunks
            ],
        )
        for doc in docs
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_single_document(
    document_id: int,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Get a document by ID with its chunks."""
    doc = await get_document(session, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        doc_type=doc.doc_type,
        created_at=doc.created_at,
        chunks=[
            ChunkResponse(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                chunk_index=c.chunk_index,
                token_count=c.token_count,
                strategy=c.strategy,
                has_embedding=c.embedding is not None,
            )
            for c in doc.chunks
        ],
    )


@router.post("/{document_id}/chunk", response_model=list[ChunkResponse])
async def chunk_single_document(
    document_id: int,
    body: ChunkingRequest,
    session: AsyncSession = Depends(get_session),
) -> list[ChunkResponse]:
    """Chunk a document using the specified strategy."""
    doc = await get_document(session, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = await chunk_document(
        session, document_id, body.strategy, body.max_tokens, body.overlap_tokens
    )
    return [
        ChunkResponse(
            id=c.id,
            document_id=c.document_id,
            content=c.content,
            chunk_index=c.chunk_index,
            token_count=c.token_count,
            strategy=c.strategy,
            has_embedding=c.embedding is not None,
        )
        for c in chunks
    ]


@router.post("/{document_id}/compare", response_model=ChunkingComparisonResponse)
async def compare_chunking_strategies(
    document_id: int,
    body: ChunkingRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> ChunkingComparisonResponse:
    """Compare semantic and naive chunking on the same document.

    This is the key teaching endpoint. The response contains both strategies'
    chunks side-by-side with statistics, so the frontend can render a visual
    comparison.
    """
    doc = await get_document(session, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    max_tokens = body.max_tokens if body else 256
    overlap_tokens = body.overlap_tokens if body else 50

    return await compare_strategies(session, document_id, max_tokens, overlap_tokens)
