# Azure App Service デプロイメント

## ブランチの目的

`feature/azure-app-service-deployment` ブランチは、estimation-agent-core アプリケーションを Azure App Service にデプロイするための設定と手順をまとめたものです。

## 現状

### ✅ 完了した作業

1. **Azure リソースの作成**
   - リソースグループ: `rg-jhongo0067-1948` (既存)
   - App Service プラン: `estimation-core-plan` (B1、Linux、Japan West)
   - App Service: `estimation-agent-core` (Python 3.11)
   - URL: https://estimation-agent-core.azurewebsites.net

2. **アプリケーションの設定**
   - `requirements.txt` に `gunicorn` を追加
   - `startup.sh` スクリプトを作成（依存関係のインストールとgunicorn起動）
   - スタートアップコマンド設定: `bash startup.sh`

3. **設定の適用**
   - `SCM_DO_BUILD_DURING_DEPLOYMENT=1`
   - `ENABLE_ORYX_BUILD=true`

4. **デプロイの実行と動作確認**
   - ZIPデプロイ完了（`RuntimeSuccessful`）
   - アプリ再起動完了
   - ヘルスチェック成功：`https://estimation-agent-core.azurewebsites.net/health` → `{"status":"ok"}`
   - アプリケーション正常稼働中

### 🔍 発見した問題

1. **ZIPデプロイでのOryxビルド未実行**
   - `az webapp deploy --type zip` でもOryxビルド（pip install）は可能だが、今回はビルド対象を見つけられていない状態
   - 結果としてファイルコピーのみが実行され、依存関係がインストールされていない

2. **コンテナ起動の失敗**
   - exit code: 3 で繰り返しクラッシュ
   - 原因: gunicorn および依存パッケージが未インストール

3. **Japan East リージョンのクォータ制限**
   - B1プランの作成時にクォータ不足エラー
   - 回避策: Japan West リージョンに変更

## 採用した解決策

### startup.sh による依存関係のインストール

```bash
#!/usr/bin/env bash
set -euo pipefail

cd /home/site/wwwroot

echo "Python: $(python -V || true)"
echo "Pip: $(python -m pip -V || true)"

python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements.txt

echo "Starting gunicorn..."
exec python -m gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout 600 app:app
```

**利点**:
- 確実に依存関係がインストールされる
- Azure App Service の標準的なアプローチ
- `python -m pip` / `python -m gunicorn` で環境の取り違えを防止
- `cd /home/site/wwwroot` で作業ディレクトリを明示

**欠点**:
- 起動時に毎回 pip install が実行される（初回起動が遅い）

**改善ポイント**:
- `pip` 直呼びではなく `python -m pip` で同じPython環境を確実に使用
- `set -euo pipefail` でエラー時の即座停止と未定義変数の検出
- `exec` でプロセス管理を改善（シグナル処理の最適化）

## 次のステップ

### 1. デプロイの実行

現在の `startup.sh` は既に改善版が適用されています。以下の手順でデプロイを実行してください。

### 2. デプロイ手順

```bash
# ZIPを作成（__pycache__を除外）
cd /workspaces/estimation-agent-core
rm -f deploy.zip
zip -r deploy.zip startup.sh app.py requirements.txt estimate_config.yaml logic/ templates/ \
  -x "**/__pycache__/*" "*.pyc"

# ZIPの構造を確認（startup.shがルート直下にあること）
unzip -l deploy.zip | head -20

# デプロイ
az webapp deploy \
  --resource-group rg-jhongo0067-1948 \
  --name estimation-agent-core \
  --src-path deploy.zip \
  --type zip

# 再起動
az webapp restart \
  -g rg-jhongo0067-1948 \
  -n estimation-agent-core

# 動作確認（30秒待ってから）
sleep 30
curl https://estimation-agent-core.azurewebsites.net/health
```

期待される結果: `{"status":"ok"}`

### 3. トラブルシューティング

動作しない場合のログ確認:

```bash
# リアルタイムログ
az webapp log tail \
  --name estimation-agent-core \
  --resource-group rg-jhongo0067-1948

# ログのダウンロード
az webapp log download \
  --name estimation-agent-core \
  --resource-group rg-jhongo0067-1948 \
  --log-file app-logs.zip
```

確認すべき項目:
- `pip install` が実行されているか
- `gunicorn` が見つからないエラーが出ていないか
- `app:app` のインポートが成功しているか
- ポート8000でリッスンしているか

## 代替アプローチ（将来的な改善案）

### オプション1: Docker コンテナデプロイ

より確実で高速な起動を実現:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存関係のインストール（キャッシュレイヤー）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=2", "--timeout=600", "app:app"]
```

デプロイ手順:
```bash
# イメージのビルドとプッシュ
az acr build \
  --registry <your-acr-name> \
  --image estimation-agent-core:latest \
  .

# App Serviceにデプロイ
az webapp config container set \
  --name estimation-agent-core \
  --resource-group rg-jhongo0067-1948 \
  --docker-custom-image-name <your-acr-name>.azurecr.io/estimation-agent-core:latest
```

### オプション2: GitHub Actions による CI/CD

自動デプロイパイプラインの構築:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to App Service
        run: |
          zip -r deploy.zip startup.sh app.py requirements.txt estimate_config.yaml logic/ templates/
          az webapp deploy \
            --resource-group rg-jhongo0067-1948 \
            --name estimation-agent-core \
            --src-path deploy.zip \
            --type zip
```

## 関連ドキュメント

- [Azure App Service Python ドキュメント](https://docs.microsoft.com/azure/app-service/quickstart-python)
- [Gunicorn デプロイメントガイド](https://docs.gunicorn.org/en/stable/deploy.html)
- [Azure CLI リファレンス](https://docs.microsoft.com/cli/azure/webapp)

## まとめ

現在、Azure App Service へのデプロイは設定完了済みですが、最終的な動作確認が残っています。`startup.sh` による依存関係のインストールアプローチは確実性が高く、次のデプロイで正常に起動する見込みです。

将来的には、Docker コンテナデプロイや CI/CD パイプラインの導入により、より堅牢で自動化されたデプロイフローを構築することを推奨します。
