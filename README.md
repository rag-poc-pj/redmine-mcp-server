# Redmine MCP Server

AWS Lambda + API Gateway で動作する Redmine 向け MCP (Model Context Protocol) サーバーです。
GenU などの AI エージェントから Redmine のチケット・プロジェクトを操作できます。

## 機能 (Tools)

| ツール名 | 説明 |
|----------|------|
| `get_issues` | チケット一覧の取得・検索 |
| `get_issue` | チケット詳細・コメント・添付ファイルの取得 |
| `create_issue` | 新規チケットの作成 |
| `update_issue` | 既存チケットの更新 |
| `add_comment` | チケットへのコメント追加 |
| `get_projects` | プロジェクト一覧の取得 |

## 必要環境

- Node.js 20+
- AWS CLI (デプロイ時)
- Serverless Framework v3 (デプロイ時)

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/YOUR_USERNAME/redmine-mcp-server.git
cd redmine-mcp-server
npm install
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集:

```env
REDMINE_URL=https://your-redmine.example.com
REDMINE_API_KEY=your_api_key_here
```

> **Redmine APIキーの取得方法**
> Redmine にログイン → 右上のユーザー名 → 「個人設定」→「APIアクセスキー」を表示

### 3. ローカル起動・動作確認

```bash
npm run dev
```

```
MCP Endpoint : http://localhost:3000/mcp
Health Check : http://localhost:3000/health
```

## AWS Lambda へのデプロイ

### 1. AWS Systems Manager Parameter Store に環境変数を登録

```bash
aws ssm put-parameter \
  --name "/redmine-mcp/dev/REDMINE_URL" \
  --value "https://your-redmine.example.com" \
  --type "String"

aws ssm put-parameter \
  --name "/redmine-mcp/dev/REDMINE_API_KEY" \
  --value "your_api_key_here" \
  --type "SecureString"
```

### 2. デプロイ

```bash
npm run deploy         # dev ステージ
npm run deploy:prod    # prod ステージ
```

デプロイ完了後、API Gateway の URL が表示されます：

```
endpoints:
  POST - https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/mcp
  GET  - https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/health
```

## GenU への接続設定

GenU の MCP 設定ファイルに以下を追加してください：

```json
{
  "mcpServers": {
    "redmine": {
      "url": "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/mcp",
      "transport": "streamable-http"
    }
  }
}
```

## プロジェクト構成

```
redmine-mcp-server/
├── src/
│   ├── index.ts          # ローカル開発用エントリーポイント
│   ├── lambda.ts         # Lambda エントリーポイント
│   ├── app.ts            # Express アプリ (HTTP Transport)
│   ├── server.ts         # MCP ツール定義
│   └── redmine-client.ts # Redmine REST API クライアント
├── .env.example          # 環境変数サンプル
├── .gitignore
├── package.json
├── tsconfig.json
├── serverless.yml        # Serverless Framework 設定
└── README.md
```

## ライセンス

MIT
