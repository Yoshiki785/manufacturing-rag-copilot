"""Tests for embedding generation functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIError, RateLimitError

from src.app.rag.embed import generate_embedding


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
