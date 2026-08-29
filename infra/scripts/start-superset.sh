#!/bin/sh
set -eu

export SUPERSET_CONFIG_PATH="${SUPERSET_CONFIG_PATH:-/opt/superset/config/superset_config.py}"
export PYTHONPATH="/opt/superset/config:${PYTHONPATH:-}"

superset db upgrade
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
  --firstname "${SUPERSET_ADMIN_FIRSTNAME:-Zhi}" \
  --lastname "${SUPERSET_ADMIN_LASTNAME:-Ying}" \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@platform.localhost}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin1234}" || true
superset init

exec gunicorn \
  --bind "0.0.0.0:${ANALYTICS_PORT:-8088}" \
  --workers 2 \
  --worker-class gthread \
  --threads 8 \
  --timeout 180 \
  "superset.app:create_app()"
