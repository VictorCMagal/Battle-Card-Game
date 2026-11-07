# APIs REST (JSON)

Todas as respostas: `{"ok": true, ...}` ou `{"ok": false, "error": "<chave i18n>", "message": "<texto>"}`.
Mutações exigem o cabeçalho `X-CSRFToken` (token no `<meta name="csrf-token">`). Rotas autenticadas respondem 401 sem sessão.

| Método e rota | Auth | Descrição |
|---|---|---|
| `GET /api/status/` | não | status do servidor e usuários online |
| `GET /api/servidores/` | não | servidores ativos e ocupação |
| `GET /api/i18n/` | não | dicionário de textos do idioma atual |
| `POST /api/contas/` | não | cadastro `{name,password,password2,email}` → 201 / 422 (`fields`) / 409 |
| `GET /api/contas/disponibilidade/?name=&email=` | não | checagem assíncrona (30/min por IP) |
| `POST /api/login/` | não | `{name,password}`; 10 tentativas/5 min por IP+nome; sessão única |
| `POST /api/logout/`, `GET /api/me/` | sim | sessão e dados da conta |
| `GET /api/cartas/` | sim | catálogo completo |
| `GET/POST /api/decks/` | sim | lista decks+Grimorium / cria deck `{slot,name}` |
| `PATCH/DELETE /api/decks/<id>/` | sim | renomeia / remove deck vazio |
| `POST /api/decks/mover/` | sim | `{card_uid, kind:"deck"\|"grimorium", deck_id?}` |
| `POST /api/decks/selecionar/` | sim | `{slot}` define o deck das partidas |
| `GET /api/salas/?server=` | sim | snapshot das salas (criar/entrar usam WebSocket) |

Painel (`/painel/...`, somente ADMIN/DEV): contas, cartas (CRUD, importar JSON/CSV, exportar), decks, histórico, configurações, monitor.
