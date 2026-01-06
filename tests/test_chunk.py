"""Tests for document chunking functionality."""

from src.app.rag.chunk import chunk_document


def test_chunk_document_normal():
    """Test normal document chunking."""
    content = (
        "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
    )
    chunks = chunk_document(content, chunk_size=50, chunk_overlap=10)

    assert len(chunks) > 0
    assert all(chunk.content for chunk in chunks)
    assert all(chunk.chunk_index >= 0 for chunk in chunks)
    assert chunks[0].start_char == 0


def test_chunk_document_empty_string():
    """Test chunking empty string."""
    chunks = chunk_document("")
    assert len(chunks) == 0


def test_chunk_document_whitespace_only():
    """Test chunking whitespace-only string."""
    chunks = chunk_document("   \n\n  \t  ")
    assert len(chunks) == 0


def test_chunk_document_overlap():
    """Test that chunks have proper overlap."""
    content = "A" * 200  # Long content
    chunks = chunk_document(content, chunk_size=100, chunk_overlap=20)

    assert len(chunks) >= 2
    # Check that there is overlap between consecutive chunks
    for i in range(len(chunks) - 1):
        current_end = chunks[i].end_char
        next_start = chunks[i + 1].start_char
        # Next chunk should start before current ends (overlap)
        assert next_start < current_end


def test_chunk_document_sentence_boundary():
    """Test that chunking prefers sentence boundaries."""
    content = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here. Fifth sentence here."
    chunks = chunk_document(content, chunk_size=60, chunk_overlap=5)

    # Check that chunks tend to end at sentence boundaries
    # At least some chunks should end with punctuation
    ends_with_punctuation = [chunk.content.rstrip().endswith((".", "!", "?")) for chunk in chunks]
    assert any(ends_with_punctuation)


def test_chunk_document_indexes_sequential():
    """Test that chunk indexes are sequential."""
    content = "This is a test document with multiple sentences. " * 10
    chunks = chunk_document(content, chunk_size=100, chunk_overlap=10)

    indexes = [chunk.chunk_index for chunk in chunks]
    assert indexes == list(range(len(chunks)))


def test_chunk_document_positions_valid():
    """Test that start_char and end_char are valid positions."""
    content = "This is a test document with content."
    chunks = chunk_document(content, chunk_size=20, chunk_overlap=5)

    for chunk in chunks:
        assert 0 <= chunk.start_char < len(content)
        assert chunk.start_char < chunk.end_char <= len(content)
        # Verify the content matches the positions
        expected_content = content[chunk.start_char : chunk.end_char].strip()
        assert chunk.content == expected_content


def test_chunk_document_custom_sizes():
    """Test chunking with custom chunk size and overlap."""
    content = "This is a test. " * 50
    chunk_size = 80
    chunk_overlap = 15

    chunks = chunk_document(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for chunk in chunks:
        # Each chunk should be roughly chunk_size or less
        assert (
            len(chunk.content) <= chunk_size + 50
        )  # Allow some flexibility for sentence boundaries


def test_chunk_document_metadata_exists():
    """Test that chunks have metadata dict."""
    content = "This is a test document."
    chunks = chunk_document(content)

    for chunk in chunks:
        assert isinstance(chunk.metadata, dict)
