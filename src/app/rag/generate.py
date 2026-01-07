"""Response generation for RAG pipeline."""

import re
from dataclasses import dataclass

from openai import AsyncOpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_exponential

from src.app.core.config import settings
from src.app.core.exceptions import GenerationError
from src.app.core.logging import get_logger
from src.app.rag.retrieve import RetrievalResult

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a manufacturing domain expert assistant. Your role is to provide accurate, helpful answers based on the provided context documents.

IMPORTANT RULES:
1. Only answer based on the provided context. If the context doesn't contain enough information, say so.
2. Always cite your sources using [Source N] notation, where N corresponds to the context chunk number.
3. Be precise with technical details, part numbers, and specifications.
4. If safety information is relevant, always include it prominently.
5. Structure your response clearly with headings if appropriate."""


@dataclass
class GenerationResult:
    """Result of response generation."""

    answer: str
    citations: list[dict]
    token_usage: dict


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def generate_response(
    query: str,
    context_chunks: list[RetrievalResult],
    conversation_history: list[dict] | None = None,
) -> GenerationResult:
    """
    Generate a response using retrieved context and LLM.

    Args:
        query: User's question.
        context_chunks: Retrieved context chunks with metadata.
        conversation_history: Optional previous messages for context.

    Returns:
        GenerationResult with answer, citations, and token usage.

    Note:
        Uses the system prompt to enforce citation requirements.
        Formats context chunks with source numbers for reference.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Format context for the prompt
    context_text = _format_context(context_chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context_text}\n\nQuestion: {query}",
        }
    )

    try:
        logger.info(f"Generating response for query: {query[:50]}...")

        response = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content or ""

        # Extract [Source N] citations from the response
        citation_pattern = r"\[Source\s+(\d+)\]"
        source_numbers = set(int(m) for m in re.findall(citation_pattern, answer))

        # Build citation list with chunk info
        citations = []
        for source_num in sorted(source_numbers):
            idx = source_num - 1  # Convert 1-based to 0-based index
            if 0 <= idx < len(context_chunks):
                chunk = context_chunks[idx]
                citations.append(
                    {
                        "source": source_num,
                        "chunk_id": str(chunk.chunk_id),
                        "content": chunk.content[:200] + "..."
                        if len(chunk.content) > 200
                        else chunk.content,
                    }
                )

        # Track token usage
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        logger.info(
            f"Generated response with {len(citations)} citations, {token_usage['total_tokens']} tokens"
        )

        return GenerationResult(
            answer=answer,
            citations=citations,
            token_usage=token_usage,
        )

    except Exception as e:
        logger.error(f"Error during response generation: {e}")
        raise GenerationError(
            message="Failed to generate response",
            details={
                "query_length": len(query),
                "context_chunks": len(context_chunks),
                "model": settings.openai_chat_model,
            },
            original_error=e,
        )


def _format_context(chunks: list[RetrievalResult]) -> str:
    """Format retrieved chunks into context string with source numbers."""
    formatted = []
    for i, chunk in enumerate(chunks, 1):
        formatted.append(f"[Source {i}]\n{chunk.content}\n")
    return "\n".join(formatted)
