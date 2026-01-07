# Manufacturing RAG Copilot API Guide

製造業向けRAGシステムのAPI使用ガイド

## 🚀 Quick Start

### 1. 環境セットアップ

```bash
# .envファイルを作成
cp .env.example .env

# OpenAI APIキーを設定
# .envファイルを編集して OPENAI_API_KEY を設定

# 依存関係をインストール
make install
```

### 2. データベース起動

```bash
# テストDB起動（ポート5433）
docker-compose up -d postgres-test

# または本番DB起動（ポート5432）
docker-compose up -d postgres
```

### 3. サーバー起動

```bash
# 開発サーバー起動
make dev

# または直接起動
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. APIドキュメント確認

ブラウザで以下にアクセス:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Check

サーバーの健全性を確認

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### 1. Document Ingestion

製造ドキュメントをシステムに取り込む

**Endpoint:** `POST /api/v1/ingest`

**Request Body:**
```json
{
  "content": "製造プロセスの標準作業手順書...",
  "metadata": {
    "title": "CNC フライス盤 SOP",
    "document_type": "SOP",
    "equipment": "XYZ-3000",
    "version": "2.1"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Manufacturing Process SOP\n\nTorque Specifications:\n- Tool holder: 45 Nm\n- Workpiece clamping: 30-35 Nm",
    "metadata": {
      "title": "Torque Specifications",
      "type": "technical_doc"
    }
  }'
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. RAG Query

製造知識に基づいて質問に回答

**Endpoint:** `POST /api/v1/query`

**Request Body:**
```json
{
  "query": "トルク仕様は何Nmですか？",
  "thread_id": "optional-thread-uuid",
  "top_k": 5
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the recommended torque specification?",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "answer": "The recommended torque specifications are:\n- Tool holder tightening torque: 45 Nm [Source 1]\n- Workpiece clamping: 30-35 Nm [Source 1]",
  "citations": [
    {
      "source": 1,
      "chunk_id": "chunk-uuid",
      "content": "Torque Specifications:\n- Tool holder: 45 Nm..."
    }
  ],
  "thread_id": "new-thread-uuid"
}
```

### 3. List Threads

会話スレッド一覧を取得

**Endpoint:** `GET /api/v1/threads`

**cURL Example:**
```bash
curl http://localhost:8000/api/v1/threads
```

**Response:**
```json
[
  {
    "id": "thread-uuid",
    "title": "Torque specifications",
    "user_id": null,
    "meta": {},
    "created_at": "2026-01-06T10:00:00Z",
    "updated_at": "2026-01-06T10:05:00Z"
  }
]
```

### 4. Get Thread Details

特定のスレッドの詳細とメッセージ履歴を取得

**Endpoint:** `GET /api/v1/threads/{thread_id}`

**cURL Example:**
```bash
curl http://localhost:8000/api/v1/threads/{thread_id}
```

**Response:**
```json
{
  "id": "thread-uuid",
  "title": "Torque specifications",
  "user_id": null,
  "meta": {},
  "created_at": "2026-01-06T10:00:00Z",
  "updated_at": "2026-01-06T10:05:00Z",
  "messages": [
    {
      "id": "message-uuid-1",
      "role": "user",
      "content": "What is the torque specification?",
      "citations": [],
      "token_count": null,
      "created_at": "2026-01-06T10:00:00Z"
    },
    {
      "id": "message-uuid-2",
      "role": "assistant",
      "content": "The torque is 45 Nm [Source 1]",
      "citations": [{"source": 1, "chunk_id": "...", "content": "..."}],
      "token_count": 150,
      "created_at": "2026-01-06T10:00:05Z"
    }
  ]
}
```

## 🧪 Testing

### Unit & Integration Tests

```bash
# 全テスト実行（PostgreSQL必須）
make test

# 特定のテストのみ
pytest tests/test_api.py -v

# カバレッジ付き
pytest tests/ --cov=src/app --cov-report=html
```

### Manual API Testing

```bash
# 1. サーバー起動
make dev

# 2. ヘルスチェック
curl http://localhost:8000/health

# 3. テストデータ挿入
python test_api_manual.py

# 4. スレッド確認
curl http://localhost:8000/api/v1/threads
```

## 🔧 Configuration

### Environment Variables

`.env`ファイルで設定:

```bash
# OpenAI API（必須）
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/manufacturing_rag

# RAG Parameters
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.3

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development

# Security
API_KEY_ENABLED=true
API_KEYS=["your-api-key-1","your-api-key-2"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_QUERY=30/minute
RATE_LIMIT_INGEST=10/minute
RATE_LIMIT_THREADS=60/minute
```

### Database Configuration

**開発環境（テストDB）:**
- URL: `postgresql+asyncpg://postgres:postgres@localhost:5433/manufacturing_rag_test`
- ポート: 5433
- データ: tmpfs（揮発性）

**本番環境:**
- URL: `postgresql+asyncpg://postgres:postgres@localhost:5432/manufacturing_rag`
- ポート: 5432
- データ: 永続化（Dockerボリューム）

## 📊 Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | 正常にレスポンス |
| 404 | Not Found | リソースが見つからない |
| 500 | Internal Server Error | サーバーエラー |

## 🔐 Authentication

APIキー認証とレート制限はデフォルトで有効です。
無効化する場合は `.env` の `API_KEY_ENABLED` / `RATE_LIMIT_ENABLED` を調整してください。

本番環境では以下を推奨:
- API Key authentication
- JWT tokens
- Rate limiting

## 📝 Best Practices

### 1. Document Ingestion

- **適切なメタデータ**: document_type, equipment, version等を含める
- **適切な粒度**: 1つの手順書、1つのSOP単位で取り込む
- **更新管理**: バージョン管理をメタデータで行う

### 2. Query Optimization

- **top_k調整**: デフォルト5、必要に応じて増減
- **スレッド利用**: 会話の文脈を保持するためthread_idを使用
- **明確な質問**: 具体的な質問ほど精度の高い回答が得られる

### 3. Performance

- **バッチ処理**: 大量のドキュメントは並列で取り込む
- **インデックス**: pgvectorのIVFFlat索引が自動作成される
- **キャッシュ**: 同じ質問の繰り返しはスレッド履歴を参照

## 🐛 Troubleshooting

### OpenAI API Errors

```
Error: AuthenticationError
```
→ .envファイルのOPENAI_API_KEYを確認

### Database Connection Errors

```
Error: Connection refused
```
→ PostgreSQLが起動しているか確認: `docker-compose ps`

### Port Already in Use

```
Error: Address already in use
```
→ ポート変更または既存プロセス終了: `lsof -i :8000`

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## 🤝 Contributing

テストを追加してプルリクエストを送信してください:

```bash
# テスト実行
make test

# Linting
make lint

# Format
make format
```
