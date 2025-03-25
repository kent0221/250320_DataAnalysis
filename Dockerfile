# Pythonアプリケーション用のDockerfile

FROM python:3.11

WORKDIR /app

# 依存関係を明示的にインストール
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.23.5
RUN pip install --no-cache-dir mysql-connector-python==8.0.32
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# デフォルトコマンドはなし（compose.yamlで設定）
