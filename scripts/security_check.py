#!/usr/bin/env python3
import os
import re
from pathlib import Path

def check_env_file():
    """環境変数ファイルのチェック"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("⚠️ .envファイルが存在します。.gitignoreに含まれていることを確認してください。")
    
    if not env_example.exists():
        print("❌ .env.exampleファイルが見つかりません。")

def check_sensitive_data():
    """機密データのチェック"""
    patterns = [
        r'(?i)api[_-]key',
        r'(?i)secret',
        r'(?i)password',
        r'(?i)token',
    ]
    
    for path in Path('.').rglob('*'):
        if path.is_file() and path.suffix in ['.py', '.md', '.txt']:
            content = path.read_text()
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    print(f"⚠️ 潜在的な機密情報: {path} - {match.group()}")

if __name__ == "__main__":
    print("🔒 セキュリティチェックを実行中...")
    check_env_file()
    check_sensitive_data() 