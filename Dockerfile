FROM python:3.11-slim

WORKDIR /app

# システム依存関係とクリーンアップを一度に実行
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Pipを最新にアップグレード
RUN pip install --no-cache-dir --upgrade pip

# Python依存関係（キャッシュ効率のため分離）
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# アプリケーションコード
COPY . .

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ポート設定
EXPOSE 8080

# 実行
CMD ["python", "enhanced_main_v2.py"]
