"""Tests for API endpoints."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.app.db.models import Document, Thread


@pytest.mark.asyncio
async def test_query_rag_endpoint_success(client):
    """Test successful RAG query."""
    mock_embedding = [0.1] * 1536
    mock_generate_response = AsyncMock(
        return_value=type(
            "GenerationResult",
            (),
            {
                "answer": "Test answer with [Source 1]",
                "citations": [{"source": 1, "chunk_id": str(uuid4()), "content": "Test"}],
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            },
        )
    )

    with patch("src.app.api.routes.generate_embedding", return_value=mock_embedding):
        with patch("src.app.api.routes.retrieve_similar_chunks", return_value=[]):
            with patch("src.app.api.routes.generate_response", mock_generate_response):
                response = await client.post(
                    "/api/v1/query",
                    json={"query": "What is the torque specification?"},
                )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "thread_id" in data


@pytest.mark.asyncio
async def test_query_rag_with_thread_id(client, session):
    """Test RAG query with existing thread ID."""
    # Create a thread
    thread = Thread(id=uuid4(), title="Test Thread", meta={})
    session.add(thread)
    await session.commit()

    mock_embedding = [0.1] * 1536
    mock_generate_response = AsyncMock(
        return_value=type(
            "GenerationResult",
            (),
            {
                "answer": "Follow-up answer",
                "citations": [],
                "token_usage": {"prompt_tokens": 80, "completion_tokens": 30, "total_tokens": 110},
            },
        )
    )

    with patch("src.app.api.routes.generate_embedding", return_value=mock_embedding):
        with patch("src.app.api.routes.retrieve_similar_chunks", return_value=[]):
            with patch("src.app.api.routes.generate_response", mock_generate_response):
                response = await client.post(
                    "/api/v1/query",
                    json={
                        "query": "Follow-up question",
                        "thread_id": str(thread.id),
                    },
                )

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == str(thread.id)


@pytest.mark.asyncio
async def test_query_rag_invalid_thread_id(client):
    """Test RAG query with non-existent thread ID."""
    fake_thread_id = str(uuid4())

    mock_embedding = [0.1] * 1536
    mock_generate_response = AsyncMock(
        return_value=type(
            "GenerationResult",
            (),
            {
                "answer": "Test answer",
                "citations": [],
                "token_usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )
    )

    with patch("src.app.api.routes.generate_embedding", return_value=mock_embedding):
        with patch("src.app.api.routes.retrieve_similar_chunks", return_value=[]):
            with patch("src.app.api.routes.generate_response", mock_generate_response):
                response = await client.post(
                    "/api/v1/query",
                    json={
                        "query": "Test question",
                        "thread_id": fake_thread_id,
                    },
                )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ingest_document_endpoint(client):
    """Test document ingestion endpoint."""
    mock_document_id = uuid4()

    with patch("src.app.api.routes.ingest_doc", return_value=mock_document_id):
        response = await client.post(
            "/api/v1/ingest",
            json={
                "content": "Test document content",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["document_id"] == str(mock_document_id)


@pytest.mark.asyncio
async def test_ingest_document_minimal(client):
    """Test document ingestion with minimal data."""
    mock_document_id = uuid4()

    with patch("src.app.api.routes.ingest_doc", return_value=mock_document_id):
        response = await client.post(
            "/api/v1/ingest",
            json={"content": "Minimal content"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data


@pytest.mark.asyncio
async def test_list_threads_empty(client):
    """Test listing threads when database is empty."""
    response = await client.get("/api/v1/threads")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_threads_with_data(client, session):
    """Test listing threads with existing data."""
    # Create threads
    thread1 = Thread(id=uuid4(), title="Thread 1", meta={})
    thread2 = Thread(id=uuid4(), title="Thread 2", meta={})
    session.add(thread1)
    session.add(thread2)
    await session.commit()

    response = await client.get("/api/v1/threads")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Verify thread structure
    for thread in data:
        assert "id" in thread
        assert "title" in thread
        assert "created_at" in thread


@pytest.mark.asyncio
async def test_get_thread_success(client, session):
    """Test retrieving a specific thread."""
    thread = Thread(id=uuid4(), title="Test Thread", meta={"key": "value"})
    session.add(thread)
    await session.commit()

    response = await client.get(f"/api/v1/threads/{thread.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(thread.id)
    assert data["title"] == "Test Thread"
    assert "messages" in data
    assert isinstance(data["messages"], list)


@pytest.mark.asyncio
async def test_get_thread_not_found(client):
    """Test retrieving non-existent thread."""
    fake_thread_id = uuid4()

    response = await client.get(f"/api/v1/threads/{fake_thread_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_response_format(client):
    """Test that query response has correct format."""
    mock_embedding = [0.1] * 1536
    mock_generate_response = AsyncMock(
        return_value=type(
            "GenerationResult",
            (),
            {
                "answer": "Formatted answer",
                "citations": [
                    {
                        "source": 1,
                        "chunk_id": str(uuid4()),
                        "content": "Citation content",
                    }
                ],
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            },
        )
    )

    with patch("src.app.api.routes.generate_embedding", return_value=mock_embedding):
        with patch("src.app.api.routes.retrieve_similar_chunks", return_value=[]):
            with patch("src.app.api.routes.generate_response", mock_generate_response):
                response = await client.post(
                    "/api/v1/query",
                    json={"query": "Test query"},
                )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["thread_id"], str)

    # Verify citation structure
    if data["citations"]:
        citation = data["citations"][0]
        assert "source" in citation
        assert "chunk_id" in citation
        assert "content" in citation


@pytest.mark.asyncio
async def test_query_with_top_k_parameter(client):
    """Test query with custom top_k parameter."""
    mock_embedding = [0.1] * 1536
    mock_retrieve = AsyncMock(return_value=[])
    mock_generate_response = AsyncMock(
        return_value=type(
            "GenerationResult",
            (),
            {
                "answer": "Answer",
                "citations": [],
                "token_usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )
    )

    with patch("src.app.api.routes.generate_embedding", return_value=mock_embedding):
        with patch("src.app.api.routes.retrieve_similar_chunks", mock_retrieve):
            with patch("src.app.api.routes.generate_response", mock_generate_response):
                response = await client.post(
                    "/api/v1/query",
                    json={"query": "Test query", "top_k": 10},
                )

    assert response.status_code == 200
    # Verify retrieve was called with top_k=10
    assert mock_retrieve.called
    call_kwargs = mock_retrieve.call_args.kwargs
    assert call_kwargs["top_k"] == 10
