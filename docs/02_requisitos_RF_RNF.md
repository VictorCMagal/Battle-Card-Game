# 2. Requisitos Funcionais (RF) e Não Funcionais (RNF) — BATTLE CARD-GAME

Fontes: especificação original v4 (**O§**), prompt-mestre (**P§**) e decisões da Fase 1 (**D-xx**).
Prioridade: **Obr** = obrigatório, **Imp** = importante, **Opc** = opcional (todos estão no escopo da Semana 1).

**Legenda de verificação nesta versão**

| Código | Significado |
|---|---|
| **Auto** | coberto por teste automatizado executado e aprovado (motor e regras puras: 56 testes) |
| **Manual** | código escrito, ainda **não executado**; depende de execução no ambiente do usuário (há testes Django escritos em `tests/django_tests/`) |
| **Auto + Manual** | a regra pura é testada; a integração (API, banco, tela) ainda não foi executada |
| **Estrutura** | mecanismo pronto, sem conteúdo cadastrado |

---

## A. Requisitos Funcionais

### A.1 Conta e acesso

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF01]** | O sistema deve permitir **criar conta** informando nome (4–16 caracteres, letras A–Z sem acento e dígitos), senha (6–32 caracteres), repetição da senha e e-mail (mais de 3 caracteres, com `@` e ao menos um `.` após o `@`, até 64 caracteres). | Obr | O§1, D-01, D-02 | Auto + Manual |
| **[RF02]** | O sistema deve garantir **unicidade de nome (sem diferenciar maiúsculas) e de e-mail** e informar a disponibilidade de forma assíncrona durante o preenchimento. | Obr | O§1 | Manual |
| **[RF03]** | O sistema deve permitir **login e logout** com nome e senha, mantendo a sessão por cookie seguro. | Obr | O§7 | Manual |
| **[RF04]** | O sistema deve permitir **uma única sessão ativa por conta**: um novo login encerra a sessão anterior, inclusive as conexões WebSocket. | Imp | D-26 | Manual |
| **[RF05]** | O sistema deve **limitar tentativas de login** (10 por 5 minutos por IP e nome) e **impedir login de contas bloqueadas** (`acc_code = RED`). | Obr | P§8, O§2.1 | Manual |
| **[RF06]** | O sistema deve manter **perfis de conta**: `DEV`, `ADMIN` (acessam o painel), `GREEN` (jogador), `RED` (bloqueado) e `GRAY` (reservado, sem comportamento). | Obr | O§2.1, D-04 | Manual |
| **[RF07]** | Ao criar uma conta, o sistema deve gerar o **Deck 1 com 40 cartas aleatórias** (Card_ID de 1 a 100, no máximo 3 iguais, sem Foil/Shiny), criar um **Grimorium vazio** e marcar `acc_status = 1`. | Obr | D-03 | Auto + Manual |

### A.2 Servidores, lobby, chat e salas

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF08]** | A página inicial deve exibir o **status do servidor** e o **número de usuários online**, com acesso a Login e Criar conta. | Obr | O§1 | Manual |
| **[RF09]** | O sistema deve permitir **selecionar o servidor** a partir de uma lista editável pelo administrador (MVP: "Servidor 1"). | Obr | O§7, D-24 | Manual |
| **[RF10]** | O lobby deve **listar as contas logadas** no servidor, atualizando em tempo real. | Obr | O§7 | Manual |
| **[RF11]** | O sistema deve oferecer **chat global do lobby** (máx. 126 caracteres, com hora do servidor e nome do remetente). | Obr | O§7 | Manual |
| **[RF12]** | O sistema deve oferecer **chat privado** entre dois usuários online. | Imp | P§20, D-22 | Manual |
| **[RF13]** | O sistema deve permitir **criar sala** informando nome, modo (1x1 ou Debug) e senha opcional. | Obr | O§7 | Manual |
| **[RF14]** | O sistema deve **listar, buscar por ID e entrar em salas** abertas, exigindo senha quando houver; o segundo jogador entra como Jogador B. Salas Debug não aceitam segundo jogador. | Obr | O§7, D-20 | Manual |
| **[RF15]** | O sistema deve permitir **convidar um usuário online** para a sala em que o convidante está. | Imp | P§21, D-22 | Manual |
| **[RF16]** | A sala deve exibir os estados **ABERTA, READY e EM BATALHA** e nunca permanecer vazia (se o Jogador A sai, o B assume o lugar de A). | Obr | O§7 | Manual |
| **[RF17]** | A sala deve ter **chat próprio** visível aos ocupantes. | Obr | O§7 | Manual |
| **[RF18]** | O sistema deve permitir **sair da sala**; sair durante a batalha equivale a derrota por abandono. | Obr | D-21 | Manual |
| **[RF19]** | O sistema deve exibir **notificações básicas** (convites, desconexão do adversário, erros de regra) sem recarregar a página. | Imp | P§21 | Manual |

### A.3 Decks e Grimorium

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF20]** | O sistema deve exibir os **6 slots de deck** e o **Grimorium** da conta, com suas cartas. | Obr | O§2.2, O§2.3 | Manual |
| **[RF21]** | O sistema deve permitir **criar, renomear e remover (apenas se vazio)** um deck. | Imp | P§13 | Manual |
| **[RF22]** | O sistema deve permitir **mover cartas entre decks e Grimorium** respeitando: deck com no máximo **40** cartas, no máximo **3 cópias do mesmo Card_ID por deck**, Grimorium com no máximo **500** cartas, e apenas cartas da própria conta. | Obr | O§2.2, O§2.3, D-05, D-06 | Auto (regras) + Manual |
| **[RF23]** | O sistema deve permitir **selecionar o deck** usado nas partidas. Slots 4 a 6 só ficam disponíveis com `premium_check`. | Obr | O§2.1 | Auto (regra de slot) + Manual |

### A.4 Preparação da partida

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF24]** | O sistema deve exigir que o jogador esteja **READY** com o deck selecionado contendo **exatamente 40 cartas**; a partida 1x1 inicia quando ambos estão READY e conectados (Debug: quando o único jogador dá READY). | Obr | O§3, D-05 | Manual |
| **[RF25]** | O sistema deve permitir a cada jogador **escolher X ou O uma única vez em 10 segundos**; quem não escolher recebe o símbolo restante (ou sorteio, se ninguém escolher). No modo Debug a atribuição é automática. | Obr | O§3.1, D-12 | Auto + Manual |
| **[RF26]** | O **servidor deve sortear o símbolo de iniciativa**; o jogador com o símbolo sorteado começa o turno 1. | Obr | O§3.1 | Auto |
| **[RF27]** | Ao iniciar, o sistema deve configurar cada jogador com **LIFE 20, MANA 1 (0–6), mão de 5 cartas (máx. 6)**, Deck da Batalha embaralhado, descarte público e **Avatar na arena 5x5** (posições (2,0) e (2,4)). | Obr | O§3.1, O§3.2 | Auto |

### A.5 Regras do turno e da arena

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF28]** | Cada turno deve durar **45 segundos**, com contador visual (aviso aos 15 s); ao zerar, o turno é encerrado pelo servidor. | Obr | O§3.3 | Auto (expiração) + Manual (contador) |
| **[RF29]** | Na fase **START**, o sistema deve comprar cartas até a mão ter 5; se o deck acabar, aplicar **DECK BURN** (1 LIFE por carta que faltou). | Obr | O§3.3, D-14 | Auto |
| **[RF30]** | O sistema deve permitir **WALKING_AVATAR** (um bloco N/S/L/O por turno; não sobre carta adversária; sobre carta própria a destrói). | Obr | O§3.3 | Auto |
| **[RF31]** | Ao fim do turno em que o Avatar não andou, o sistema deve aplicar **MEDITATION** (+1 MANA, máx. 6). | Obr | O§3.3 | Auto |
| **[RF32]** | O sistema deve permitir **SUMMONING** (uma vez por turno) de carta SUMMON da mão em bloco adjacente ou diagonal ao Avatar, face-up ou face-down. Sobre carta própria (sem combinação) a carta do bloco é descartada; sobre carta adversária resolve **ATTACK**; sobre o Avatar adversário só é permitido se o LIFE dele for ≤ Power da carta. | Obr | O§3.3, D-09 | Auto |
| **[RF33]** | O sistema deve permitir **DOUBLE CAST** (pagar 1 MANA após uma invocação para invocar uma segunda vez no mesmo turno). | Obr | O§3.3 | Auto |
| **[RF34]** | O sistema deve permitir **MOVEMENT** (um bloco N/S/L/O por turno por carta), vedado no turno da invocação (*Cooldown Effect*) e para o Avatar próprio. | Obr | O§3.3 | Auto |
| **[RF35]** | O sistema deve resolver **ATTACK** pelo *Damage System*: dano = Power efetivo + Attack_Bonus − Shield (mínimo 0); contra-ataque com o Power do alvo; dano excedente atinge o LIFE do dono da carta destruída; carta com Power efetivo ≤ 0 é destruída; o atacante vencedor ocupa o bloco do alvo (exceto Avatar). | Obr | O§5, D-10 | Auto |
| **[RF36]** | O sistema deve cobrar **MANA COST** uma vez ao revelar a carta (**FLIP EFFECT**); sem MANA suficiente, a carta é descartada e o jogador perde LIFE igual ao déficit (MANA vai a 0). | Obr | O§3.3, D-11 | Auto |
| **[RF37]** | O sistema deve aplicar **MANA GAIN** ao atacar, somando os valores configurados na carta cujo elemento coincide com os do alvo (limite 0–6; Avatar não gera MANA GAIN). | Obr | O§4, D-17 | Auto |
| **[RF38]** | O sistema deve permitir o uso de **skills ativas** (Fire Ball, Teleport, Explosion), uma por turno por carta, com carta face-up, fora do turno da invocação e antes de mover/atacar, pagando o MANA da skill. | Obr | O§3.3, D-16 | Auto |
| **[RF39]** | O sistema deve suportar **fusão/combinação (STACK e SUMMONING)** configurável por dados; sem combinação cadastrada, o movimento sobre carta própria é bloqueado. | Obr | O§3.3, D-15 | Estrutura (tabela vazia) |
| **[RF40]** | O sistema deve permitir **selecionar uma carta** (destaque visível a ambos sem revelar cartas ocultas) e **desmarcar com o botão direito**. | Obr | O§3.3 | Auto (parcial) + Manual |
| **[RF41]** | O sistema deve permitir **END TURN manual** e encerrar o turno **automaticamente** quando o jogador esgotar as ações possíveis. | Obr | O§3.3 | Auto + Manual |

### A.6 Fim de partida, resiliência e recompensas

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF42]** | O sistema deve encerrar a partida quando o LIFE de um jogador chegar a 0 ou menos (derrota) e declarar **empate** se ambos chegarem a 0 ou menos na mesma ação. | Obr | O§3.1, D-19 | Auto |
| **[RF43]** | O sistema deve aplicar **derrota por AFK** (modo 1x1) após 3 turnos consecutivos sem nenhuma ação do jogador (END TURN manual conta como ação). | Obr | O§3.3, D-13 | Auto |
| **[RF44]** | O sistema deve tratar **abandono** (sair da sala em batalha) como derrota sem Battlepoints, concedendo 10 BP ao adversário. | Obr | D-21 | Manual |
| **[RF45]** | O sistema deve permitir **reconexão** durante a partida: janela de 120 s com timers correndo; ao reconectar, o jogador recebe o estado atual; expirada a janela, perde por desconexão. | Imp | P§19, D-23 | Manual |
| **[RF46]** | O sistema deve oferecer o **modo Debug**: um usuário controla os dois lados, sem derrota por AFK e sem recompensas. | Obr | O§3, D-12 | Auto + Manual |
| **[RF47]** | O sistema deve conceder **recompensas** no modo 1x1: vitória por LIFE +100 BP / derrota +50 BP; empate +25 BP para ambos; AFK, abandono ou desconexão: vencedor +10 BP e perdedor 0; Magicdust +1 por carta destruída; `victory_counts` +1 ao vencedor. | Imp | O§1, D-07 | Auto (cálculo) + Manual (gravação) |
| **[RF48]** | O sistema deve **registrar o histórico** de cada partida (cabeçalho e eventos em ordem cronológica com numeração única por partida). | Obr | O§2.4 | Manual |

### A.7 Cartas, administração e operação

| ID | Requisito | Prior. | Origem | Verificação |
|---|---|---|---|---|
| **[RF49]** | O sistema deve carregar do banco um **catálogo de 100 cartas iniciais** (Card_ID 1–100; Card_ID 0 inválido), com atributos, elementos, MANA GAIN e skills. | Obr | O§4, O§6 | Auto (geração) + Manual (carga) |
| **[RF50]** | O painel deve permitir **criar, editar e remover cartas** (remoção bloqueada se a carta estiver em uso). | Imp | P§13.1 | Manual |
| **[RF51]** | O painel deve permitir **importar cartas via JSON ou CSV**, com validação e **relatório** de criadas, atualizadas, ignoradas, duplicadas e linhas com erro; e **exportar** o catálogo em JSON. | Imp | P§13.1 | Auto (validação/CSV) + Manual |
| **[RF52]** | O painel deve permitir **gerir contas** (perfil, premium, contadores, nova senha); somente `DEV` altera contas privilegiadas. | Imp | P§22 | Manual |
| **[RF53]** | O painel deve permitir **consultar decks, Grimoriums e histórico de partidas** com seus eventos. | Imp | P§22 | Manual |
| **[RF54]** | O painel deve permitir **gerir servidores e configurações** e **apagar mensagens de chat antigas**. | Opc | P§22 | Manual |
| **[RF55]** | O sistema deve oferecer **monitoramento em tempo real** (usuários online, conexões, salas, partidas ativas, erros recentes) a `ADMIN`/`DEV`. | Imp | P§23 | Manual |
| **[RF56]** | O sistema deve exibir todos os textos por **chaves de internacionalização** (PT-BR inicial), incluindo textos de skills. | Imp | P§29 | Manual |
| **[RF57]** | O sistema deve permitir **substituir imagens de cartas** (normal, Foil, Shiny) por um manifesto, sem alterar código; sem imagem, usa placeholders. | Opc | P§28, O§4 | Manual |

---

## B. Requisitos Não Funcionais

Metas marcadas como **alvo** ainda **não foram medidas** nesta versão.

### B.1 Desempenho e capacidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF01]** | O servidor deve processar um comando de jogo e devolver o novo estado em tempo percebido como imediato. | **Alvo:** ≤ 200 ms (p95) em rede local com 10 partidas simultâneas |
| **[RNF02]** | O servidor deve suportar uso simultâneo moderado em um único processo. | **Alvo:** ≥ 50 conexões WebSocket e ≥ 10 partidas simultâneas |
| **[RNF03]** | O temporizador do turno deve ter precisão adequada. | Desvio ≤ 1 s em relação aos 45 s configurados; o cliente usa o relógio do servidor |
| **[RNF04]** | O painel de monitoramento deve atualizar a cada 2 segundos. | Observação manual |

### B.2 Persistência e integridade

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF05]** | Dados persistentes (contas, decks, Grimoriums, cartas, histórico, chat) devem ser gravados em **MySQL** com charset `utf8mb4`. | Inspeção do banco após o setup |
| **[RNF06]** | Operações que alteram decks/Grimorium devem ser **atômicas** (transação com trava de linha). | Testes `DeckServiceTests` (escritos) |
| **[RNF07]** | O histórico de eventos deve ter **ordem garantida** por numeração única por partida. | Restrição `UNIQUE(partida, seq)` |
| **[RNF08]** | Dados de cartas, skills e combinações devem residir no banco, **não no código**. | Revisão de código; importação via painel |
| **[RNF09]** | **Limitação aceita:** o estado de partidas em andamento é mantido em memória; reiniciar o servidor encerra as partidas, e o histórico de uma partida só é gravado ao seu término. | Documentado em `docs/pendencias.md` |

### B.3 Usabilidade e acessibilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF10]** | A interface deve estar em **português do Brasil**, com mensagens de erro de regra claras e acionáveis. | Revisão das chaves `err.*` |
| **[RNF11]** | O jogador deve ver continuamente **LIFE, MANA, mão, deck, descarte, turno e tempo restante**, e os blocos válidos de ação devem ser destacados. | Teste manual da arena |
| **[RNF12]** | O layout deve ser **responsivo** (cartas redimensionadas proporcionalmente à tela). | Teste em larguras de 360 a 1920 px |
| **[RNF13]** | Eventos importantes devem ser anunciados a leitores de tela (`aria-live`) e os controles devem ser acessíveis por teclado quando possível. | Verificação básica; **sem auditoria WCAG** nesta versão |
| **[RNF14]** | Formulários devem dar **retorno imediato** (validação no cliente espelhando o servidor, que sempre revalida). | Teste manual |

### B.4 Segurança

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF15]** | Senhas devem ser armazenadas apenas como **hash** do Django; nunca registradas em log. | Revisão; filtro `RedactFilter` |
| **[RNF16]** | O servidor deve ser **autoritativo**: o cliente não define o jogador do comando e toda ação é validada antes de alterar o estado. | Testes do motor; revisão |
| **[RNF17]** | **Informação oculta** (mão e deck do adversário, Card_ID de cartas face-down) não deve ser enviada ao cliente adversário. | Teste `test_hidden_info_not_leaked` |
| **[RNF18]** | Requisições HTTP que alteram estado devem ter **proteção CSRF**; cookies `HttpOnly` e `SameSite`, `Secure` com HTTPS. | Revisão/teste manual |
| **[RNF19]** | WebSockets exigem **sessão válida** e **origem permitida**, com limite de 8 KB por mensagem e 40 mensagens por 5 s. | Teste `test_ws` (escrito) |
| **[RNF20]** | O frontend deve evitar **XSS**: texto de usuário só via `textContent`, sem scripts e estilos inline, com **CSP** restritiva. | Revisão; busca por `innerHTML`/`style=` |
| **[RNF21]** | Acesso ao SQL somente por **ORM parametrizado**; permissões por perfil (`ADMIN`/`DEV` no painel). | Revisão de código |
| **[RNF22]** | Sorteios (embaralhar, X/O, iniciativa, deck inicial) devem usar gerador **criptograficamente seguro**. | Revisão (`secrets.SystemRandom`) |
| **[RNF23]** | Chat e login devem ter **limitação de taxa** contra abuso. | Testes escritos |

### B.5 Portabilidade e implantação

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF24]** | O sistema deve rodar em **Windows e Linux** com Python 3.11+ e MySQL 8, **sem Docker obrigatório**. | Instalação com `scripts/setup.*` |
| **[RNF25]** | Configuração por **arquivo `.env`**; segredos fora do código e do Git. | Presença de `.env.example` e `.gitignore` |
| **[RNF26]** | O frontend deve funcionar em **navegadores modernos** (versões recentes de Chrome, Edge, Firefox e Safari) sem dependências de CDN. | Teste manual |
| **[RNF27]** | O canal de mensagens deve funcionar sem Redis (memória) e permitir **Redis opcional** por configuração. | Variável `CHANNEL_LAYER` |

### B.6 Manutenibilidade, extensibilidade e observabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF28]** | As regras devem estar isoladas em um **motor sem dependência de Django, banco ou rede**, testável por unidade. | Execução dos testes sem Django |
| **[RNF29]** | Novas **skills**, **combinações**, **tipos de carta** e **idiomas** devem ser adicionados sem alterar o núcleo do motor. | Registro de skills; tabela `Combinacao`; dicionários `locale/` |
| **[RNF30]** | O sistema deve manter **logs com rotação** por categoria (django, ws, match, app), sem dados sensíveis. | Arquivos em `logs/` |
| **[RNF31]** | O código deve ser comentado e acompanhado de **documentação técnica e diagramas** (Mermaid). | Pasta `docs/` |
| **[RNF32]** | Deve haver **testes automatizados** do motor e das regras puras executáveis sem infraestrutura. | `scripts/run_tests.sh` (56 testes) |

### B.7 Confiabilidade

| ID | Requisito | Critério de verificação |
|---|---|---|
| **[RNF33]** | Uma ação inválida **não deve alterar** o estado da partida e deve retornar mensagem de erro de regra. | Testes do motor (`GameError`) |
| **[RNF34]** | Quedas de conexão do cliente devem permitir **reconexão automática** com *backoff* e ressincronização do estado. | Teste manual |
| **[RNF35]** | Falha ao persistir o histórico não deve impedir o encerramento da partida para os jogadores. | Revisão do fluxo de encerramento |

---

## C. Matriz de rastreabilidade resumida

| Fonte | Requisitos |
|---|---|
| O§1 Website e conta | RF01–RF03, RF06, RF08, RF47 |
| O§2 Banco, decks e Grimorium | RF04–RF07, RF20–RF23, RF48 |
| O§3 Mecânica da partida | RF24–RF46 |
| O§4 e O§6 Cartas | RF37–RF39, RF49–RF51, RF57 |
| O§5 Damage System | RF35 |
| O§7 Lobby, salas e chat | RF09–RF19 |
| P§ Prompt-mestre (segurança, painel, i18n, logs) | RF50–RF56, RNF05–RNF35 |
