# Pythonアプリケーション用のDockerfile

FROM python:3.11

WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update && \
  apt-get install -y less

COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーションコードのコピー
COPY app/ ./app/

# 実行権限の付与
RUN chmod +x /app/app/main.py

CMD ["python", "-m", "app.main", "--interactive"]
