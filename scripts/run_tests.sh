#!/usr/bin/env bash
# Testes do motor e das regras puras (não exigem Django). Com --django roda também a suíte Django
# usando SQLite (apenas para testes) — requer as dependências instaladas (scripts/setup.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
[ -d venv ] && . venv/bin/activate && PY=python
"$PY" -m unittest tests.engine.test_game tests.test_pure_rules -v
if [ "${1:-}" = "--django" ]; then
  DB_ENGINE=sqlite "$PY" manage.py test tests.django_tests -v 2
fi
