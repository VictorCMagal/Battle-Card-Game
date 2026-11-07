# Combate (Damage System, original §5 + decisões D-09/D-10/D-16/D-17)

* **Power efetivo** = Power + Power_Bonus − Damage. A carta é destruída com Power efetivo ≤ 0 (vai ao descarte, +1 magicdust ao autor).
* **Ataque** (movendo ou invocando sobre carta adversária): revela primeiro o alvo e depois o atacante (cobrando MANA COST; se alguma for descartada, não há combate).
  `dano = max(0, Power efetivo do atacante + Attack_Bonus − Shield do alvo)` somado ao `damage` do alvo.
  **Contra-ataque:** `max(0, Power do alvo − Shield do atacante)` somado ao `damage` do atacante (valor bruto, como no original;
  `engine/constants.py: COUNTER_USES_EFFECTIVE_POWER` muda isso). O contra-ataque ocorre mesmo se o alvo morrer.
* **Dano excedente:** vai ao LIFE do dono da carta destruída (do alvo e também do atacante). Exemplo do original: atacante 10 × alvo 5 → alvo destruído, LIFE do dono −5, atacante fica com 5 de Power.
* **Atacante vencedor ocupa o bloco do alvo** (exceto Avatar, que nunca é destruído). Se o alvo sobrevive, o atacante por movimento permanece onde está; **uma carta invocada que não destrói o alvo é descartada** (herdado do texto de §3.3 — ver pendências).
* **Ataque ao Avatar:** `LIFE −= Power efetivo + Attack_Bonus`. Sem MANA GAIN contra Avatar.
* **MANA GAIN:** soma dos valores das configurações do atacante cujo elemento aparece no alvo; MANA limitado a 0–6.
* **Skills:** Fire Ball (custo 1, 2 de dano em SUMMON adversária face-up, sem alcance, ignora Shield), Teleport (custo 2, 2 movimentos, sem ataque),
  Explosion (custo 3, 3 de dano nas 8 casas ao redor face-up — inclui cartas próprias e Avatares; dano de skill não transborda para o LIFE, exceto o dano direto ao Avatar).
