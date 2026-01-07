"""Tests for rate limiting behavior."""

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.app.core.rate_limit import create_limiter


def _make_client(enabled: bool) -> AsyncClient:
    limiter = create_limiter(enabled=enabled)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/limited")
    @limiter.limit("1/minute")
    async def limited(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_rate_limit_enforced():
    """Test that requests are blocked when limit exceeded."""
    async with _make_client(enabled=True) as client:
        response = await client.get("/limited")
        assert response.status_code == 200

        response = await client.get("/limited")
        assert response.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_disabled_allows_requests():
    """Test that disabling rate limits allows repeated requests."""
    async with _make_client(enabled=False) as client:
        response = await client.get("/limited")
        assert response.status_code == 200

        response = await client.get("/limited")
        assert response.status_code == 200
