"""
Integration tests for Langfuse tracing.

Verifies that the observability endpoints work and return data.
Requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY.

Run with: pytest tests/integration/observability/ -v -m integration
"""

import pytest

from httpx import AsyncClient

pytestmark = pytest.mark.integration


class TestObservabilityEndpoints:
    """Test observability API endpoints."""

    async def test_get_traces(self, client: AsyncClient) -> None:
        response = await client.get("/observability/traces?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "traces" in data
        assert "total" in data

    async def test_get_model_pricing(self, client: AsyncClient) -> None:
        response = await client.get("/observability/models")
        assert response.status_code == 200
        data = response.json()
        assert "llm_models" in data
        assert "embedding_models" in data
        assert "claude-sonnet-4-20250514" in data["llm_models"]
        assert "voyage-3" in data["embedding_models"]

    async def test_calculate_cost(self, client: AsyncClient) -> None:
        response = await client.post(
            "/observability/costs/calculate?model=claude-sonnet-4-20250514&input_tokens=1000&output_tokens=500"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] > 0
        assert data["model_known"] is True

    async def test_cost_summary(self, client: AsyncClient) -> None:
        response = await client.get("/observability/costs/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_cost_usd" in data
