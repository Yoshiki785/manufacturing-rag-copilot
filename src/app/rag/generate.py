"""Response generation for RAG pipeline."""

from dataclasses import dataclass

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.app.core.config import settings
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

    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {query}",
    })

    # TODO: Complete implementation
    # - Call OpenAI chat completion
    # - Extract citations from response
    # - Track token usage

    raise NotImplementedError("Generation not yet implemented")


def _format_context(chunks: list[RetrievalResult]) -> str:
    """Format retrieved chunks into context string with source numbers."""
    formatted = []
    for i, chunk in enumerate(chunks, 1):
        formatted.append(f"[Source {i}]\n{chunk.content}\n")
    return "\n".join(formatted)
