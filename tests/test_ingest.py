"""Tests for document ingestion functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from src.app.db.models import Chunk, Document, Embedding
from src.app.rag.ingest import ingest_document


@pytest.mark.asyncio
async def test_ingest_document_success(session):
    """Test successful document ingestion."""
    content = "This is a test document. It has multiple sentences. Each sentence provides context."

    # Mock embedding generation
    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
            title="Test Document",
            source_type="manual",
            source_path="/test/path.txt",
            metadata={"key": "value"},
        )

        assert document_id is not None

        # Verify document was created
        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one()
        assert document.title == "Test Document"
        assert document.content == content
        assert document.source_type == "manual"
        assert document.meta == {"key": "value"}


@pytest.mark.asyncio
async def test_ingest_document_creates_chunks(session):
    """Test that ingestion creates chunks."""
    content = "First sentence. Second sentence. Third sentence."

    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
        )

        # Verify chunks were created
        result = await session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = result.scalars().all()
        assert len(chunks) > 0

        # Verify chunk properties
        for chunk in chunks:
            assert chunk.content
            assert chunk.chunk_index >= 0
            assert chunk.document_id == document_id


@pytest.mark.asyncio
async def test_ingest_document_creates_embeddings(session):
    """Test that ingestion creates embeddings for each chunk."""
    content = "Test content for embedding generation."

    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
        )

        # Get chunks
        result = await session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = result.scalars().all()

        # Verify embeddings were created for each chunk
        for chunk in chunks:
            embedding_result = await session.execute(
                select(Embedding).where(Embedding.chunk_id == chunk.id)
            )
            embeddings = embedding_result.scalars().all()
            assert len(embeddings) > 0

            # Verify embedding properties
            embedding = embeddings[0]
            assert embedding.model_name == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_ingest_document_with_metadata(session):
    """Test that metadata is saved correctly."""
    content = "Test content."
    metadata = {"source": "test", "version": "1.0", "author": "Test Author"}

    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
            metadata=metadata,
        )

        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one()
        assert document.meta == metadata


@pytest.mark.asyncio
async def test_ingest_document_minimal_params(session):
    """Test ingestion with only required parameters."""
    content = "Minimal test content."

    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
        )

        assert document_id is not None

        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one()
        assert document.content == content
        assert document.title is None
        assert document.meta == {}


@pytest.mark.asyncio
async def test_ingest_document_long_content(session):
    """Test ingestion of long document content."""
    # Create long content that will be split into multiple chunks
    content = "This is a test sentence. " * 100

    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
        )

        # Verify multiple chunks were created
        result = await session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = result.scalars().all()
        assert len(chunks) > 1


@pytest.mark.asyncio
async def test_ingest_document_chunk_order(session):
    """Test that chunks maintain correct order."""
    content = "First. Second. Third. Fourth. Fifth."

    mock_embedding = [0.1] * 1536

    with patch("src.app.rag.ingest.generate_embedding", return_value=mock_embedding):
        document_id = await ingest_document(
            session=session,
            content=content,
        )

        result = await session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        chunks = result.scalars().all()

        # Verify sequential chunk indexes
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i


@pytest.mark.asyncio
async def test_ingest_document_embedding_generation_called(session):
    """Test that embedding generation is called for each chunk."""
    content = "Test content for embedding calls."

    mock_generate_embedding = AsyncMock(return_value=[0.1] * 1536)

    with patch("src.app.rag.ingest.generate_embedding", mock_generate_embedding):
        await ingest_document(
            session=session,
            content=content,
        )

        # Verify generate_embedding was called
        assert mock_generate_embedding.called
        # Should be called at least once (for each chunk)
        assert mock_generate_embedding.call_count > 0
