"""FastAPI application entry point."""

from fastapi import FastAPI

from src.app.api.routes import router
from src.app.core.config import settings

app = FastAPI(
    title="Manufacturing RAG Copilot",
    description="RAG-powered assistant for manufacturing domain knowledge",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
