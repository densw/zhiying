#!/bin/sh
set -eu

MODE="${1:-webserver}"

cd /workspace
python -m pip install --no-cache-dir --upgrade pip
python -m pip install --no-cache-dir dagster dagster-webserver pandas psycopg[binary]

mkdir -p "${DAGSTER_HOME:-/opt/dagster/dagster_home}"
cp /opt/dagster/app/dagster.yaml "${DAGSTER_HOME:-/opt/dagster/dagster_home}/dagster.yaml"
cp /opt/dagster/app/workspace.yaml "${DAGSTER_HOME:-/opt/dagster/dagster_home}/workspace.yaml"

if [ "$MODE" = "daemon" ]; then
  exec dagster-daemon run -w "${DAGSTER_HOME:-/opt/dagster/dagster_home}/workspace.yaml"
fi

exec dagster-webserver \
  --host 0.0.0.0 \
  --port "${DAGSTER_PORT:-3000}" \
  -w "${DAGSTER_HOME:-/opt/dagster/dagster_home}/workspace.yaml"
