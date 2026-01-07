"""Tests for security and authentication functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from sqlalchemy import select

from src.app.core.security import verify_api_key
from src.app.db.models import AuditLog


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.url = MagicMock()
    request.url.path = "/api/v1/query"
    request.method = "POST"
    return request


@pytest.mark.asyncio
async def test_verify_api_key_success(session, mock_request):
    """Test successful API key verification."""
    valid_api_key = "test-api-key-123"

    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = [valid_api_key]

        result = await verify_api_key(
            request=mock_request,
            x_api_key=valid_api_key,
            session=session,
        )

        assert result == valid_api_key

        # Verify audit log was created
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert audit_logs[0].event_type == "auth.success"
        assert audit_logs[0].action == "access_granted"


@pytest.mark.asyncio
async def test_verify_api_key_missing(session, mock_request):
    """Test API key verification with missing key."""
    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = ["valid-key"]

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(
                request=mock_request,
                x_api_key=None,
                session=session,
            )

        assert exc_info.value.status_code == 401
        assert "Missing API key" in exc_info.value.detail

        # Verify audit log was created
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert audit_logs[0].event_type == "auth.failed"
        assert audit_logs[0].action == "access_denied"
        assert audit_logs[0].details["reason"] == "missing_api_key"


@pytest.mark.asyncio
async def test_verify_api_key_invalid(session, mock_request):
    """Test API key verification with invalid key."""
    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = ["valid-key-123"]

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(
                request=mock_request,
                x_api_key="invalid-key",
                session=session,
            )

        assert exc_info.value.status_code == 403
        assert "Invalid API key" in exc_info.value.detail

        # Verify audit log was created
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert audit_logs[0].event_type == "auth.failed"
        assert audit_logs[0].action == "access_denied"
        assert audit_logs[0].details["reason"] == "invalid_api_key"


@pytest.mark.asyncio
async def test_verify_api_key_disabled(session, mock_request):
    """Test API key verification when authentication is disabled."""
    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = False

        result = await verify_api_key(
            request=mock_request,
            x_api_key=None,
            session=session,
        )

        assert result == "disabled"

        # Verify audit log was created for bypass
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert audit_logs[0].event_type == "auth.bypass"
        assert audit_logs[0].action == "access"


@pytest.mark.asyncio
async def test_verify_api_key_multiple_valid_keys(session, mock_request):
    """Test API key verification with multiple valid keys."""
    valid_keys = ["key-1", "key-2", "key-3"]

    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = valid_keys

        # Test each valid key
        for key in valid_keys:
            result = await verify_api_key(
                request=mock_request,
                x_api_key=key,
                session=session,
            )
            assert result == key


@pytest.mark.asyncio
async def test_verify_api_key_logs_ip_address(session, mock_request):
    """Test that API key verification logs the IP address."""
    valid_api_key = "test-key"
    expected_ip = "192.168.1.100"
    mock_request.client.host = expected_ip

    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = [valid_api_key]

        await verify_api_key(
            request=mock_request,
            x_api_key=valid_api_key,
            session=session,
        )

        # Verify IP address was logged
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert str(audit_logs[0].ip_address) == expected_ip


@pytest.mark.asyncio
async def test_verify_api_key_logs_path_and_method(session, mock_request):
    """Test that API key verification logs the request path and method."""
    valid_api_key = "test-key"
    mock_request.url.path = "/api/v1/ingest"
    mock_request.method = "POST"

    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = [valid_api_key]

        await verify_api_key(
            request=mock_request,
            x_api_key=valid_api_key,
            session=session,
        )

        # Verify path and method were logged
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert audit_logs[0].details["path"] == "/api/v1/ingest"
        assert audit_logs[0].details["method"] == "POST"


@pytest.mark.asyncio
async def test_verify_api_key_no_client_info(session):
    """Test API key verification when request has no client info."""
    request = MagicMock(spec=Request)
    request.client = None
    request.url = MagicMock()
    request.url.path = "/api/v1/query"
    request.method = "GET"

    valid_api_key = "test-key"

    with patch("src.app.core.security.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.api_keys = [valid_api_key]

        result = await verify_api_key(
            request=request,
            x_api_key=valid_api_key,
            session=session,
        )

        assert result == valid_api_key

        # Verify audit log was created with None IP
        audit_result = await session.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        assert len(audit_logs) == 1
        assert audit_logs[0].ip_address is None
