#!/usr/bin/env bash
set -euo pipefail

cd /home/site/wwwroot

echo "Python: $(python -V || true)"
echo "Pip: $(python -m pip -V || true)"

python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements.txt

echo "Starting gunicorn..."
exec python -m gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout 600 app:app
