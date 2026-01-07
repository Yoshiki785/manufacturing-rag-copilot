"""Rate limiting utilities using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.app.core.config import settings


def create_limiter(
    *,
    default_limits: list[str] | None = None,
    enabled: bool | None = None,
) -> Limiter:
    """Create a rate limiter configured from settings."""
    resolved_enabled = settings.rate_limit_enabled if enabled is None else enabled
    resolved_limits = default_limits

    if resolved_limits is None:
        resolved_limits = [settings.rate_limit_default] if resolved_enabled else []

    return Limiter(
        key_func=get_remote_address,
        default_limits=resolved_limits,
        enabled=resolved_enabled,
    )


limiter = create_limiter()
