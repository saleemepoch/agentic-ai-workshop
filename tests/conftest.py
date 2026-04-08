"""
Shared test fixtures for the Agentic AI Workshop.

Provides async database sessions, a FastAPI test client, and common test data.

Interview talking points:
- Why separate unit and integration fixtures? Unit tests should be fast and isolated
  (no DB, no API calls). Integration tests hit the real database and real external APIs.
  The conftest provides both paths.
- Why httpx.AsyncClient for testing? FastAPI recommends it for async test clients.
  It speaks ASGI directly — no server needed.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.database import Base, get_session
from src.main import app


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio as the async backend for tests."""
    return "asyncio"


@pytest.fixture
async def db_engine():
    """Create a test database engine.

    Uses the same DATABASE_URL as the app — in CI, this points to a test database.
    Tables are created before tests and dropped after.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Provide a transactional database session that rolls back after each test.

    This ensures test isolation — each test starts with a clean state.
    """
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Provide an async HTTP client wired to the FastAPI app with test DB session.

    Overrides the get_session dependency so all requests use the test session.
    """

    async def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
