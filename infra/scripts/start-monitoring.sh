#!/bin/sh
set -eu

cd /workspace
python -m pip install --no-cache-dir --upgrade pip

if [ -f "${MONITORING_APP_DIR:-infra/monitoring}/requirements.txt" ]; then
  python -m pip install --no-cache-dir -r "${MONITORING_APP_DIR:-infra/monitoring}/requirements.txt"
else
  python -m pip install --no-cache-dir fastapi uvicorn[standard] pandas psycopg[binary]
fi

APP_DIR="${MONITORING_APP_DIR:-infra/monitoring}"
if [ ! -d "$APP_DIR" ]; then
  echo "Monitoring app directory not found: $APP_DIR" >&2
  exit 1
fi

exec python -m uvicorn "${MONITORING_APP_IMPORT:-app:app}" \
  --app-dir "$APP_DIR" \
  --host 0.0.0.0 \
  --port "${MONITORING_PORT:-8000}"
