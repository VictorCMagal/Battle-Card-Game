# Configuração (.env)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | — | obrigatória |
| `DEBUG` | False | nunca True em produção |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | localhost | hosts/origens aceitos (também valida o Origin do WebSocket) |
| `SECURE_COOKIES` | False | True com HTTPS |
| `DB_ENGINE` | mysql | `sqlite` só para a suíte de testes |
| `DB_NAME/USER/PASSWORD/HOST/PORT` | — | MySQL |
| `CHANNEL_LAYER` | memory | `redis` opcional (`REDIS_URL`, instale `channels-redis`) |
| `IDIOMA` | PT-BR | pasta em `locale/` (ex.: PT-BR → `locale/pt_BR`) |
| `TIME_ZONE` | America/Sao_Paulo | fuso do relógio do chat |
| `LOG_DIR`, `LOG_LEVEL` | logs, INFO | logs rotativos por categoria |
| `SEED_TEST_PASSWORD` | — | senha das contas de teste |

Constantes de regra em `engine/constants.py`; limites de chat/login/reconexão em `config/settings.py` (`CHAT_RATE`, `LOGIN_RATE`, `RECONNECT_SECONDS`…).
