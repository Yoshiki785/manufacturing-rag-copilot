# AI Usage Declaration

## Overview

This project uses AI/LLM technologies as core functionality to provide intelligent document retrieval and question answering.

## AI Components

### OpenAI API
- **Embeddings**: text-embedding-3-small for vector representations
- **Chat Completion**: GPT-4o for response generation
- **Purpose**: Core RAG pipeline functionality

## Data Handling

- User queries are sent to OpenAI for embedding generation
- Retrieved context and queries are sent to OpenAI for response generation
- No training data is shared with OpenAI (API usage only)
- All data transmission uses encrypted connections

## Limitations

- Responses are limited to information in the document corpus
- AI may occasionally misinterpret technical terminology
- Citation accuracy depends on retrieval quality
- Not suitable for real-time safety-critical decisions

## Human Oversight

- All AI responses include source citations for verification
- Audit logging tracks all AI-generated content
- Users should verify critical information with authoritative sources

## Updates

This document will be updated as AI capabilities and usage patterns evolve.
