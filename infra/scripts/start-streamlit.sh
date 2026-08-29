#!/bin/sh
set -eu

cd /workspace
python -m pip install --no-cache-dir --upgrade pip

if [ -f "${DECISION_APP_DIR:-infra/decision}/requirements.txt" ]; then
  python -m pip install --no-cache-dir -r "${DECISION_APP_DIR:-infra/decision}/requirements.txt"
else
  python -m pip install --no-cache-dir streamlit pandas sqlalchemy psycopg[binary]
fi

APP_PATH="${DECISION_APP_DIR:-infra/decision}/${DECISION_APP_FILE:-app.py}"
if [ ! -f "$APP_PATH" ]; then
  echo "Decision app not found: $APP_PATH" >&2
  exit 1
fi

exec streamlit run "$APP_PATH" \
  --server.address=0.0.0.0 \
  --server.port="${DECISION_PORT:-8501}" \
  --server.headless=true \
  --browser.gatherUsageStats=false
