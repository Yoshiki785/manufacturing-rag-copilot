"""Test fixtures and configuration."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.app.db.models import Base
from src.app.db.session import get_session
from src.app.main import app

# Test database URL - PostgreSQL with pgvector support
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/manufacturing_rag_test",
)


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create pgvector extension and all tables
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session_maker(test_engine):
    """Create a test session maker."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="function")
async def session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with overridden dependencies."""
    from src.app.core.security import verify_api_key

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    async def override_verify_api_key() -> str:
        """Bypass API key verification in tests."""
        return "test-api-key"

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()

    # Mock embeddings
    embedding_mock = AsyncMock()
    embedding_response = MagicMock()
    embedding_response.data = [MagicMock()]
    embedding_response.data[0].embedding = [0.1] * 1536
    embedding_mock.create.return_value = embedding_response
    client.embeddings = embedding_mock

    # Mock chat completions
    chat_mock = AsyncMock()
    chat_response = MagicMock()
    chat_response.choices = [MagicMock()]
    chat_response.choices[0].message.content = "Test response [Source 1]"
    chat_response.usage = MagicMock()
    chat_response.usage.prompt_tokens = 100
    chat_response.usage.completion_tokens = 50
    chat_response.usage.total_tokens = 150
    chat_mock.create.return_value = chat_response
    client.chat = MagicMock()
    client.chat.completions = chat_mock

    return client


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "id": uuid4(),
        "title": "Test Document",
        "content": "This is a test document. It contains multiple sentences. This helps test chunking.",
        "source_type": "manual",
        "source_path": "/test/path.txt",
        "meta": {"key": "value"},
    }


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    return [
        {
            "id": uuid4(),
            "content": "First chunk content.",
            "chunk_index": 0,
            "start_char": 0,
            "end_char": 20,
        },
        {
            "id": uuid4(),
            "content": "Second chunk content.",
            "chunk_index": 1,
            "start_char": 15,
            "end_char": 37,
        },
    ]


@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing."""
    return [0.1] * 1536
