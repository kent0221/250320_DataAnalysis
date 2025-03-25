#!/bin/bash

echo "🔍 未追跡ファイルの確認..."
git clean -fdx --dry-run

echo "🔒 環境変数ファイルの確認..."
if [ -f .env ]; then
    echo "警告: .envファイルが存在します"
fi

echo "🧪 テストの実行..."
python -m pytest tests/ --cov=app --cov-report=term-missing

echo "📊 レート制限テストの確認..."
python -m pytest tests/test_api_client.py -k "test_rate_limit"

echo "🔍 機密情報スキャンの実行..."
if [ -f scripts/security_check.py ]; then
    python scripts/security_check.py
fi

echo "📊 コードカバレッジレポートの生成中..."
python -m pytest --cov=app --cov-report=html tests/

echo "🔒 セキュリティチェックの実行中..."
safety check -r requirements.txt

echo "✨ リンターの実行中..."
flake8 app/ tests/ 