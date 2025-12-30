"""Tests for health check endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test that health endpoint returns healthy status."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_returns_environment():
    """Test that health endpoint includes environment info."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    data = response.json()
    assert data["environment"] in ["development", "staging", "production"]
