"""Security utilities for API authentication and authorization."""

from datetime import datetime
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.db.models import AuditLog
from src.app.db.session import get_session

logger = get_logger(__name__)


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_session),
) -> str:
    """
    Verify API key from request header.

    Args:
        request: FastAPI request object.
        session: Database session for audit logging.
        x_api_key: API key from X-API-Key header.

    Returns:
        API key if valid.

    Raises:
        HTTPException: If API key is missing or invalid.

    Note:
        This function also creates an audit log entry for each authentication attempt.
    """
    # Get client IP address
    client_ip = request.client.host if request.client else None

    # Check if API key authentication is enabled
    if not settings.api_key_enabled:
        # If authentication is disabled, allow request but log it
        logger.warning("API key authentication is disabled")
        await _create_audit_log(
            session=session,
            event_type="auth.bypass",
            action="access",
            details={"reason": "authentication_disabled"},
            ip_address=client_ip,
        )
        return "disabled"

    # Check if API key is provided
    if not x_api_key:
        logger.warning(f"Missing API key from {client_ip}")
        await _create_audit_log(
            session=session,
            event_type="auth.failed",
            action="access_denied",
            details={"reason": "missing_api_key", "path": str(request.url.path)},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key
    valid_keys = settings.api_keys
    if x_api_key not in valid_keys:
        logger.warning(f"Invalid API key from {client_ip}")
        await _create_audit_log(
            session=session,
            event_type="auth.failed",
            action="access_denied",
            details={"reason": "invalid_api_key", "path": str(request.url.path)},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    # Success - log successful authentication
    logger.debug(f"API key authenticated from {client_ip}")
    await _create_audit_log(
        session=session,
        event_type="auth.success",
        action="access_granted",
        details={"path": str(request.url.path), "method": request.method},
        ip_address=client_ip,
    )

    return x_api_key


async def _create_audit_log(
    session: AsyncSession,
    event_type: str,
    action: str,
    details: dict,
    ip_address: str | None = None,
    user_id: str | None = None,
) -> None:
    """
    Create an audit log entry.

    Args:
        session: Database session.
        event_type: Type of event (e.g., 'auth.success', 'auth.failed').
        action: Action performed (e.g., 'access_granted', 'access_denied').
        details: Additional details about the event.
        ip_address: Client IP address.
        user_id: User identifier if available.
    """
    audit_log = AuditLog(
        id=uuid4(),
        event_type=event_type,
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    session.add(audit_log)
    await session.commit()
    logger.debug(f"Audit log created: {event_type} - {action}")
