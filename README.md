# Manufacturing RAG Copilot

An AI-powered Retrieval-Augmented Generation (RAG) system designed for manufacturing domain knowledge assistance.

## Why

Manufacturing teams need quick, accurate access to technical documentation, procedures, and institutional knowledge. This RAG copilot provides:

- **Contextual answers** with citations from your document base
- **Audit trail** for compliance and traceability
- **Domain-optimized** chunking and retrieval for technical content

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│   OpenAI    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                   ┌──────▼──────┐
                   │  PostgreSQL │
                   │  + pgvector │
                   └─────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed design.

## Quickstart

```bash
# Clone and setup
git clone https://github.com/Yoshiki785/manufacturing-rag-copilot.git
cd manufacturing-rag-copilot

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn src.app.main:app --reload
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/ingest` | POST | Ingest documents |
| `/api/v1/query` | POST | Query the RAG system |
| `/api/v1/threads` | GET/POST | Manage conversation threads |

## Data Model

- **documents**: Source documents with metadata
- **chunks**: Text chunks with source references
- **embeddings**: Vector embeddings (pgvector)
- **threads**: Conversation threads
- **messages**: Thread messages with citations
- **audit_logs**: System audit trail

## Evaluation

- Retrieval metrics: MRR, Recall@k
- Generation metrics: Faithfulness, relevance scoring
- End-to-end: User feedback integration

## Security

See [SECURITY.md](SECURITY.md) for security policy and vulnerability reporting.

## AI Usage

See [AI_USAGE.md](AI_USAGE.md) for details on AI/LLM usage in this project.

## License

MIT License - see [LICENSE](LICENSE)
