# Decisões aprovadas (Fase 1) e como foram aplicadas

Respostas do usuário prevalecem sobre as recomendações originais.

| ID | Decisão final | Onde |
|---|---|---|
| D-01 | `acc_password` compatível com o hash do Django (**VARCHAR(128)**); e-mail **VARCHAR(64)**; PIN anulável; `codigo_id` gerado | `accounts/models.py` |
| D-02 | Nome: A–Z sem acento + dígitos, 4–16, único sem diferenciar maiúsculas | `accounts/rules.py` |
| D-03 | **40 cartas aleatórias** (Card_ID 1–100, máx. 3 iguais) no Deck 1; **Grimorium inicial com 0 cartas**; vale para contas de teste (3 decks cada); sem Foil/Shiny; `acc_status=1` | `decks/services.py`, `seed_dev` |
| D-04 | `GRAY` aceito sem comportamento | `AccCode` |
| D-05 | Inventário = Decks + Grimorium; salvar deck ≤ 40; jogar exige exatamente 40 | `decks/services.py` |
| D-06 | Limite de 3 cópias é **por deck** (6 decks → até 18 iguais na conta); Grimoriums de teste vazios | `decks/rules.py` |
| D-07 | BP/magicdust/victory_counts conforme original; sem loja; score só armazenado | `game/rewards.py` |
| D-08 | Cartas 41–100 e skills em rodízio (determinístico) | `seeds/generate_cards.py` |
| D-09 | Summon sobre bloco ocupado (Avatar só como golpe final; carta própria é substituída; adversária = ataque) | `engine/game.py` |
| D-10 | `level` = **Power**; §5 como regra única; Power efetivo; dano mínimo 0; excesso ao LIFE do dono; **atacante vencedor ocupa o bloco do alvo destruído (não se for Avatar)** | `engine/game.py` |
| D-11 | MANA COST insuficiente: MANA→0 e LIFE −(custo−MANA); flip por ataque revela→cobra→combate | `engine/game.py` |
| D-12 | Debug: X/O automático, um usuário controla A e B, sem BP | `runtime.py` |
| D-13 | AFK: turnos sem ação (END TURN manual conta); zera ao agir; não vale no debug | `engine/game.py` |
| D-14 | DECK BURN: compra o que houver, −1 LIFE por carta faltante | `engine/game.py` |
| D-15 | STACK sem combinação: bloqueado; tabela vazia | `engine/combos.py` |
| D-16 | Skills conforme proposta (sem alcance no Fire Ball; Teleport 2 passos sem ataque; Explosion inclui próprias e Avatares; skill ignora Shield) | `engine/skills.py` |
| D-17 | MANA GAIN soma elementos; Avatar não gera; limite 0–6 | `engine/game.py` |
| D-18/19 | `secrets.SystemRandom`; "mesma ação" = um comando | `engine`, `runtime` |
| D-20 | Salas: ABERTA / READY (2 jogadores) / EM BATALHA; sem espectadores; debug visível e não clicável; senha na entrada | `runtime.py` |
| D-21 | Sair durante a batalha = derrota por abandono (sem BP; adversário +10) | `consumers.py` |
| D-22 | Chat privado entre online; convite = convidar para a sua sala; notificações como toasts | `consumers.py` |
| D-23 | Reconexão 120 s; timers continuam; expirada = derrota sem BP, adversário +10 | `runtime.py` |
| D-24 | Um servidor ("Servidor 1") em tabela editável | `core/models.py` |
| D-25 | Testes possíveis executados; o restante o usuário roda ao baixar o .zip | `docs/pendencias.md` |
| D-26/27/28 | Sessão única; fuso configurável; versões fixadas por faixa + venv/pip, Docker opcional só para o MySQL | settings, scripts |
