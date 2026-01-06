"""Tests for logging configuration."""

import logging
from unittest.mock import MagicMock, patch

from src.app.core.logging import get_logger, log_event, setup_logging


def test_setup_logging_creates_logger():
    """Test that setup_logging creates and configures a logger."""
    logger = setup_logging()

    assert logger is not None
    assert logger.name == "manufacturing_rag"
    assert isinstance(logger, logging.Logger)


def test_setup_logging_sets_log_level():
    """Test that logger is configured with correct log level."""
    logger = setup_logging()

    # Default log level from settings should be applied
    assert logger.level in [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]


def test_setup_logging_adds_handler():
    """Test that logger has stream handler configured."""
    logger = setup_logging()

    assert len(logger.handlers) > 0
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_setup_logging_handler_has_formatter():
    """Test that handler has correct formatter."""
    logger = setup_logging()

    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            assert handler.formatter is not None
            assert "%(asctime)s" in handler.formatter._fmt
            assert "%(levelname)s" in handler.formatter._fmt
            assert "%(name)s" in handler.formatter._fmt
            assert "%(message)s" in handler.formatter._fmt


def test_setup_logging_does_not_duplicate_handlers():
    """Test that calling setup_logging multiple times doesn't duplicate handlers."""
    logger1 = setup_logging()
    handler_count_1 = len(logger1.handlers)

    logger2 = setup_logging()
    handler_count_2 = len(logger2.handlers)

    # Should be the same logger instance with same handler count
    assert logger1 is logger2
    assert handler_count_1 == handler_count_2


def test_get_logger_returns_child_logger():
    """Test that get_logger returns a properly named child logger."""
    logger = get_logger("test_module")

    assert logger.name == "manufacturing_rag.test_module"
    assert isinstance(logger, logging.Logger)


def test_get_logger_different_names():
    """Test that get_logger returns different loggers for different names."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert logger1.name != logger2.name
    assert logger1.name == "manufacturing_rag.module1"
    assert logger2.name == "manufacturing_rag.module2"


def test_log_event_logs_message_without_kwargs():
    """Test log_event with just event message."""
    mock_logger = MagicMock(spec=logging.Logger)

    log_event(mock_logger, "Test event")

    mock_logger.info.assert_called_once_with("Test event")


def test_log_event_logs_message_with_kwargs():
    """Test log_event with event message and additional context."""
    mock_logger = MagicMock(spec=logging.Logger)

    log_event(mock_logger, "User action", user_id="123", action="login")

    # Should be called with formatted string including key-value pairs
    call_args = mock_logger.info.call_args[0][0]
    assert "User action" in call_args
    assert "user_id=123" in call_args
    assert "action=login" in call_args


def test_log_event_formats_multiple_kwargs():
    """Test log_event formats multiple kwargs correctly."""
    mock_logger = MagicMock(spec=logging.Logger)

    log_event(
        mock_logger,
        "Database query",
        table="documents",
        operation="INSERT",
        rows=5,
    )

    call_args = mock_logger.info.call_args[0][0]
    assert "Database query" in call_args
    assert "table=documents" in call_args
    assert "operation=INSERT" in call_args
    assert "rows=5" in call_args
    # Check that kwargs are separated by " | "
    assert " | " in call_args


def test_log_event_with_empty_kwargs():
    """Test log_event with empty kwargs dict."""
    mock_logger = MagicMock(spec=logging.Logger)

    log_event(mock_logger, "Simple event")

    mock_logger.info.assert_called_once_with("Simple event")


@patch("src.app.core.logging.settings")
def test_setup_logging_respects_log_level_setting(mock_settings):
    """Test that setup_logging respects log level from settings."""
    mock_settings.log_level = "DEBUG"

    # Clear any existing handlers to test fresh
    logger = logging.getLogger("manufacturing_rag")
    logger.handlers.clear()

    logger = setup_logging()

    assert logger.level == logging.DEBUG


@patch("src.app.core.logging.settings")
def test_setup_logging_with_warning_level(mock_settings):
    """Test setup_logging with WARNING log level."""
    mock_settings.log_level = "WARNING"

    # Clear any existing handlers to test fresh
    logger = logging.getLogger("manufacturing_rag")
    logger.handlers.clear()

    logger = setup_logging()

    assert logger.level == logging.WARNING
