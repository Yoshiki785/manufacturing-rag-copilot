"""Embedding generation for RAG pipeline."""

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for a text string.

    Args:
        text: Input text to embed.

    Returns:
        List of floats representing the embedding vector.

    Raises:
        OpenAIError: If embedding generation fails after retries.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )

    return response.data[0].embedding


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a batch.

    Args:
        texts: List of input texts to embed.

    Returns:
        List of embedding vectors corresponding to input texts.

    Note:
        OpenAI supports batching up to 2048 texts per request.
        This function handles larger batches by splitting them.
    """
    # TODO: Implement batched embedding generation
    # - Respect API rate limits
    # - Handle batch size limits
    # - Implement parallel processing for large batches

    raise NotImplementedError("Batch embedding not yet implemented")
