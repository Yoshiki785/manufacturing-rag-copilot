"""API route definitions."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.db.models import Message, Thread
from src.app.db.session import get_session
from src.app.rag.embed import generate_embedding
from src.app.rag.generate import generate_response
from src.app.rag.ingest import ingest_document as ingest_doc
from src.app.rag.retrieve import retrieve_similar_chunks

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
async def query_rag(
    request: QueryRequest,
    session: AsyncSession = Depends(get_session),
) -> QueryResponse:
    """Query the RAG system with a question."""
    # Generate embedding for the query
    query_embedding = await generate_embedding(request.query)

    # Retrieve similar chunks
    context_chunks = await retrieve_similar_chunks(
        session=session,
        query_embedding=query_embedding,
        top_k=request.top_k,
    )

    # Generate response using LLM
    generation_result = await generate_response(
        query=request.query,
        context_chunks=context_chunks,
    )

    # Handle thread management
    if request.thread_id:
        # Existing thread
        thread_uuid = UUID(request.thread_id)
        stmt = select(Thread).where(Thread.id == thread_uuid)
        result = await session.execute(stmt)
        thread = result.scalar_one_or_none()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
    else:
        # Create new thread
        thread = Thread(
            id=uuid4(),
            title=request.query[:100],
        )
        session.add(thread)

    # Save user message
    user_message = Message(
        id=uuid4(),
        thread_id=thread.id,
        role="user",
        content=request.query,
    )
    session.add(user_message)

    # Save assistant message
    assistant_message = Message(
        id=uuid4(),
        thread_id=thread.id,
        role="assistant",
        content=generation_result.answer,
        citations=generation_result.citations,
        token_count=generation_result.token_usage.get("total_tokens"),
    )
    session.add(assistant_message)

    await session.commit()

    return QueryResponse(
        answer=generation_result.answer,
        citations=generation_result.citations,
        thread_id=str(thread.id),
    )


@router.post("/ingest")
async def ingest_document(
    request: IngestRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Ingest a document into the RAG system."""
    document_id = await ingest_doc(
        session=session,
        content=request.content,
        metadata=request.metadata,
    )
    return {"document_id": str(document_id)}


@router.get("/threads")
async def list_threads(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List conversation threads."""
    stmt = select(Thread).order_by(Thread.created_at.desc()).limit(100)
    result = await session.execute(stmt)
    threads = result.scalars().all()

    return [
        {
            "id": str(thread.id),
            "title": thread.title,
            "user_id": thread.user_id,
            "meta": thread.meta,
            "created_at": thread.created_at.isoformat() if thread.created_at else None,
            "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        }
        for thread in threads
    ]


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get a specific conversation thread."""
    thread_uuid = UUID(thread_id)
    stmt = (
        select(Thread)
        .where(Thread.id == thread_uuid)
        .options(selectinload(Thread.messages))
    )
    result = await session.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return {
        "id": str(thread.id),
        "title": thread.title,
        "user_id": thread.user_id,
        "meta": thread.meta,
        "created_at": thread.created_at.isoformat() if thread.created_at else None,
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "citations": msg.citations,
                "token_count": msg.token_count,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in thread.messages
        ],
    }
