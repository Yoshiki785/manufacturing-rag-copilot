"""Tests for embedding generation functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIError, RateLimitError

from src.app.rag.embed import generate_embedding, generate_embeddings_batch


@pytest.mark.asyncio
async def test_generate_embedding_success():
    """Test successful embedding generation."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1] * 1536

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        embedding = await generate_embedding("Test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_generate_embedding_dimensions():
    """Test that embedding has correct dimensions (1536)."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1] * 1536

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        embedding = await generate_embedding("Another test")

        assert len(embedding) == 1536


@pytest.mark.asyncio
async def test_generate_embedding_retry_on_rate_limit():
    """Test retry behavior on rate limit error."""
    mock_client = MagicMock()
    mock_embeddings = AsyncMock()

    # First call raises RateLimitError, second succeeds
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1] * 1536

    mock_embeddings.create.side_effect = [
        RateLimitError(
            "Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        ),
        mock_response,
    ]
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        embedding = await generate_embedding("Test retry")

        # Should succeed after retry
        assert len(embedding) == 1536
        # Verify create was called twice (initial + retry)
        assert mock_embeddings.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_embedding_fails_after_max_retries():
    """Test that function fails after maximum retries."""
    from tenacity import RetryError

    mock_client = MagicMock()
    mock_embeddings = AsyncMock()

    # Always raise error
    mock_embeddings.create.side_effect = APIError(
        "API Error",
        request=MagicMock(),
        body=None,
    )
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        with pytest.raises(RetryError):
            await generate_embedding("Test fail")


@pytest.mark.asyncio
async def test_generate_embedding_empty_text():
    """Test embedding generation with empty text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.0] * 1536

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        embedding = await generate_embedding("")

        assert len(embedding) == 1536


@pytest.mark.asyncio
async def test_generate_embedding_long_text():
    """Test embedding generation with long text."""
    long_text = "Test sentence. " * 1000

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.5] * 1536

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        embedding = await generate_embedding(long_text)

        assert len(embedding) == 1536
        mock_embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_empty_list():
    """Test batch embedding with empty list."""
    result = await generate_embeddings_batch([])
    assert result == []


@pytest.mark.asyncio
async def test_generate_embeddings_batch_single_text():
    """Test batch embedding with single text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(["Single text"])

        assert len(result) == 1
        assert result[0] == [0.1, 0.2, 0.3]
        mock_embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_multiple_texts():
    """Test batch embedding with multiple texts under 2048 limit."""
    test_texts = [f"Text {i}" for i in range(100)]
    expected_embeddings = [[0.1 * i, 0.2 * i, 0.3 * i] for i in range(100)]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=emb) for emb in expected_embeddings]

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(test_texts)

        assert len(result) == 100
        assert result == expected_embeddings
        mock_embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_chunking_over_limit():
    """Test batch embedding splits correctly when over 2048 limit."""
    # Create 3000 texts to trigger batching (2048 + 952)
    test_texts = [f"Text {i}" for i in range(3000)]

    batch1_embeddings = [[0.1 * i] * 3 for i in range(2048)]
    batch2_embeddings = [[0.1 * i] * 3 for i in range(2048, 3000)]

    mock_client = MagicMock()
    mock_response1 = MagicMock()
    mock_response1.data = [MagicMock(embedding=emb) for emb in batch1_embeddings]

    mock_response2 = MagicMock()
    mock_response2.data = [MagicMock(embedding=emb) for emb in batch2_embeddings]

    mock_embeddings = AsyncMock()
    mock_embeddings.create.side_effect = [mock_response1, mock_response2]
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(test_texts)

        assert len(result) == 3000
        # Should be called twice: once for first 2048, once for remaining 952
        assert mock_embeddings.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_embeddings_batch_preserves_order():
    """Test that batch processing preserves order of texts."""
    test_texts = ["First", "Second", "Third"]
    expected_embeddings = [[1.0], [2.0], [3.0]]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=emb) for emb in expected_embeddings]

    mock_embeddings = AsyncMock()
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        result = await generate_embeddings_batch(test_texts)

        assert result[0] == [1.0]
        assert result[1] == [2.0]
        assert result[2] == [3.0]


@pytest.mark.asyncio
async def test_generate_embeddings_batch_error_handling():
    """Test error handling in batch processing."""
    mock_client = MagicMock()
    mock_embeddings = AsyncMock()
    mock_embeddings.create.side_effect = Exception("API Error")
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        with pytest.raises(Exception, match="API Error"):
            await generate_embeddings_batch(["Text 1", "Text 2"])


@pytest.mark.asyncio
async def test_generate_embeddings_batch_rate_limit_delay():
    """Test that rate limiting delay is applied between batches."""
    # Create enough texts to trigger 2 batches (2048 + 52)
    test_texts = [f"Text {i}" for i in range(2100)]

    batch1_embeddings = [[0.1] * 3 for _ in range(2048)]
    batch2_embeddings = [[0.2] * 3 for _ in range(52)]

    mock_client = MagicMock()
    mock_response1 = MagicMock()
    mock_response1.data = [MagicMock(embedding=emb) for emb in batch1_embeddings]

    mock_response2 = MagicMock()
    mock_response2.data = [MagicMock(embedding=emb) for emb in batch2_embeddings]

    mock_embeddings = AsyncMock()
    mock_embeddings.create.side_effect = [mock_response1, mock_response2]
    mock_client.embeddings = mock_embeddings

    with patch("src.app.rag.embed.AsyncOpenAI", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await generate_embeddings_batch(test_texts)

            assert len(result) == 2100
            # Sleep should be called once (for the second batch)
            mock_sleep.assert_called_once_with(1)
