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
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    if not content or not content.strip():
        return []

    chunks: list[ChunkResult] = []
    start = 0
    chunk_index = 0

    while start < len(content):
        end = min(start + chunk_size, len(content))

        # Try to break at sentence boundary if not at end
        if end < len(content):
            # Look for sentence endings within the last 20% of the chunk
            search_start = start + int(chunk_size * 0.8)
            best_break = -1
            for sep in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                pos = content.rfind(sep, search_start, end)
                if pos > best_break:
                    best_break = pos + len(sep)

            if best_break > search_start:
                end = best_break

        chunk_content = content[start:end].strip()

        if chunk_content:
            chunks.append(
                ChunkResult(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={},
                )
            )
            chunk_index += 1

        # Move start position with overlap
        start = end - chunk_overlap if end < len(content) else len(content)

    return chunks
