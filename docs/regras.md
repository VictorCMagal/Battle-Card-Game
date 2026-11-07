# Regras implementadas (resumo operacional)

Base: documento original v4 + decisões D-01…D-28 (`docs/decisoes.md`).

* **Início:** ambos READY; LIFE 20, MANA 1 (0–6), mão 5 (máx. 6), deck embaralhado (`secrets.SystemRandom`), Avatares em (2,0) e (2,4).
  X/O em 10 s (uma escolha por jogador; faltantes recebem o restante/sorteio); o servidor sorteia a iniciativa. Debug: automático.
* **Turno (45 s, aviso aos 15 s):** START (compra até 5; DECK BURN = 1 LIFE por carta faltante) → ACTION → ENDING
  (MEDITATION +1 MANA se o Avatar não andou). Fim automático quando não há mais ações possíveis.
* **Ações:** WALKING_AVATAR (1 bloco N/S/L/O; sobre carta própria a destrói; não sobre carta adversária) · SUMMONING (1/turno, blocos ao redor
  do Avatar, face-up/down; sobre carta própria sem combinação a descarta; sobre carta adversária = ATTACK; sobre o Avatar adversário só se LIFE ≤ Power) ·
  DOUBLE CAST (1 MANA, 2ª invocação) · MOVEMENT (1/turno, não no turno da invocação) · SKILL (1/turno, face-up, não no turno da invocação nem após mover/atacar) · END TURN.
* **MANA COST:** cobrado na 1ª vez que a carta fica face-up na arena. Sem MANA: carta descartada, MANA→0 e LIFE −(custo−MANA).
* **Fim:** LIFE ≤ 0 derrota; ambos ≤ 0 na mesma ação = empate; 3 turnos consecutivos sem ação (1x1) = derrota AFK; abandono/desconexão expirada = derrota.
* **Recompensas (1x1):** vitória por LIFE +100 BP, derrota +50, empate +25 (ambos); AFK/abandono: vencedor +10, perdedor 0; magicdust +1 por carta destruída; victory_counts +1. Debug não concede nada.
Detalhes do combate: `docs/combate.md`.
