"""Vector similarity retrieval for RAG pipeline."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.exceptions import DatabaseError, RetrievalError
from src.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Result of a retrieval query."""

    chunk_id: UUID
    document_id: UUID
    content: str
    similarity_score: float
    metadata: dict


async def retrieve_similar_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    top_k: int | None = None,
    similarity_threshold: float | None = None,
) -> list[RetrievalResult]:
    """
    Retrieve chunks most similar to the query embedding.

    Args:
        session: Database session for queries.
        query_embedding: Vector representation of the query.
        top_k: Maximum number of results to return.
        similarity_threshold: Minimum similarity score for results.

    Returns:
        List of RetrievalResult objects sorted by similarity.

    Note:
        Uses pgvector's cosine similarity for efficient vector search.
        Results are filtered by similarity threshold before ranking.
    """
    top_k = top_k or settings.top_k_retrieval
    similarity_threshold = similarity_threshold or settings.similarity_threshold

    logger.info(f"Retrieving similar chunks: top_k={top_k}, threshold={similarity_threshold}")

    # Build SQL query using pgvector cosine distance operator (<=>)
    # Cosine distance ranges from 0 (identical) to 2 (opposite)
    # Similarity = 1 - distance (ranges from -1 to 1)
    query = text("""
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            c.meta,
            1 - (e.embedding <=> :query_embedding) AS similarity_score
        FROM embeddings e
        JOIN chunks c ON e.chunk_id = c.id
        JOIN documents d ON c.document_id = d.id
        WHERE 1 - (e.embedding <=> :query_embedding) >= :threshold
        ORDER BY similarity_score DESC
        LIMIT :limit
    """)

    try:
        result = await session.execute(
            query,
            {
                "query_embedding": str(query_embedding),
                "threshold": similarity_threshold,
                "limit": top_k,
            },
        )
        rows = result.fetchall()

        retrieval_results = []
        for row in rows:
            retrieval_results.append(
                RetrievalResult(
                    chunk_id=row.chunk_id,
                    document_id=row.document_id,
                    content=row.content,
                    similarity_score=float(row.similarity_score),
                    metadata=row.meta or {},
                )
            )

        logger.info(f"Retrieved {len(retrieval_results)} chunks")
        return retrieval_results

    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        raise RetrievalError(
            message="Failed to retrieve similar chunks",
            details={
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
            },
            original_error=e,
        )


async def retrieve_with_reranking(
    session: AsyncSession,
    query: str,
    query_embedding: list[float],
    top_k: int | None = None,
) -> list[RetrievalResult]:
    """
    Retrieve and rerank chunks using cross-encoder scoring.

    Args:
        session: Database session for queries.
        query: Original query text for reranking.
        query_embedding: Vector representation of the query.
        top_k: Maximum number of final results.

    Returns:
        List of RetrievalResult objects after reranking.

    Note:
        First retrieves more candidates (e.g., 3x top_k) using vector
        search, then reranks using a cross-encoder model for better
        relevance scoring.
    """
    # TODO: Implement retrieval with reranking
    raise NotImplementedError("Reranking not yet implemented")
