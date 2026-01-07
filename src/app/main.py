"""FastAPI application entry point."""

import logging
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.routes import router
from src.app.core.config import settings
from src.app.core.exceptions import (
    AuthenticationError,
    DatabaseError,
    EmbeddingError,
    GenerationError,
    IngestError,
    RAGException,
    RateLimitError,
    RetrievalError,
    ValidationError,
)
from src.app.core.logging import get_logger
from src.app.core.rate_limit import limiter
from src.app.db.models import AuditLog
from src.app.db.session import async_session_maker

logger = get_logger(__name__)

app = FastAPI(
    title="Manufacturing RAG Copilot",
    description="RAG-powered assistant for manufacturing domain knowledge",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app, endpoint="/metrics")


# Error handlers
async def log_error_to_audit(
    session: AsyncSession,
    error: Exception,
    request: Request,
) -> None:
    """Log error to audit log."""
    try:
        client_ip = request.client.host if request.client else None
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "path": str(request.url.path),
            "method": request.method,
        }

        if isinstance(error, RAGException):
            error_details.update(error.details)
            if error.original_error:
                error_details["original_error"] = str(error.original_error)

        audit_log = AuditLog(
            id=uuid4(),
            event_type="error.occurred",
            action="error_logged",
            details=error_details,
            ip_address=client_ip,
            created_at=datetime.utcnow(),
        )
        session.add(audit_log)
        await session.commit()
    except Exception as audit_error:
        logger.error(f"Failed to log error to audit: {audit_error}")


@app.exception_handler(ValidationError)
async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.message}", extra={"details": exc.details})

    async with async_session_maker() as session:
        await log_error_to_audit(session, exc, request)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning(
        f"Authentication error: {exc.message}", extra={"details": exc.details}
    )

    async with async_session_maker() as session:
        await log_error_to_audit(session, exc, request)

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Authentication Error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(
    request: Request, exc: RateLimitError
) -> JSONResponse:
    """Handle rate limit errors."""
    logger.warning(f"Rate limit error: {exc.message}", extra={"details": exc.details})

    async with async_session_maker() as session:
        await log_error_to_audit(session, exc, request)

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate Limit Exceeded",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(EmbeddingError)
@app.exception_handler(RetrievalError)
@app.exception_handler(GenerationError)
@app.exception_handler(IngestError)
@app.exception_handler(DatabaseError)
async def rag_error_handler(request: Request, exc: RAGException) -> JSONResponse:
    """Handle RAG-related errors."""
    logger.error(f"RAG error: {exc.message}", extra={"details": exc.details})

    async with async_session_maker() as session:
        await log_error_to_audit(session, exc, request)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details if settings.environment == "development" else {},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected errors."""
    logger.exception(f"Unexpected error: {str(exc)}")

    async with async_session_maker() as session:
        await log_error_to_audit(session, exc, request)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": (
                {"error": str(exc)} if settings.environment == "development" else {}
            ),
        },
    )


app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
