#!/bin/sh
set -eu

APP_DIR="${REPORTS_APP_DIR:-infra/reports}"
cd "/workspace/$APP_DIR"

if [ -f package-lock.json ]; then
  npm ci
elif [ -f package.json ]; then
  npm install
fi

if [ -f package.json ]; then
  if node -e "const fs=require('fs'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); process.exit(pkg.scripts && pkg.scripts.build ? 0 : 1)"; then
    npm run build
  fi

  if node -e "const fs=require('fs'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); process.exit(pkg.scripts && pkg.scripts.start ? 0 : 1)"; then
    exec npm run start -- --host 0.0.0.0 --port "${REPORTS_PORT:-3000}"
  fi
fi

if [ -f server.mjs ]; then
  exec node server.mjs
fi

echo "Reports app is missing a runnable entrypoint in $APP_DIR" >&2
exit 1
