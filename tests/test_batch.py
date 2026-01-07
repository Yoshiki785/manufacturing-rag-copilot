"""Tests for batch processing functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from src.app.db.models import Chunk, Document, Embedding
from src.app.rag.embed import generate_embeddings_batch
from src.app.rag.ingest import ingest_batch


@pytest.mark.asyncio
async def test_generate_embeddings_batch_empty_list():
    """Test batch embedding with empty list."""
    result = await generate_embeddings_batch([])
    assert result == []


@pytest.mark.asyncio
async def test_generate_embeddings_batch_single_text():
    """Test batch embedding with single text."""
    texts = ["This is a test text."]
    mock_embedding = [0.1] * 1536

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = mock_embedding

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(texts)

        assert len(result) == 1
        assert result[0] == mock_embedding
        mock_embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_multiple_texts():
    """Test batch embedding with multiple texts."""
    texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
    mock_embeddings_data = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536, [0.4] * 1536, [0.5] * 1536]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock() for _ in range(5)]
    for i, mock_emb in enumerate(mock_embeddings_data):
        mock_response.data[i].embedding = mock_emb

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(texts)

        assert len(result) == 5
        assert result == mock_embeddings_data
        mock_embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_large_batch():
    """Test batch embedding with more than 2048 texts (multiple batches)."""
    # Create 3000 texts to test batch splitting
    texts = [f"Text {i}" for i in range(3000)]

    mock_client = MagicMock()
    mock_embeddings = AsyncMock()

    # Mock responses for each batch call
    def create_mock_response(batch_size):
        mock_response = MagicMock()
        mock_response.data = [MagicMock() for _ in range(batch_size)]
        for item in mock_response.data:
            item.embedding = [0.1] * 1536
        return mock_response

    # First batch: 2048 items, second batch: 952 items
    mock_embeddings.create.side_effect = [
        create_mock_response(2048),
        create_mock_response(952),
    ]
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(texts)

        assert len(result) == 3000
        # Should have been called twice (2048 + 952)
        assert mock_embeddings.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_embeddings_batch_maintains_order():
    """Test that batch embedding maintains input order."""
    texts = [f"Text {i}" for i in range(10)]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock() for _ in range(10)]
    for i in range(10):
        # Each embedding has a different value to verify order
        mock_response.data[i].embedding = [float(i)] * 1536

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(texts)

        # Verify order is maintained
        for i in range(10):
            assert result[i][0] == float(i)


@pytest.mark.asyncio
async def test_ingest_batch_empty_list(session):
    """Test batch ingestion with empty list."""
    result = await ingest_batch(session, [])
    assert result == []


@pytest.mark.asyncio
async def test_ingest_batch_single_document(session):
    """Test batch ingestion with single document."""
    documents = [
        {
            "content": "This is a test document.",
            "title": "Test Doc",
            "metadata": {"type": "test"},
        }
    ]

    mock_embeddings = [[0.1] * 1536]

    with patch(
        "src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings
    ):
        result = await ingest_batch(session, documents)

        assert len(result) == 1
        assert result[0] is not None

        # Verify document was created
        stmt = select(Document).where(Document.id == result[0])
        db_result = await session.execute(stmt)
        doc = db_result.scalar_one()
        assert doc.title == "Test Doc"
        assert doc.content == "This is a test document."


@pytest.mark.asyncio
async def test_ingest_batch_multiple_documents(session):
    """Test batch ingestion with multiple documents."""
    documents = [
        {"content": "Document 1 content.", "title": "Doc 1"},
        {"content": "Document 2 content.", "title": "Doc 2"},
        {"content": "Document 3 content.", "title": "Doc 3"},
    ]

    # Mock 3 embeddings (one per document chunk)
    mock_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]

    with patch(
        "src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings
    ):
        result = await ingest_batch(session, documents)

        assert len(result) == 3

        # Verify all documents were created
        stmt = select(Document)
        db_result = await session.execute(stmt)
        docs = db_result.scalars().all()
        assert len(docs) == 3


@pytest.mark.asyncio
async def test_ingest_batch_creates_chunks_and_embeddings(session):
    """Test that batch ingestion creates chunks and embeddings."""
    documents = [
        {"content": "First document. " * 50},  # Will create multiple chunks
        {"content": "Second document. " * 50},
    ]

    # Create dynamic mock that returns embeddings based on input size
    async def mock_generate_embeddings_batch(texts):
        return [[0.1] * 1536 for _ in range(len(texts))]

    with patch(
        "src.app.rag.ingest.generate_embeddings_batch",
        side_effect=mock_generate_embeddings_batch,
    ):
        result = await ingest_batch(session, documents)

        assert len(result) == 2

        # Verify chunks were created
        stmt = select(Chunk)
        db_result = await session.execute(stmt)
        chunks = db_result.scalars().all()
        assert len(chunks) > 0

        # Verify embeddings were created
        stmt = select(Embedding)
        db_result = await session.execute(stmt)
        embeddings = db_result.scalars().all()
        assert len(embeddings) == len(chunks)


@pytest.mark.asyncio
async def test_ingest_batch_with_metadata(session):
    """Test batch ingestion preserves metadata."""
    documents = [
        {
            "content": "Document with metadata",
            "title": "Meta Doc",
            "source_type": "manual",
            "source_path": "/path/to/doc",
            "metadata": {"version": "1.0", "author": "Test"},
        }
    ]

    mock_embeddings = [[0.1] * 1536]

    with patch(
        "src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings
    ):
        result = await ingest_batch(session, documents)

        stmt = select(Document).where(Document.id == result[0])
        db_result = await session.execute(stmt)
        doc = db_result.scalar_one()

        assert doc.source_type == "manual"
        assert doc.source_path == "/path/to/doc"
        assert doc.meta["version"] == "1.0"
        assert doc.meta["author"] == "Test"


@pytest.mark.asyncio
async def test_ingest_batch_efficiency(session):
    """Test that batch ingestion calls generate_embeddings_batch only once."""
    documents = [{"content": f"Document {i}"} for i in range(10)]

    mock_embeddings = [[0.1] * 1536 for _ in range(10)]
    mock_generate = AsyncMock(return_value=mock_embeddings)

    with patch("src.app.rag.ingest.generate_embeddings_batch", mock_generate):
        await ingest_batch(session, documents)

        # Should be called only once for all documents
        mock_generate.assert_called_once()
        # Verify it was called with all chunk texts
        call_args = mock_generate.call_args[0][0]
        assert len(call_args) == 10  # 10 chunks (one per doc)


@pytest.mark.asyncio
async def test_ingest_batch_handles_long_documents(session):
    """Test batch ingestion with long documents that create many chunks."""
    documents = [
        {"content": "This is a long document. " * 200, "title": "Long Doc 1"},
        {"content": "Another long document. " * 200, "title": "Long Doc 2"},
    ]

    # Create dynamic mock that returns embeddings based on input size
    async def mock_generate_embeddings_batch(texts):
        return [[0.1] * 1536 for _ in range(len(texts))]

    with patch(
        "src.app.rag.ingest.generate_embeddings_batch",
        side_effect=mock_generate_embeddings_batch,
    ):
        result = await ingest_batch(session, documents)

        assert len(result) == 2

        # Verify multiple chunks were created
        stmt = select(Chunk)
        db_result = await session.execute(stmt)
        chunks = db_result.scalars().all()
        assert len(chunks) > 10  # Should have many chunks


@pytest.mark.asyncio
async def test_ingest_batch_chunk_index_consistency(session):
    """Test that chunk indexes are consistent within each document."""
    documents = [
        {"content": "Document 1. " * 100},
        {"content": "Document 2. " * 100},
    ]

    # Create dynamic mock that returns embeddings based on input size
    async def mock_generate_embeddings_batch(texts):
        return [[0.1] * 1536 for _ in range(len(texts))]

    with patch(
        "src.app.rag.ingest.generate_embeddings_batch",
        side_effect=mock_generate_embeddings_batch,
    ):
        result = await ingest_batch(session, documents)

        # Check chunks for first document
        stmt = (
            select(Chunk)
            .where(Chunk.document_id == result[0])
            .order_by(Chunk.chunk_index)
        )
        db_result = await session.execute(stmt)
        chunks = db_result.scalars().all()

        # Verify chunk indexes are sequential starting from 0
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
