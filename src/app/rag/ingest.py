"""Document ingestion pipeline for RAG system."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.logging import get_logger
from src.app.db.models import Chunk, Document, Embedding
from src.app.rag.chunk import chunk_document
from src.app.rag.embed import generate_embedding

logger = get_logger(__name__)


async def ingest_document(
    session: AsyncSession,
    content: str,
    title: str | None = None,
    source_type: str | None = None,
    source_path: str | None = None,
    metadata: dict | None = None,
) -> UUID:
    """
    Ingest a document into the RAG system.

    Args:
        session: Database session.
        content: Document text content.
        title: Optional document title.
        source_type: Type of source (e.g., 'manual', 'procedure', 'spec').
        source_path: Original file path or URL.
        metadata: Additional metadata dictionary.

    Returns:
        UUID of the created document.

    Process:
        1. Create document record
        2. Chunk the document content
        3. Generate embeddings for each chunk
        4. Store chunks and embeddings in database
    """
    metadata = metadata or {}

    # Create document
    document = Document(
        id=uuid4(),
        title=title,
        content=content,
        source_type=source_type,
        source_path=source_path,
        metadata=metadata,
    )
    session.add(document)

    # Chunk document
    chunks = chunk_document(content)

    # Process each chunk
    for chunk_data in chunks:
        chunk = Chunk(
            id=uuid4(),
            document_id=document.id,
            content=chunk_data.content,
            chunk_index=chunk_data.chunk_index,
            start_char=chunk_data.start_char,
            end_char=chunk_data.end_char,
            metadata=chunk_data.metadata,
        )
        session.add(chunk)

        # Generate and store embedding
        embedding_vector = await generate_embedding(chunk_data.content)
        embedding = Embedding(
            id=uuid4(),
            chunk_id=chunk.id,
            embedding=embedding_vector,
            model_name="text-embedding-3-small",
        )
        session.add(embedding)

    await session.commit()
    logger.info(f"Ingested document {document.id} with {len(chunks)} chunks")

    return document.id


async def ingest_batch(
    session: AsyncSession,
    documents: list[dict],
) -> list[UUID]:
    """
    Ingest multiple documents in batch.

    Args:
        session: Database session.
        documents: List of document dicts with content and metadata.

    Returns:
        List of created document UUIDs.

    Note:
        Optimizes embedding generation by batching API calls.
    """
    # TODO: Implement batch ingestion with optimized embedding calls
    raise NotImplementedError("Batch ingestion not yet implemented")
