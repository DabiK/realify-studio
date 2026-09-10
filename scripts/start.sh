#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f dist/index.html ]; then
  echo "Construire l’interface avec npm ci puis npm run build."
  exit 1
fi
if [ -x .venv/bin/python3 ]; then
  exec .venv/bin/python3 server.py "$@"
else
  exec python3 server.py "$@"
fi
