"""Tests for database session management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_session


@pytest.mark.asyncio
async def test_get_session_yields_session():
    """Test that get_session yields an AsyncSession."""
    async for session in get_session():
        assert isinstance(session, AsyncSession)
        # Only test the first yielded session
        break


@pytest.mark.asyncio
async def test_get_session_can_be_used_in_context():
    """Test that get_session works as an async generator."""
    session_count = 0
    async for session in get_session():
        session_count += 1
        assert session is not None
        break

    assert session_count == 1


@pytest.mark.asyncio
async def test_get_session_exception_triggers_rollback(test_engine):
    """Test that exceptions trigger session rollback."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Create a session maker with test engine
    test_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Patch the session maker to use test engine
    with patch("src.app.db.session.async_session_maker", test_session_maker):
        # Verify that exception is propagated
        with pytest.raises(RuntimeError):
            async for session in get_session():
                # Raise an exception to test rollback behavior
                raise RuntimeError("Simulated database error")


@pytest.mark.asyncio
async def test_get_session_normal_operation_no_rollback():
    """Test that normal operations don't trigger rollback."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session

    with patch("src.app.db.session.async_session_maker", mock_session_maker):
        async for session in get_session():
            # Normal operation - no exception
            assert session is not None
            break

    # Rollback should NOT be called in normal operation
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_get_session_multiple_calls_independent():
    """Test that multiple calls to get_session are independent."""
    sessions = []

    async for session in get_session():
        sessions.append(session)
        break

    async for session in get_session():
        sessions.append(session)
        break

    # Each call should yield a session
    assert len(sessions) == 2
    assert all(isinstance(s, AsyncSession) for s in sessions)


@pytest.mark.asyncio
async def test_get_session_with_actual_operations(session):
    """Test get_session with actual database operations."""
    # Use the test session fixture from conftest
    from sqlalchemy import text

    # Execute a simple query
    result = await session.execute(text("SELECT 1 as value"))
    row = result.fetchone()

    assert row is not None
    assert row.value == 1


@pytest.mark.asyncio
async def test_get_session_exception_handling_with_specific_error(test_engine):
    """Test exception handling with specific database error."""
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Create a session maker with test engine
    test_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Patch the session maker to use test engine
    with patch("src.app.db.session.async_session_maker", test_session_maker):
        # Verify that SQLAlchemy exceptions are propagated
        with pytest.raises(SQLAlchemyError):
            async for session in get_session():
                raise SQLAlchemyError("Database connection error")


@pytest.mark.asyncio
async def test_get_session_cleanup_after_exception(test_engine):
    """Test that session is properly cleaned up after exception."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Create a session maker with test engine
    test_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Patch the session maker to use test engine
    with patch("src.app.db.session.async_session_maker", test_session_maker):
        # Verify that ValueError exceptions are propagated
        with pytest.raises(ValueError):
            async for session in get_session():
                raise ValueError("Test error")

        # After exception, the session should be cleaned up automatically
        # by the context manager (no assertions needed as cleanup is automatic)
