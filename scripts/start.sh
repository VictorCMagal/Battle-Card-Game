#!/usr/bin/env bash
# Inicia o servidor ASGI (HTTP + WebSocket). Uso: scripts/start.sh [dev]
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
. venv/bin/activate
if [ "${1:-}" = "dev" ]; then
  exec python manage.py runserver 0.0.0.0:8000
fi
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
