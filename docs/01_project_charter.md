# 1. Project Charter (Termo de Abertura) — BATTLE CARD-GAME

| Campo | Conteúdo |
|---|---|
| Projeto | BATTLE CARD-GAME (identificador técnico `BATTLE_CARD_GAME`) |
| Versão do documento | 1.0 — baseado na primeira versão entregue (Fase 2) |
| Fontes | Especificação original `BATTLE_CARD-GAME_v4.docx`, prompt-mestre de desenvolvimento, decisões D-01 a D-28 aprovadas na Fase 1 |
| Horizonte | "Esta semana" = **Semana 1**, a primeira entrega (MVP jogável) |

> **Nota de premissa:** o texto do pedido fala em "o que está dentro e fora do escopo desta semana". Este documento trata a *Semana 1* como a entrega do `BATTLE_CARD_GAME.zip`. Se o ciclo for outro, apenas a seção 3 precisa ser reclassificada.

---

## A. Justificativa e visão geral do produto

### A.1 Justificativa

Jogos de cartas colecionáveis com combate tático em tabuleiro exigem regras precisas (custos de mana, dano acumulado, contra-ataque, turnos cronometrados) e proteção contra trapaça. Em um jogo online, a única forma de garantir justiça é um **servidor autoritativo**: o cliente apenas pede ações e o servidor decide o resultado.

O projeto nasce da necessidade de ter, de forma própria e extensível, um jogo cuja especificação já existe em documento (regras, atributos de carta, dados de teste), mas que ainda não tinha implementação. A primeira versão valida as regras e a arquitetura antes de investir em conteúdo (arte, mais cartas, economia).

Motivadores principais:

1. **Validar a mecânica** descrita no documento original (arena 5x5, Avatar, invocação, combate por *Damage System*, skills) com um motor executável e testável.
2. **Criar uma base extensível**: novas cartas, skills, combinações e idiomas entram por dados, sem alterar o núcleo.
3. **Garantir integridade**: regras no servidor, informação oculta protegida, persistência transacional de contas, decks e histórico.
4. **Preparar o futuro**: arquitetura pronta para NPC/IA, novos tipos de carta e loja, sem implementá-los agora.

### A.2 Visão geral do produto

**BATTLE CARD-GAME** é um jogo de cartas online **1x1** jogado no navegador. Cada jogador controla um **Avatar** em uma arena de **5x5 blocos**, invoca criaturas (cartas SUMMON) ao redor do Avatar e as usa para mover, atacar e usar skills, buscando reduzir o **LIFE** do adversário de 20 a 0.

| Aspecto | Descrição |
|---|---|
| Plataforma | Aplicação web (HTML/CSS/JS) + servidor Python (Django, Django Channels/WebSocket) + MySQL |
| Modos | **1x1** (dois jogadores) e **Debug** (um jogador controla os dois lados, sem recompensas) |
| Fluxo do jogador | Criar conta → login → escolher servidor → lobby (chat, salas) → sala → READY → X/O → partida |
| Meta-jogo | Decks (6 slots, 40 cartas, até 3 cópias iguais por deck), Grimorium (até 500 cartas), Battlepoints e Magicdust |
| Administração | Painel web para contas, cartas (CRUD e importação JSON/CSV), decks, histórico, configurações e monitoramento em tempo real |
| Idioma inicial | Português do Brasil, com estrutura de internacionalização |

---

## B. Objetivos SMART do software

Convenções: **E**specífico, **M**ensurável, **A**tingível, **R**elevante, **T**emporal. "S1" = fim da Semana 1; "S2" = fim da Semana 2 (próximo ciclo).

| ID | Objetivo | Específico | Mensurável | Atingível | Relevante | Prazo |
|---|---|---|---|---|---|---|
| OBJ-01 | Motor de regras completo e testado | Implementar em Python puro as regras de turno, invocação, movimento, combate, skills, mana, AFK e fim de partida (RF27–RF43, RF46) | Suíte automatizada do motor e das regras puras com **todos os testes passando** (56 na versão atual); toda regra listada tem ao menos um teste, exceto STACK/combinações (tabela entregue vazia) | Sim: motor isolado de rede e banco | Base da justiça do jogo | **S1** (cumprido) |
| OBJ-02 | Jornada completa de uma partida 1x1 | Duas contas criam conta, entram na mesma sala, dão READY, escolhem X/O e terminam uma partida com resultado e recompensa gravados | Roteiro manual de aceitação (UC01→UC09) executado **sem erro bloqueante** em ambiente com MySQL | Sim, após a primeira execução ajustar eventuais falhas | Prova de valor do produto | **S1** execução pelo usuário; ajustes em **S2** |
| OBJ-03 | Persistência íntegra | Contas, decks, Grimoriums e histórico gravados em MySQL com transações; limites (40 cartas, 3 cópias por deck, 500 no Grimorium) nunca violados | 100% das tentativas de violar limites rejeitadas (testes `tests/django_tests`) | Sim | Evita corrupção de dados | **S2** (testes escritos, execução pendente) |
| OBJ-04 | Segurança básica | Senha com hash, CSRF, CSP, validação de origem do WebSocket, limite de taxa em login e chat, estado oculto não enviado ao adversário | Checklist de `docs/seguranca.md` com 100% dos itens verificados por revisão e teste | Sim | Exposição pública exige | **S2** |
| OBJ-05 | Extensibilidade por dados | Adicionar carta, skill de catálogo, combinação ou idioma sem editar o motor | Uma carta nova importada via painel (JSON/CSV) aparece no catálogo e joga em uma partida sem alterar código | Sim | Reduz custo de evolução | **S2** |
| OBJ-06 | Operação observável | Logs rotativos por categoria e painel de monitoramento em tempo real | Painel exibe usuários online, salas, partidas e erros com atualização ≤ 2 s | Sim | Suporte e diagnóstico | **S2** |
| OBJ-07 | Portabilidade | Instalação em Windows e Linux sem Docker obrigatório | Instalação do zero em cada SO em **≤ 30 minutos** seguindo `docs/instalacao.md` | Sim | Facilita uso e testes | **S2** |

---

## C. Escopo preliminar

### C.1 Dentro do escopo (Semana 1)

**Conta e acesso**
- Cadastro com validações, login/logout, sessão única por conta, perfis `DEV`, `ADMIN`, `GREEN`, `RED` (e `GRAY` reservado).
- Deck inicial de 40 cartas aleatórias (máx. 3 iguais) e Grimorium vazio por conta.

**Lobby e salas**
- Seleção de servidor, lobby com contas online, chat global, chat privado e convites.
- Criação, busca e entrada em salas (com senha opcional), estados ABERTA / READY / EM BATALHA, chat da sala.

**Cartas e decks**
- Catálogo de 100 cartas iniciais (dados no banco), editor de decks e Grimorium (mover cartas, renomear, selecionar deck).

**Partida**
- X/O, iniciativa, LIFE/MANA/mão, turno de 45 s, WALKING_AVATAR, MEDITATION, SUMMONING, DOUBLE CAST, MOVEMENT, ATTACK com *Damage System*, MANA COST, FLIP EFFECT, MANA GAIN, skills Fire Ball, Teleport e Explosion, DECK BURN, AFK, abandono, reconexão, modo Debug, histórico e recompensas.

**Administração e operação**
- Painel (contas, cartas, importação/exportação, decks, histórico, configurações), monitor em tempo real, logs, internacionalização PT-BR.
- Scripts de instalação (Windows/Linux), documentação e diagramas.

### C.2 Expressamente fora do escopo (Semana 1)

| Item excluído | Observação |
|---|---|
| Loja, pagamentos, moeda real, compra de premium | Apenas campos armazenados (`cur_cash`, `premium_check`) |
| Aquisição de cartas (pacotes, drop, crafting) | Logo, sem sorteio de Foil/Shiny; as cartas iniciais nunca são Foil/Shiny |
| Ranking público e matchmaking automático | `score` só é armazenado |
| Tipos de carta SPELL, EQUIPMENT, ITEM, FIELD, CURSE | Retornam erro "não implementado" |
| Combinações/fusões de cartas (conteúdo) | Motor pronto; tabela `Combinacao` entregue vazia |
| PIN, verificação de e-mail, recuperação de senha | Campos existem; sem fluxo |
| NPC/IA | Apenas arquitetura preparada |
| Espectadores e replays na interface | Histórico gravado, sem visualizador |
| Escala horizontal (vários processos) e retomada de partida após reinício | Estado de partida em memória, por processo |
| Aplicativo nativo mobile, notificações push | Somente navegador |
| Arte final de cartas, animações e áudio | Placeholders substituíveis por manifesto |
| Moderação automática de chat | Existe o campo `moderado` para evolução |

### C.3 Entregáveis da Semana 1

`BATTLE_CARD_GAME.zip` (código, scripts, SQL, seeds, testes e documentação técnica) e esta documentação de projeto (Charter, Requisitos, Casos de Uso e User Stories).

### C.4 Premissas, restrições e riscos

| Tipo | Descrição |
|---|---|
| Premissa | O documento original v4 e as decisões D-01 a D-28 são a fonte de verdade das regras |
| Premissa | O usuário executa e valida o sistema no próprio ambiente (Python 3.11+, MySQL 8) |
| Restrição | Servidor único; estado das partidas em memória; Redis opcional apenas para o canal de mensagens |
| Restrição | Sem dependências externas de frontend (sem CDN) |
| **Risco R1** | O código Django/Channels/MySQL e as telas foram escritos, mas **ainda não executados** (só o motor e as regras puras foram testados). Mitigação: execução guiada do roteiro UC01→UC09 e `scripts/run_tests.sh --django` |
| **Risco R2** | Migrations ainda não geradas (geradas na primeira instalação). Mitigação: versioná-las após o `setup` |
| **Risco R3** | Versões de dependências definidas por faixa, sem verificação. Mitigação: `pip freeze` após o primeiro setup |
| Risco R4 | Reinício do servidor encerra partidas em andamento e perde seu histórico. Mitigação: documentado; evolução futura para estado compartilhado |
| Risco R5 | Regras omissas no original foram resolvidas por decisões (D-xx); uma carta invocada que não destrói o alvo é descartada sem confirmação explícita |

### C.5 Critérios de sucesso do projeto (Semana 1)

1. Suíte automatizada do motor 100% verde.
2. Instalação concluída em ambiente com MySQL e login de contas de teste.
3. Uma partida 1x1 completa, do READY ao resultado, com histórico e recompensas gravados.
4. Painel acessível apenas a `ADMIN`/`DEV`.

---

## D. Stakeholders e público-alvo

### D.1 Stakeholders

| Stakeholder | Papel | Interesse / expectativa | Influência |
|---|---|---|---|
| Solicitante do projeto (autor da especificação) | Patrocinador e *Product Owner* | Regras fiéis ao documento; entrega testável; decide ambiguidades | Alta |
| Equipe de desenvolvimento (solicitante + assistente de IA) | Execução | Código claro, testável e documentado | Alta |
| Jogadores | Usuários finais | Partidas justas, rápidas e sem travamentos; interface clara | Média |
| Administradores (`ADMIN`) | Operação | Gerir contas, cartas e acompanhar o servidor | Média |
| Desenvolvedores (`DEV`) | Manutenção | Evoluir regras, cartas e skills com baixo risco | Média |
| Testadores/QA | Validação | Roteiros e critérios de aceite claros | Média |
| Infraestrutura/hospedagem (a definir) | Operação em produção | Requisitos de HTTPS, WebSocket, MySQL e logs | Baixa (nesta semana) |

### D.2 Público-alvo

| Segmento | Perfil | Necessidades |
|---|---|---|
| Jogadores de card games táticos | Adultos e jovens com familiaridade com jogos de cartas/tabuleiro | Regras profundas, partidas curtas (turnos de 45 s), deck próprio |
| Jogadores casuais | Querem jogar rápido contra um amigo | Criar sala, convidar, jogar sem instalação |
| Operadores do jogo | Administram o servidor | Painel simples, importação em lote de cartas |

> Os perfis acima são hipóteses de trabalho derivadas da natureza do produto; o documento original não define personas.
