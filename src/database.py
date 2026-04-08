"""
Database engine and session management.

Uses SQLAlchemy 2.0 async API with asyncpg driver for PostgreSQL.
pgvector extension is enabled on startup for vector similarity search.

Interview talking points:
- Why async SQLAlchemy? FastAPI is async-native. Blocking DB calls in an async
  framework waste the event loop. asyncpg is the fastest PostgreSQL driver for Python.
- Why a session factory function? Each request gets its own session via dependency
  injection. Sessions are not shared across requests — this prevents connection leaks
  and ensures transaction isolation.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def init_db() -> None:
    """Create tables and enable pgvector extension.

    Called once at application startup via FastAPI lifespan.
    In production, you'd use Alembic migrations instead of create_all.
    We use create_all here for simplicity — this is a teaching platform,
    not a production system with schema migration concerns.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent additive migrations — safe to run on every startup.
        # Postgres ADD COLUMN IF NOT EXISTS is the simplest path here without
        # introducing Alembic for a teaching platform.
        await conn.execute(
            text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)")
        )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for dependency injection.

    Usage in FastAPI:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session_factory() as session:
        yield session
