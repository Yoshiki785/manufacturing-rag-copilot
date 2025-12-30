"""Structured logging configuration."""

import logging
import sys
from typing import Any

from src.app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured logging for the application."""
    logger = logging.getLogger("manufacturing_rag")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"manufacturing_rag.{name}")


def log_event(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """Log a structured event with additional context."""
    extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"{event} | {extra_info}" if extra_info else event)
