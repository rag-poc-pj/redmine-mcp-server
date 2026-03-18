#!/bin/bash
# EC2上での起動スクリプト

# 環境変数設定
export REDMINE_URL="https://ld-redmine.kddi.com"
export REDMINE_API_KEY="your_api_key_here"
export AWS_REGION="ap-northeast-1"

# 依存関係インストール
pip3 install -r requirements.txt

# サーバー起動（バックグラウンド）
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

echo "サーバーを起動しました（port 8000）"
echo "ログ: tail -f app.log"
echo "停止: kill \$(lsof -t -i:8000)"
