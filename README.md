# BATTLE CARD-GAME

Jogo de cartas online 1x1 (Python · Django · Django Channels/WebSockets · MySQL · HTML/CSS/JS).
Servidor autoritativo: o navegador só envia pedidos; as regras vivem no pacote `engine/` (Python puro).

> **Leia primeiro `docs/pendencias.md`.** Nesta entrega, o motor de jogo (`engine/`) e as regras puras foram
> testados (56 testes passando). O código Django/Channels/MySQL e o frontend foram escritos, mas **não puderam ser
> executados** no ambiente de desenvolvimento (sem Django, MySQL e internet). Rode a suíte completa na sua máquina.

## Início rápido (Linux/macOS)

```bash
# 1) MySQL 8 rodando e banco criado (edite a senha em sql/00_create_database.sql antes)
mysql -u root -p < sql/00_create_database.sql
# 2) 1ª execução cria .env; edite as credenciais do banco e rode de novo
scripts/setup.sh
scripts/setup.sh --dev-data        # cria as 3 contas de teste (veja abaixo)
# 3) iniciar
scripts/start.sh                   # Daphne (HTTP + WebSocket) em http://localhost:8000
```

Windows: `scripts\setup.bat`, `scripts\start.bat`. Sem MySQL local: `docker compose up -d db` (só o banco; veja `docker-compose.yml`).

## Contas de teste (`seed_dev`)

`TesteA`, `TesteB` (jogadores) e `TesteC` (**ADMIN**, acessa `/painel/`). Senha = `SEED_TEST_PASSWORD` do `.env`.
Cada conta tem 3 decks de 40 cartas aleatórias (máx. 3 iguais por deck) e Grimorium vazio. **Não use em produção.**
Para criar um administrador real: `python manage.py createadmin NOME EMAIL`.

## Testes

```bash
scripts/run_tests.sh               # motor + regras puras (não exige Django)
scripts/run_tests.sh --django      # inclui testes Django com SQLite (exige setup)
```

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `engine/` | regras do jogo em Python puro (turnos, combate, skills, projeção por jogador) |
| `apps/accounts` | Conta (modelo de usuário), cadastro, login, regras de validação |
| `apps/cards` | catálogo de cartas (banco), importação JSON/CSV, cache |
| `apps/decks` | Decks, Grimorium, deck inicial aleatório |
| `apps/game` | salas, partidas (runtime), WebSockets, histórico, recompensas |
| `apps/chat` | chat (lobby, sala, privado), limites e persistência |
| `apps/painel` | painel administrativo e monitoramento |
| `apps/core` | servidores, i18n, presença, páginas, middleware de segurança |
| `frontend/` | templates, CSS, JS (sem scripts/estilos inline) |
| `seeds/`, `sql/` | 100 cartas (JSON/CSV/SQL gerados), scripts SQL |
| `docs/` | documentação e diagramas Mermaid (`docs/diagrams/*.mmd`) |

## Documentação

`docs/arquitetura.md` · `banco.md` · `apis.md` · `websockets.md` · `regras.md` · `combate.md` · `cartas.md` ·
`instalacao.md` · `configuracao.md` · `dependencias.md` · `seguranca.md` · `manutencao.md` · `decisoes.md` · `pendencias.md`
