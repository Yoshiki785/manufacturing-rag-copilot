"""Document chunking utilities for RAG pipeline."""

from dataclasses import dataclass

from src.app.core.config import settings


@dataclass
class ChunkResult:
    """Result of chunking a document."""

    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict


def chunk_document(
    content: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[ChunkResult]:
    """
    Split document content into overlapping chunks.

    Args:
        content: The document text to chunk.
        chunk_size: Maximum size of each chunk in characters.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of ChunkResult objects containing chunk data.

    Note:
        Uses sentence-aware splitting to avoid breaking mid-sentence
        when possible. Falls back to character splitting for very long
        sentences.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    # TODO: Implement sentence-aware chunking
    # - Split on sentence boundaries (., !, ?)
    # - Respect chunk_size limits
    # - Apply overlap between chunks
    # - Handle edge cases (code blocks, tables, lists)

    raise NotImplementedError("Chunking not yet implemented")


def chunk_for_manufacturing(content: str) -> list[ChunkResult]:
    """
    Chunk content with manufacturing-domain optimizations.

    Args:
        content: Manufacturing document text (specs, procedures, etc.)

    Returns:
        List of ChunkResult objects optimized for manufacturing content.

    Note:
        Preserves structure of:
        - Part numbers and specifications
        - Step-by-step procedures
        - Safety warnings and notes
        - Technical tables and lists
    """
    # TODO: Implement manufacturing-specific chunking
    raise NotImplementedError("Manufacturing chunking not yet implemented")
