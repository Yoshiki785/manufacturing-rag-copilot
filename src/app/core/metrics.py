"""Prometheus metrics for Manufacturing RAG Copilot."""

from prometheus_client import Counter, Histogram, Gauge

# Request metrics (custom, in addition to instrumentator defaults)
rag_requests_total = Counter(
    "rag_requests_total",
    "Total number of RAG requests",
    ["endpoint", "status"],
)

# Embedding metrics
embedding_generations_total = Counter(
    "embedding_generations_total",
    "Total number of embeddings generated",
    ["model", "status"],
)

embedding_generation_duration_seconds = Histogram(
    "embedding_generation_duration_seconds",
    "Time spent generating embeddings",
    ["model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

embedding_batch_size = Histogram(
    "embedding_batch_size",
    "Number of texts in embedding batch",
    buckets=(1, 10, 50, 100, 500, 1000, 2048),
)

# Document ingestion metrics
documents_ingested_total = Counter(
    "documents_ingested_total",
    "Total number of documents ingested",
    ["status"],
)

chunks_created_total = Counter(
    "chunks_created_total",
    "Total number of chunks created",
)

document_ingestion_duration_seconds = Histogram(
    "document_ingestion_duration_seconds",
    "Time spent ingesting documents",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# Retrieval metrics
retrieval_queries_total = Counter(
    "retrieval_queries_total",
    "Total number of retrieval queries",
    ["status"],
)

retrieval_duration_seconds = Histogram(
    "retrieval_duration_seconds",
    "Time spent on retrieval queries",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
)

chunks_retrieved_total = Counter(
    "chunks_retrieved_total",
    "Total number of chunks retrieved",
)

retrieval_similarity_scores = Histogram(
    "retrieval_similarity_scores",
    "Distribution of similarity scores",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

# Generation metrics
response_generations_total = Counter(
    "response_generations_total",
    "Total number of responses generated",
    ["model", "status"],
)

response_generation_duration_seconds = Histogram(
    "response_generation_duration_seconds",
    "Time spent generating responses",
    ["model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
)

# Token usage metrics
openai_tokens_total = Counter(
    "openai_tokens_total",
    "Total OpenAI tokens used",
    ["model", "token_type"],
)

# Database metrics
database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["operation", "status"],
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Time spent on database queries",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

# Error metrics
errors_total = Counter(
    "errors_total",
    "Total errors by type",
    ["error_type", "component"],
)

# System metrics
active_threads = Gauge(
    "active_threads",
    "Number of active conversation threads",
)

active_documents = Gauge(
    "active_documents",
    "Number of documents in the system",
)

active_chunks = Gauge(
    "active_chunks",
    "Number of chunks in the system",
)
