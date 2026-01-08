# Manufacturing RAG Copilot - ユーザーガイド

## 📖 目次
1. このシステムは何か
2. 主な機能
3. セットアップ方法
4. 基本的な使い方
5. API使用例
6. よくある質問
7. トラブルシューティング

---

## 1. このシステムは何か

### 概要
Manufacturing RAG Copilot (製造業RAGコパイロット) は、製造業の技術文書・手順書・仕様書などを管理し、質問に対してAIが文書を検索して回答するシステムです。

### 解決する問題
- 製造現場での「この手順書どこだっけ?」
- 技術文書が分散していて探すのに時間がかかる
- ベテラン社員の知識が属人化している
- 新入社員のオンボーディングに時間がかかる

### できること
1. **文書取り込み**: PDF、Word、テキストなどの技術文書をシステムに登録
2. **自然言語検索**: 「トルク仕様は?」のような質問で関連情報を検索
3. **AI回答生成**: 検索結果をもとにGPT-4oが分かりやすく回答
4. **出典表示**: 回答の根拠となる文書を明示 (トレーサビリティ)
5. **会話履歴**: 過去の質問・回答を保存

---

## 2. 主な機能

### 2.1 文書管理機能
- **取り込み対応**: テキスト、PDF、Word、Excel
- **メタデータ管理**: 文書タイプ、作成日、更新日
- **自動チャンク化**: 長文を適切な単位に分割
- **バッチ取り込み**: 複数文書を一括登録

### 2.2 検索・回答機能
- **セマンティック検索**: 意味で検索 (キーワードマッチではない)
- **コンテキスト回答**: 関連する複数の文書を参照して回答
- **出典引用**: [Source 1], [Source 2] の形式で出典表示
- **会話継続**: 前の質問を考慮した回答

### 2.3 セキュリティ機能
- **APIキー認証**: X-API-Keyヘッダーで認証
- **レート制限**: 1分間に10リクエストまで
- **監査ログ**: 全ての操作を記録

### 2.4 監視機能
- **Prometheusメトリクス**: /metricsエンドポイントで取得
- **処理時間計測**: クエリごとの応答時間
- **トークン使用量**: OpenAI API使用量の追跡

---

## 3. セットアップ方法

### 3.1 必要な環境
- Python 3.11以上
- PostgreSQL 16 (pgvector拡張必須)
- OpenAI APIキー

### 3.2 インストール手順

#### Step 1: リポジトリクローン
```bash
git clone https://github.com/Yoshiki785/manufacturing-rag-copilot.git
cd manufacturing-rag-copilot
```

#### Step 2: 環境変数設定
```bash
cp .env.example .env
nano .env  # またはお好みのエディタ
```

必須の設定:
```bash
# OpenAI API
OPENAI_API_KEY=sk-your-actual-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/manufacturing_rag

# Security
API_KEYS=your-secure-key-1,your-secure-key-2

# Retrieval
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7
```

#### Step 3: データベース起動
```bash
docker-compose up -d
```

確認:
```bash
docker ps  # postgresコンテナが起動しているか確認
```

#### Step 4: 依存関係インストール
```bash
pip install -e ".[dev]"
```

#### Step 5: データベース初期化
```bash
# スキーマは自動作成される (docker-compose.ymlで設定済み)
# 確認:
docker exec -it manufacturing-rag-db psql -U postgres -d manufacturing_rag -c "\dt"
```

#### Step 6: サーバー起動
```bash
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

確認:
```bash
curl http://localhost:8000/health
# {"status":"healthy","environment":"development"}
```

---

## 4. 基本的な使い方

### 4.1 ヘルスチェック

**目的**: システムが正常に動作しているか確認

**リクエスト:**
```bash
curl http://localhost:8000/health
```

**レスポンス:**
```json
{
  "status": "healthy",
  "environment": "development"
}
```

---

### 4.2 文書の取り込み

**目的**: 技術文書をシステムに登録

**リクエスト:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "X-API-Key: your-secure-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "製品XYZ-100のトルク仕様は45 Nmです。締め付け時は必ずトルクレンチを使用してください。",
    "metadata": {
      "title": "製品XYZ-100 組立手順書",
      "document_type": "assembly_manual",
      "version": "1.2",
      "author": "製造部"
    }
  }'
```

**レスポンス:**
```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**説明:**
- `content`: 文書の本文 (必須)
- `metadata`: 文書のメタ情報 (オプション)
  - `title`: 文書タイトル
  - `document_type`: 文書種別 (manual, spec, procedureなど)
  - `version`: バージョン
  - `author`: 作成者

---

### 4.3 質問・検索

**目的**: 質問に対して文書を検索してAIが回答

**リクエスト:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-secure-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "製品XYZ-100のトルク仕様を教えてください",
    "top_k": 5
  }'
```

**レスポンス:**
```json
{
  "answer": "製品XYZ-100のトルク仕様は45 Nmです [Source 1]。締め付け時は必ずトルクレンチを使用する必要があります [Source 1]。",
  "citations": [
    {
      "source": 1,
      "chunk_id": "chunk-uuid-1",
      "document_id": "doc-uuid-1",
      "content": "製品XYZ-100のトルク仕様は45 Nmです。締め付け時は...",
      "metadata": {
        "title": "製品XYZ-100 組立手順書"
      }
    }
  ],
  "thread_id": "thread-uuid-1"
}
```

**説明:**
- `query`: 質問文 (必須)
- `top_k`: 検索する文書の最大数 (デフォルト: 5)
- `thread_id`: 会話を継続する場合に指定 (オプション)

**回答の見方:**
- `answer`: AIの回答文
- `[Source N]`: 出典番号 (citationsの配列インデックスに対応)
- `citations`: 回答の根拠となった文書チャンク

---

### 4.4 会話の継続

**目的**: 前の質問の文脈を考慮した質問

**1回目の質問:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-secure-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "製品XYZ-100について教えて"
  }'

# レスポンスでthread_idを取得
# "thread_id": "abc-123"
```

**2回目の質問 (継続):**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-secure-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "そのトルク仕様は?",
    "thread_id": "abc-123"
  }'
```

**説明:**
- 同じ`thread_id`を使うことで会話の文脈が保持される
- 「その」「それ」などの代名詞が使える

---

### 4.5 会話履歴の確認

**スレッド一覧取得:**
```bash
curl http://localhost:8000/api/v1/threads \
  -H "X-API-Key: your-secure-key-1"
```

**特定のスレッド取得:**
```bash
curl http://localhost:8000/api/v1/threads/abc-123 \
  -H "X-API-Key: your-secure-key-1"
```

---

### 4.6 メトリクスの確認

**目的**: システムの使用状況を監視

**リクエスト:**
```bash
curl http://localhost:8000/metrics
```

**レスポンス (Prometheus形式):**
```
# HELP rag_query_duration_seconds RAGクエリの処理時間
# TYPE rag_query_duration_seconds histogram
rag_query_duration_seconds_bucket{le="0.5"} 10
rag_query_duration_seconds_bucket{le="1.0"} 25
...

# HELP rag_generation_tokens_total 生成で使用したトークン数
# TYPE rag_generation_tokens_total counter
rag_generation_tokens_total 15432
```

---

## 5. API使用例 (実践シナリオ)

### シナリオ1: 技術文書を一括登録

**状況**: 100個の組立手順書PDFをシステムに登録したい

**手順:**

1. PDFをテキスト抽出 (外部ツール使用)
```bash
# pdftotext や pdfminer などを使用
pdftotext manual001.pdf manual001.txt
```

2. Pythonスクリプトで一括登録
```python
import requests
import os

API_URL = "http://localhost:8000/api/v1/ingest"
API_KEY = "your-secure-key-1"

for filename in os.listdir("manuals/"):
    if filename.endswith(".txt"):
        with open(f"manuals/{filename}", "r", encoding="utf-8") as f:
            content = f.read()

        response = requests.post(
            API_URL,
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "content": content,
                "metadata": {
                    "title": filename,
                    "document_type": "manual",
                    "source_path": f"manuals/{filename}"
                }
            }
        )
        print(f"✓ {filename}: {response.json()['document_id']}")
```

---

### シナリオ2: Webアプリから検索機能を提供

**状況**: 社内Webアプリに検索機能を追加したい

**フロントエンド (JavaScript):**
```javascript
async function searchManual(query) {
  const response = await fetch("http://localhost:8000/api/v1/query", {
    method: "POST",
    headers: {
      "X-API-Key": "your-secure-key-1",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query: query })
  });

  const data = await response.json();

  // 回答を表示
  document.getElementById("answer").innerText = data.answer;

  // 出典を表示
  const citationsDiv = document.getElementById("citations");
  data.citations.forEach(citation => {
    const div = document.createElement("div");
    div.innerHTML = `
      <strong>[Source ${citation.source}]</strong>
      ${citation.metadata.title}<br>
      ${citation.content.substring(0, 100)}...
    `;
    citationsDiv.appendChild(div);
  });
}
```

---

### シナリオ3: Slackボットと連携

**状況**: Slackから質問できるボットを作りたい

**Pythonスクリプト (Slack Bolt使用):**
```python
from slack_bolt import App
import requests

app = App(token="xoxb-your-slack-bot-token")

@app.message("質問:")
def handle_question(message, say):
    query = message["text"].replace("質問:", "").strip()

    # RAGシステムに問い合わせ
    response = requests.post(
        "http://localhost:8000/api/v1/query",
        headers={"X-API-Key": "your-secure-key-1"},
        json={"query": query}
    )

    data = response.json()

    # Slackに回答を投稿
    say(f"💡 {data['answer']}\n\n📚 出典: {len(data['citations'])}件の文書を参照")

app.start(port=3000)
```

---

## 6. よくある質問 (FAQ)

### Q1: 検索結果が的外れです
**A:** 以下を確認してください:
- 類似度閾値が高すぎる可能性 → .envの`SIMILARITY_THRESHOLD`を0.3に下げる
- 取り込んだ文書に関連情報がない → 追加の文書を取り込む
- チャンクサイズが不適切 → `CHUNK_SIZE`を調整 (デフォルト512)

### Q2: OpenAI APIの費用が心配です
**A:** 以下で費用を確認・管理:
- `/metrics`エンドポイントで使用トークン数を確認
- OpenAIダッシュボードで使用量を監視
- `.env`の`TOP_K_RETRIEVAL`を減らして検索文書数を削減

### Q3: 日本語の文書が正しく処理されません
**A:**
- OpenAIのtext-embedding-3-smallは日本語対応済み
- チャンク境界で日本語が途切れる場合 → `CHUNK_OVERLAP`を増やす

### Q4: レート制限に引っかかります
**A:**
- `.env`の`rate_limit_per_minute`を増やす (デフォルト10)
- 本番環境ではRedisバックエンドを使用して分散レート制限

### Q5: データベースのバックアップは?
**A:**
```bash
# バックアップ
docker exec manufacturing-rag-db pg_dump -U postgres manufacturing_rag > backup.sql

# リストア
cat backup.sql | docker exec -i manufacturing-rag-db psql -U postgres manufacturing_rag
```

---

## 7. トラブルシューティング

### 問題: サーバーが起動しない

**症状:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解決策:**
```bash
# PostgreSQLコンテナの状態確認
docker ps

# 起動していない場合
docker-compose up -d

# ログ確認
docker logs manufacturing-rag-db
```

---

### 問題: OpenAI APIエラー

**症状:**
```
openai.error.AuthenticationError: Incorrect API key provided
```

**解決策:**
1. `.env`ファイルの`OPENAI_API_KEY`を確認
2. 有効なAPIキーか確認: https://platform.openai.com/api-keys
3. サーバーを再起動 (環境変数の再読み込み)

---

### 問題: 検索結果が0件

**症状:**
クエリに対して常に「情報が見つかりません」

**解決策:**
```bash
# 文書が取り込まれているか確認
docker exec -i manufacturing-rag-db psql -U postgres manufacturing_rag -c "SELECT COUNT(*) FROM documents;"

# embeddings が作成されているか確認
docker exec -i manufacturing-rag-db psql -U postgres manufacturing_rag -c "SELECT COUNT(*) FROM embeddings;"

# 0件の場合、文書を取り込む
```

---

### 問題: メモリ不足

**症状:**
```
MemoryError: Unable to allocate array
```

**解決策:**
- `TOP_K_RETRIEVAL`を減らす (デフォルト5 → 3)
- `CHUNK_SIZE`を小さくする (512 → 256)
- PostgreSQLのshared_buffersを増やす

---

## 8. 次のステップ

### 開発を続ける
- [ ] 認証をJWT/OAuth2に変更
- [ ] マルチテナント対応
- [ ] ファイルアップロードAPI追加
- [ ] 管理画面の開発

### 本番環境へデプロイ
- [ ] Docker イメージのビルド
- [ ] AWS/GCP/Azureへのデプロイ
- [ ] CI/CDパイプラインの構築
- [ ] SSL証明書の設定

### 機能拡張
- [ ] 画像認識 (図面の検索)
- [ ] 音声入力対応
- [ ] 多言語対応
- [ ] リランキング機能

---

以上でユーザーガイドは完了です。
