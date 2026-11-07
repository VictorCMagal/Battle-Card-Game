# Instalação

Requisitos: Python 3.11+, MySQL 8.x (ou `docker compose up -d db`), compilador/headers para `mysqlclient`
(Linux: `libmysqlclient-dev`/`default-libmysqlclient-dev` e `pkg-config`; Windows normalmente usa wheel pronto).

1. Crie o banco/usuário: ajuste a senha e rode `mysql -u root -p < sql/00_create_database.sql`.
2. `scripts/setup.sh` (1ª vez cria `.env`; edite `DB_*`, `ALLOWED_HOSTS`) e rode de novo. Ele instala dependências, gera/aplica migrations, carrega `Servidor 1` e as 100 cartas e coleta estáticos.
3. `scripts/setup.sh --dev-data` para contas de teste (opcional).
4. `scripts/start.sh` (Daphne) ou `scripts/start.sh dev` (runserver ASGI com recarga). Acesse http://localhost:8000.
5. Administrador: `python manage.py createadmin NOME EMAIL` (ou use `TesteC` dos dados de teste).
Produção: HTTPS com proxy reverso que repasse WebSocket (`Upgrade`), `DEBUG=False`, `SECURE_COOKIES=True`, `CSRF_TRUSTED_ORIGINS` e `ALLOWED_HOSTS` corretos.
