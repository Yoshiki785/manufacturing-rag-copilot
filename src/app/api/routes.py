"""API route definitions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str
    thread_id: str | None = None
    top_k: int = 5


class QueryResponse(BaseModel):
    """Response model for RAG queries."""

    answer: str
    citations: list[dict]
    thread_id: str


class IngestRequest(BaseModel):
    """Request model for document ingestion."""

    content: str
    metadata: dict | None = None


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest) -> QueryResponse:
    """Query the RAG system with a question."""
    # TODO: Implement RAG pipeline
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/ingest")
async def ingest_document(request: IngestRequest) -> dict[str, str]:
    """Ingest a document into the RAG system."""
    # TODO: Implement ingestion pipeline
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/threads")
async def list_threads() -> list[dict]:
    """List conversation threads."""
    # TODO: Implement thread listing
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str) -> dict:
    """Get a specific conversation thread."""
    # TODO: Implement thread retrieval
    raise HTTPException(status_code=501, detail="Not implemented")
