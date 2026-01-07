"""Document ingestion pipeline for RAG system."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import IngestError
from src.app.core.logging import get_logger
from src.app.db.models import Chunk, Document, Embedding
from src.app.rag.chunk import chunk_document
from src.app.rag.embed import generate_embedding, generate_embeddings_batch

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

    Raises:
        IngestError: If document ingestion fails.

    Process:
        1. Create document record
        2. Chunk the document content
        3. Generate embeddings for each chunk
        4. Store chunks and embeddings in database
    """
    try:
        metadata = metadata or {}

        # Create document
        document = Document(
            id=uuid4(),
            title=title,
            content=content,
            source_type=source_type,
            source_path=source_path,
            meta=metadata,
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
                meta=chunk_data.metadata,
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

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to ingest document: {e}")
        raise IngestError(
            message="Failed to ingest document",
            details={
                "title": title,
                "content_length": len(content),
                "source_type": source_type,
            },
            original_error=e,
        )


async def ingest_batch(
    session: AsyncSession,
    documents: list[dict],
) -> list[UUID]:
    """
    Ingest multiple documents in batch.

    Args:
        session: Database session.
        documents: List of document dicts with content and metadata.
            Each dict should contain:
            - content: str (required)
            - title: str (optional)
            - source_type: str (optional)
            - source_path: str (optional)
            - metadata: dict (optional)

    Returns:
        List of created document UUIDs.

    Raises:
        IngestError: If batch ingestion fails.

    Note:
        Optimizes embedding generation by batching API calls.
        Processes all documents, chunks them, then generates embeddings
        in batches for better performance.
    """
    if not documents:
        return []

    try:
        logger.info(f"Starting batch ingestion of {len(documents)} documents")

        # Step 1: Create all Document objects
        doc_objects = []
        for doc_dict in documents:
            doc_id = uuid4()
            document = Document(
                id=doc_id,
                title=doc_dict.get("title"),
                content=doc_dict["content"],
                source_type=doc_dict.get("source_type"),
                source_path=doc_dict.get("source_path"),
                meta=doc_dict.get("metadata", {}),
            )
            doc_objects.append(document)
            session.add(document)

        logger.info(f"Created {len(doc_objects)} document objects")

        # Step 2: Chunk all documents
        all_chunks_data = []
        chunk_to_doc_mapping = []  # Track which document each chunk belongs to

        for doc in doc_objects:
            chunks = chunk_document(doc.content)
            for chunk_data in chunks:
                all_chunks_data.append(chunk_data)
                chunk_to_doc_mapping.append(doc.id)

        logger.info(f"Generated {len(all_chunks_data)} chunks from all documents")

        # Step 3: Extract all chunk texts for batch embedding
        chunk_texts = [chunk_data.content for chunk_data in all_chunks_data]

        # Step 4: Generate embeddings for all chunks in batch
        logger.info("Generating embeddings for all chunks...")
        all_embeddings = await generate_embeddings_batch(chunk_texts)

        if len(all_embeddings) != len(all_chunks_data):
            raise ValueError(
                f"Embedding count mismatch: got {len(all_embeddings)}, expected {len(all_chunks_data)}"
            )

        # Step 5: Create Chunk and Embedding objects
        chunk_objects = []
        embedding_objects = []

        for i, (chunk_data, doc_id, embedding_vector) in enumerate(
            zip(all_chunks_data, chunk_to_doc_mapping, all_embeddings)
        ):
            chunk_id = uuid4()

            # Create Chunk
            chunk = Chunk(
                id=chunk_id,
                document_id=doc_id,
                content=chunk_data.content,
                chunk_index=chunk_data.chunk_index,
                start_char=chunk_data.start_char,
                end_char=chunk_data.end_char,
                meta=chunk_data.metadata,
            )
            chunk_objects.append(chunk)

            # Create Embedding
            embedding = Embedding(
                id=uuid4(),
                chunk_id=chunk_id,
                embedding=embedding_vector,
                model_name="text-embedding-3-small",
            )
            embedding_objects.append(embedding)

        # Step 6: Bulk insert all chunks and embeddings
        logger.info(
            f"Inserting {len(chunk_objects)} chunks and {len(embedding_objects)} embeddings"
        )
        session.add_all(chunk_objects)
        session.add_all(embedding_objects)

        # Step 7: Commit transaction
        await session.commit()

        document_ids = [doc.id for doc in doc_objects]
        logger.info(
            f"Successfully ingested {len(document_ids)} documents with "
            f"{len(chunk_objects)} chunks total"
        )

        return document_ids

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to ingest batch: {e}")
        raise IngestError(
            message="Failed to ingest batch of documents",
            details={
                "document_count": len(documents),
                "total_chunks": len(all_chunks_data) if "all_chunks_data" in locals() else 0,
            },
            original_error=e,
        )
