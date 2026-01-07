"""Embedding generation for RAG pipeline."""

import time

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.app.core.config import settings
from src.app.core.exceptions import EmbeddingError
from src.app.core.logging import get_logger
from src.app.core.metrics import (
    embedding_batch_size,
    embedding_generation_duration_seconds,
    embedding_generations_total,
)

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
        EmbeddingError: If embedding generation fails after retries.
    """
    start_time = time.time()
    model = settings.openai_embedding_model

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        response = await client.embeddings.create(
            model=model,
            input=text,
        )

        duration = time.time() - start_time
        embedding_generation_duration_seconds.labels(model=model).observe(duration)
        embedding_generations_total.labels(model=model, status="success").inc()

        return response.data[0].embedding

    except Exception as e:
        embedding_generations_total.labels(model=model, status="error").inc()
        logger.error(f"Failed to generate embedding: {e}")
        raise EmbeddingError(
            message="Failed to generate embedding",
            details={"text_length": len(text), "model": model},
            original_error=e,
        )


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
        Uses parallel processing for multiple batches.
    """
    import asyncio

    if not texts:
        return []

    # Record batch size
    embedding_batch_size.observe(len(texts))

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    model = settings.openai_embedding_model

    # OpenAI API limit: 2048 texts per request
    BATCH_SIZE = 2048
    batches = []

    # Split texts into batches
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        batches.append(batch)

    logger.info(
        f"Generating embeddings for {len(texts)} texts in {len(batches)} batch(es)"
    )

    async def process_batch(batch: list[str], batch_idx: int) -> list[list[float]]:
        """Process a single batch of texts."""
        try:
            # Add delay between batches to respect rate limits
            if batch_idx > 0:
                await asyncio.sleep(1)  # 1 second delay between batches

            response = await client.embeddings.create(
                model=settings.openai_embedding_model,
                input=batch,
            )

            # Extract embeddings in the same order as input
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Batch {batch_idx + 1}/{len(batches)}: Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Error processing batch {batch_idx + 1}: {e}")
            raise EmbeddingError(
                message=f"Failed to process batch {batch_idx + 1}",
                details={
                    "batch_index": batch_idx,
                    "batch_size": len(batch),
                    "model": settings.openai_embedding_model,
                },
                original_error=e,
            )

    # Process all batches in parallel
    batch_results = await asyncio.gather(
        *[process_batch(batch, idx) for idx, batch in enumerate(batches)]
    )

    # Flatten results while maintaining order
    all_embeddings = []
    for batch_result in batch_results:
        all_embeddings.extend(batch_result)

    logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
    return all_embeddings
