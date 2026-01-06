"""Tests for response generation functionality."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.app.rag.generate import generate_response
from src.app.rag.retrieve import RetrievalResult


@pytest.mark.asyncio
async def test_generate_response_success():
    """Test successful response generation."""
    context_chunks = [
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="The torque specification is 45 Nm.",
            similarity_score=0.9,
            metadata={},
        ),
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Tighten bolts in a cross pattern.",
            similarity_score=0.85,
            metadata={},
        ),
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "The torque is 45 Nm [Source 1]. Use a cross pattern [Source 2]."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    mock_chat = AsyncMock()
    mock_chat.create.return_value = mock_response
    mock_client.chat = MagicMock()
    mock_client.chat.completions = mock_chat

    with patch("src.app.rag.generate.AsyncOpenAI", return_value=mock_client):
        result = await generate_response(
            query="What is the torque specification?",
            context_chunks=context_chunks,
        )

        assert result.answer is not None
        assert isinstance(result.citations, list)
        assert isinstance(result.token_usage, dict)
        assert result.token_usage["total_tokens"] == 150


@pytest.mark.asyncio
async def test_generate_response_extracts_citations():
    """Test that citations are extracted correctly."""
    context_chunks = [
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="First chunk content.",
            similarity_score=0.9,
            metadata={},
        ),
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Second chunk content.",
            similarity_score=0.85,
            metadata={},
        ),
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Answer with [Source 1] and [Source 2]."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 120

    mock_chat = AsyncMock()
    mock_chat.create.return_value = mock_response
    mock_client.chat = MagicMock()
    mock_client.chat.completions = mock_chat

    with patch("src.app.rag.generate.AsyncOpenAI", return_value=mock_client):
        result = await generate_response(
            query="Test query",
            context_chunks=context_chunks,
        )

        assert len(result.citations) == 2
        assert result.citations[0]["source"] == 1
        assert result.citations[1]["source"] == 2


@pytest.mark.asyncio
async def test_generate_response_token_usage():
    """Test that token usage is tracked correctly."""
    context_chunks = [
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Test content.",
            similarity_score=0.9,
            metadata={},
        ),
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test answer."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 200
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 275

    mock_chat = AsyncMock()
    mock_chat.create.return_value = mock_response
    mock_client.chat = MagicMock()
    mock_client.chat.completions = mock_chat

    with patch("src.app.rag.generate.AsyncOpenAI", return_value=mock_client):
        result = await generate_response(
            query="Test query",
            context_chunks=context_chunks,
        )

        assert result.token_usage["prompt_tokens"] == 200
        assert result.token_usage["completion_tokens"] == 75
        assert result.token_usage["total_tokens"] == 275


@pytest.mark.asyncio
async def test_generate_response_with_conversation_history():
    """Test response generation with conversation history."""
    context_chunks = [
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Test content.",
            similarity_score=0.9,
            metadata={},
        ),
    ]

    conversation_history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"},
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Contextual answer."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 30
    mock_response.usage.total_tokens = 180

    mock_chat = AsyncMock()
    mock_chat.create.return_value = mock_response
    mock_client.chat = MagicMock()
    mock_client.chat.completions = mock_chat

    with patch("src.app.rag.generate.AsyncOpenAI", return_value=mock_client):
        result = await generate_response(
            query="Follow-up question",
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )

        assert result.answer == "Contextual answer."
        # Verify that chat.completions.create was called with history
        call_args = mock_chat.create.call_args
        messages = call_args.kwargs["messages"]
        # Should include system, history, and new message
        assert len(messages) >= 4


@pytest.mark.asyncio
async def test_generate_response_no_citations():
    """Test response without citations."""
    context_chunks = [
        RetrievalResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Test content.",
            similarity_score=0.9,
            metadata={},
        ),
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Answer without citations."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 120

    mock_chat = AsyncMock()
    mock_chat.create.return_value = mock_response
    mock_client.chat = MagicMock()
    mock_client.chat.completions = mock_chat

    with patch("src.app.rag.generate.AsyncOpenAI", return_value=mock_client):
        result = await generate_response(
            query="Test query",
            context_chunks=context_chunks,
        )

        assert len(result.citations) == 0


@pytest.mark.asyncio
async def test_generate_response_empty_context():
    """Test response generation with empty context."""
    context_chunks = []

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "No context available."
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 10
    mock_response.usage.total_tokens = 60

    mock_chat = AsyncMock()
    mock_chat.create.return_value = mock_response
    mock_client.chat = MagicMock()
    mock_client.chat.completions = mock_chat

    with patch("src.app.rag.generate.AsyncOpenAI", return_value=mock_client):
        result = await generate_response(
            query="Test query",
            context_chunks=context_chunks,
        )

        assert result.answer is not None
        assert len(result.citations) == 0
