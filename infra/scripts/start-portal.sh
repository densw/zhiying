#!/bin/sh
set -eu

cd /workspace
if [ -f package-lock.json ]; then
  npm ci --include=dev
else
  npm install
fi

npm run build
exec npm run start -- --ip 0.0.0.0 --port "${PORTAL_PORT:-3000}"
