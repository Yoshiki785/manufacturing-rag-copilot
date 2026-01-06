# Manufacturing RAG Copilot（日本語版）

[![CI](https://github.com/Yoshiki785/manufacturing-rag-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/Yoshiki785/manufacturing-rag-copilot/actions/workflows/ci.yml)
[![Code Quality](https://github.com/Yoshiki785/manufacturing-rag-copilot/actions/workflows/code-quality.yml/badge.svg)](https://github.com/Yoshiki785/manufacturing-rag-copilot/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/Yoshiki785/manufacturing-rag-copilot/branch/main/graph/badge.svg)](https://codecov.io/gh/Yoshiki785/manufacturing-rag-copilot)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

製造業向けのドメイン知識支援を目的とした、RAG（Retrieval-Augmented Generation）ベースのコパイロット。

## なぜ（Why）

製造現場では手順書、仕様書、保守ログなどの技術ドキュメントに素早く正確にアクセスする必要があります。本プロジェクトは次を目指します：

- ドキュメントに根拠のある回答（出典付き）
- コンプライアンスを意識した監査ログ
- 製造向けに最適化したチャンク化と検索

## アーキテクチャ（Architecture）

クライアント → FastAPI（API層） → RAGパイプライン（埋め込み・検索・生成）  
データは PostgreSQL + pgvector に保存されます。詳細は docs/architecture.ja.md を参照してください。

## クイックスタート（Quickstart）

```bash
git clone https://github.com/Yoshiki785/manufacturing-rag-copilot.git
cd manufacturing-rag-copilot

cp .env.example .env
# .env に API キー等を設定

docker-compose up -d

pip install -e "[dev]"

uvicorn src.app.main:app --reload
```

## API

- GET `/health` — ヘルスチェック
- POST `/api/v1/ingest` — ドキュメントの取り込み
- POST `/api/v1/query` — RAG による質問
- GET/POST `/api/v1/threads` — 会話スレッド管理

## データモデル（Data model）

- documents: ソースドキュメント
- chunks: ドキュメントを分割したチャンク
- embeddings: pgvector に保存するベクトル
- threads: 会話スレッド
- messages: スレッド内のメッセージ（出典情報含む）
- audit_logs: 操作履歴（監査ログ）

## 評価（Evaluation）

- 検索：MRR、Recall@k
- 生成：忠実性（faithfulness）、関連性スコア
- エンドツーエンド：ユーザーフィードバックの取り込み

## セキュリティ（Security）

機密情報は環境変数やシークレット管理で保管。詳細は SECURITY.ja.md を参照してください。

## AI 利用について（AI usage）

OpenAI API を利用した埋め込みと応答生成を行います。詳細は AI_USAGE.ja.md を参照してください。

## ライセンス（License）

MIT ライセンス（LICENSE を参照）
