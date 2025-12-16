#!/bin/bash
set -e

# 依存関係のインストール
pip install -r requirements.txt

# gunicornでアプリケーションを起動
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
