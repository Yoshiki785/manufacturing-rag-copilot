"""Custom exceptions for Manufacturing RAG Copilot."""

from typing import Any


class RAGException(Exception):
    """Base exception for RAG-related errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize RAG exception.

        Args:
            message: Error message
            details: Additional error details
            original_error: Original exception that caused this error
        """
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(message)


class EmbeddingError(RAGException):
    """Error during embedding generation."""

    pass


class RetrievalError(RAGException):
    """Error during document retrieval."""

    pass


class GenerationError(RAGException):
    """Error during response generation."""

    pass


class IngestError(RAGException):
    """Error during document ingestion."""

    pass


class DatabaseError(RAGException):
    """Error during database operations."""

    pass


class AuthenticationError(RAGException):
    """Error during authentication."""

    pass


class RateLimitError(RAGException):
    """Error due to rate limiting."""

    pass


class ValidationError(RAGException):
    """Error during input validation."""

    pass
