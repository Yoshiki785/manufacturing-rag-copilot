# Architecture

## Overview

Manufacturing RAG Copilot is a Retrieval-Augmented Generation system designed for manufacturing domain knowledge management.

## System Components

### 1. API Layer (FastAPI)
- RESTful endpoints for queries, ingestion, and thread management
- Async request handling for high throughput
- Pydantic models for request/response validation

### 2. RAG Pipeline
- **Chunking**: Sentence-aware splitting with manufacturing-specific optimizations
- **Embedding**: OpenAI text-embedding-3-small (1536 dimensions)
- **Retrieval**: pgvector cosine similarity search
- **Generation**: GPT-4o with citation-enforcing system prompt

### 3. Data Layer (PostgreSQL + pgvector)
- Document and chunk storage
- Vector embeddings with IVFFlat indexing
- Conversation thread management
- Audit logging for compliance

## Data Flow

```
Document Ingestion:
Document → Chunking → Embedding → Storage (PostgreSQL + pgvector)

Query Processing:
Query → Embedding → Retrieval → Context Assembly → LLM Generation → Response
```

## Trade-offs

### Chunking Strategy
- **Choice**: Fixed-size with overlap + sentence boundaries
- **Trade-off**: Simpler than semantic chunking but may split related content
- **Mitigation**: Manufacturing-specific rules for procedures and specs

### Embedding Model
- **Choice**: text-embedding-3-small
- **Trade-off**: Lower dimension (1536) vs larger models, but faster and cheaper
- **Mitigation**: Sufficient for manufacturing domain; can upgrade later

### Vector Index
- **Choice**: IVFFlat with 100 lists
- **Trade-off**: Approximate search vs exact; requires training data
- **Mitigation**: Good balance of speed and accuracy for expected corpus size

### Context Window
- **Choice**: Top-5 chunks by default
- **Trade-off**: More context = more accurate but higher latency and cost
- **Mitigation**: Configurable via environment; reranking for quality

## Security Considerations

- API keys stored in environment variables only
- Database credentials never in code
- Audit logging for all operations
- Input validation on all endpoints

## Scalability Path

1. **Current**: Single instance, local PostgreSQL
2. **Near-term**: Container orchestration, managed database
3. **Future**: Horizontal scaling, caching layer, async job queue
