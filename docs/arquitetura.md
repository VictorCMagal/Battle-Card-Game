# Arquitetura

Camadas: **Apresentação** (HTML/CSS/JS) → **Comunicação** (views REST + consumers WebSocket) → **Serviços**
(`accounts.services`, `decks.services`, `cards.services`, `game.runtime`) → **Domínio** (`engine`, Python puro) →
**Persistência** (Django ORM + MySQL). Diagramas: `docs/diagrams/arquitetura.mmd`.

* `engine.Game` recebe *comandos* (dicts) e devolve *eventos*. Não conhece rede, banco nem interface. Todas as
  validações ocorrem antes de mutar o estado: um `GameError` nunca deixa a partida inconsistente.
* `game.runtime`: `ROOMS` (salas em memória) e `GameSession` (uma por partida: timers de X/O, turno e reconexão,
  projeção de estado por jogador, persistência final). Tudo roda no event loop do Channels; operações de banco usam
  `database_sync_to_async`.
* Informação oculta: `Game.view_for(slot)` nunca inclui mão/deck do adversário nem o Card_ID de cartas face-down dele.
  No modo debug (um humano controla os dois lados) `reveal_all=True`.
* Extensibilidade: skills são plugins por chave (`engine/skills.py` + dados no banco); combinações são dados
  (`Combinacao`); tipos de carta não-SUMMON têm erro explícito de "não implementado"; `Game._trigger` é o ponto
  de extensão para efeitos de cartas; `GameSession` aceita qualquer fonte de comandos (base para NPC/IA).
* Limite: um processo Daphne por servidor de jogo (estado das partidas em memória; P§19). `InMemoryChannelLayer`
  por padrão; `CHANNEL_LAYER=redis` é opcional (o estado das partidas continua por processo).
