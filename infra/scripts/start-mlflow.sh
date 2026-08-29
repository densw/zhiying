#!/bin/sh
set -eu

python -m pip install --no-cache-dir --upgrade pip
python -m pip install --no-cache-dir mlflow psycopg[binary]

mkdir -p "${MLFLOW_ARTIFACT_ROOT:-/mlflow/artifacts}"

exec mlflow server \
  --host 0.0.0.0 \
  --port "${MLFLOW_PORT:-5000}" \
  --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
  --serve-artifacts \
  --artifacts-destination "${MLFLOW_ARTIFACT_ROOT:-/mlflow/artifacts}"
