"""Tests for document ingestion functionality."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.app.db.models import Chunk, Document, Embedding
from src.app.rag.ingest import ingest_batch, ingest_document


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
        result = await session.execute(select(Chunk).where(Chunk.document_id == document_id))
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
        result = await session.execute(select(Chunk).where(Chunk.document_id == document_id))
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
        result = await session.execute(select(Chunk).where(Chunk.document_id == document_id))
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
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
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


# ============================================================================
# Batch Ingestion Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_batch_success(session):
    """Test successful batch ingestion of multiple documents."""
    documents = [
        {
            "content": "First document content. It has multiple sentences.",
            "title": "Document 1",
            "source_type": "manual",
            "source_path": "/test/doc1.txt",
            "metadata": {"key": "value1"},
        },
        {
            "content": "Second document content. It also has multiple sentences.",
            "title": "Document 2",
            "source_type": "procedure",
            "source_path": "/test/doc2.txt",
            "metadata": {"key": "value2"},
        },
        {
            "content": "Third document content with more text.",
            "title": "Document 3",
            "source_type": "spec",
        },
    ]

    # Mock batch embedding generation - dynamically generate based on chunk count
    async def mock_generate_batch(texts):
        return [[0.1] * 1536 for _ in texts]

    with patch("src.app.rag.ingest.generate_embeddings_batch", side_effect=mock_generate_batch):
        document_ids = await ingest_batch(session=session, documents=documents)

        # Verify correct number of documents created
        assert len(document_ids) == 3

        # Verify all documents were created
        result = await session.execute(select(Document))
        all_docs = result.scalars().all()
        assert len(all_docs) == 3

        # Verify document properties
        for doc in all_docs:
            assert doc.title in ["Document 1", "Document 2", "Document 3"]
            assert doc.content


@pytest.mark.asyncio
async def test_ingest_batch_empty_list(session):
    """Test batch ingestion with empty list."""
    document_ids = await ingest_batch(session=session, documents=[])
    assert document_ids == []


@pytest.mark.asyncio
async def test_ingest_batch_single_document(session):
    """Test batch ingestion with a single document."""
    documents = [
        {
            "content": "Single document content.",
            "title": "Single Doc",
        }
    ]

    mock_embeddings = [[0.1] * 1536]

    with patch("src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings):
        document_ids = await ingest_batch(session=session, documents=documents)

        assert len(document_ids) == 1

        result = await session.execute(select(Document))
        docs = result.scalars().all()
        assert len(docs) == 1
        assert docs[0].title == "Single Doc"


@pytest.mark.asyncio
async def test_ingest_batch_creates_chunks(session):
    """Test that batch ingestion creates chunks for all documents."""
    documents = [
        {"content": "First document. " * 20},
        {"content": "Second document. " * 20},
    ]

    # Mock embeddings dynamically
    async def mock_generate_batch(texts):
        return [[0.1] * 1536 for _ in texts]

    with patch("src.app.rag.ingest.generate_embeddings_batch", side_effect=mock_generate_batch):
        document_ids = await ingest_batch(session=session, documents=documents)

        # Verify chunks were created for each document
        for doc_id in document_ids:
            result = await session.execute(select(Chunk).where(Chunk.document_id == doc_id))
            chunks = result.scalars().all()
            assert len(chunks) > 0


@pytest.mark.asyncio
async def test_ingest_batch_creates_embeddings(session):
    """Test that batch ingestion creates embeddings for all chunks."""
    documents = [
        {"content": "First document content."},
        {"content": "Second document content."},
    ]

    # Mock embeddings
    mock_embeddings = [[0.1] * 1536, [0.2] * 1536]

    with patch("src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings):
        await ingest_batch(session=session, documents=documents)

        # Verify embeddings were created
        result = await session.execute(select(Embedding))
        embeddings = result.scalars().all()
        assert len(embeddings) == 2

        for embedding in embeddings:
            assert embedding.model_name == "text-embedding-3-small"
            assert len(embedding.embedding) == 1536


@pytest.mark.asyncio
async def test_ingest_batch_uses_batch_embedding(session):
    """Test that batch ingestion uses generate_embeddings_batch."""
    documents = [
        {"content": "Doc 1 content."},
        {"content": "Doc 2 content."},
        {"content": "Doc 3 content."},
    ]

    mock_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
    mock_batch_fn = AsyncMock(return_value=mock_embeddings)

    with patch("src.app.rag.ingest.generate_embeddings_batch", mock_batch_fn):
        await ingest_batch(session=session, documents=documents)

        # Verify batch function was called (not individual generate_embedding)
        assert mock_batch_fn.called
        assert mock_batch_fn.call_count == 1


@pytest.mark.asyncio
async def test_ingest_batch_preserves_metadata(session):
    """Test that batch ingestion preserves document metadata."""
    documents = [
        {
            "content": "Content 1",
            "title": "Title 1",
            "source_type": "manual",
            "source_path": "/path/1",
            "metadata": {"version": "1.0", "author": "Author 1"},
        },
        {
            "content": "Content 2",
            "title": "Title 2",
            "source_type": "procedure",
            "source_path": "/path/2",
            "metadata": {"version": "2.0", "author": "Author 2"},
        },
    ]

    mock_embeddings = [[0.1] * 1536, [0.2] * 1536]

    with patch("src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings):
        document_ids = await ingest_batch(session=session, documents=documents)

        # Verify metadata is preserved
        result = await session.execute(select(Document).order_by(Document.title))
        docs = result.scalars().all()

        assert docs[0].title == "Title 1"
        assert docs[0].source_type == "manual"
        assert docs[0].source_path == "/path/1"
        assert docs[0].meta == {"version": "1.0", "author": "Author 1"}

        assert docs[1].title == "Title 2"
        assert docs[1].source_type == "procedure"
        assert docs[1].source_path == "/path/2"
        assert docs[1].meta == {"version": "2.0", "author": "Author 2"}


@pytest.mark.asyncio
async def test_ingest_batch_chunk_embedding_count_match(session):
    """Test that the number of chunks equals the number of embeddings."""
    documents = [
        {"content": "Document 1 content. " * 30},
        {"content": "Document 2 content. " * 30},
    ]

    # Will be calculated based on actual chunks created
    # Mock will be called with actual chunk texts
    async def mock_generate_batch(texts):
        return [[0.1] * 1536 for _ in texts]

    with patch("src.app.rag.ingest.generate_embeddings_batch", side_effect=mock_generate_batch):
        await ingest_batch(session=session, documents=documents)

        # Count chunks and embeddings
        chunks_result = await session.execute(select(Chunk))
        chunks = chunks_result.scalars().all()

        embeddings_result = await session.execute(select(Embedding))
        embeddings = embeddings_result.scalars().all()

        assert len(chunks) == len(embeddings)


@pytest.mark.asyncio
async def test_ingest_batch_minimal_document_params(session):
    """Test batch ingestion with minimal document parameters."""
    documents = [
        {"content": "Only content 1"},
        {"content": "Only content 2"},
    ]

    mock_embeddings = [[0.1] * 1536, [0.2] * 1536]

    with patch("src.app.rag.ingest.generate_embeddings_batch", return_value=mock_embeddings):
        document_ids = await ingest_batch(session=session, documents=documents)

        assert len(document_ids) == 2

        result = await session.execute(select(Document))
        docs = result.scalars().all()

        for doc in docs:
            assert doc.content in ["Only content 1", "Only content 2"]
            assert doc.title is None
            assert doc.meta == {}


@pytest.mark.asyncio
async def test_ingest_batch_large_batch(session):
    """Test batch ingestion with many documents."""
    # Create 10 documents
    documents = [{"content": f"Document {i} content. " * 10, "title": f"Doc {i}"} for i in range(10)]

    # Mock embeddings dynamically
    async def mock_generate_batch(texts):
        return [[0.1] * 1536 for _ in texts]

    with patch("src.app.rag.ingest.generate_embeddings_batch", side_effect=mock_generate_batch):
        document_ids = await ingest_batch(session=session, documents=documents)

        assert len(document_ids) == 10

        result = await session.execute(select(Document))
        docs = result.scalars().all()
        assert len(docs) == 10


@pytest.mark.asyncio
async def test_ingest_batch_transaction_rollback_on_error(session):
    """Test that transaction rolls back on error."""
    documents = [
        {"content": "Doc 1"},
        {"content": "Doc 2"},
    ]

    # Mock to raise an error during embedding generation
    with patch("src.app.rag.ingest.generate_embeddings_batch", side_effect=Exception("API Error")):
        with pytest.raises(Exception, match="API Error"):
            await ingest_batch(session=session, documents=documents)

        # Rollback should have occurred - no documents should be saved
        await session.rollback()
        result = await session.execute(select(Document))
        docs = result.scalars().all()
        assert len(docs) == 0
