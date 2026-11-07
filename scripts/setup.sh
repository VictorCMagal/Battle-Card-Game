#!/usr/bin/env bash
# Instala dependências, cria o .env (1ª vez), gera/aplica migrations e carrega dados essenciais.
# Uso: scripts/setup.sh [--dev-data]     (--dev-data cria as 3 contas de teste)
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || { echo "Python 3.11+ é necessário."; exit 1; }
[ -d venv ] || "$PY" -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
  sed -i.bak "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET}|" .env && rm -f .env.bak
  echo ">> .env criado. Edite DB_USER/DB_PASSWORD/DB_NAME e rode scripts/setup.sh novamente."
  echo ">> Antes, crie o banco: mysql -u root -p < sql/00_create_database.sql (ajuste a senha no arquivo)."
  exit 0
fi
python manage.py check
python manage.py makemigrations      # gera as migrations na 1ª execução (versione-as depois)
python manage.py migrate
python manage.py bootstrap
if [ "${1:-}" = "--dev-data" ]; then python manage.py seed_dev; fi
python manage.py collectstatic --noinput
echo ">> Pronto. Inicie com scripts/start.sh"
