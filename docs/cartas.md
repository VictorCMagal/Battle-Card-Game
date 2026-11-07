# Cartas

* 100 cartas iniciais geradas de forma **determinística** por `seeds/generate_cards.py` → `seeds/cards.json`, `seeds/cards.csv`, `sql/20_seed_cards.sql`.
* 1–40: Earth/Fire/Ice/Air, Power 1–10, nome Elemento+ID. 41–100: elementos diferentes (Warrior, Metal, Undead, Beast, Sorcery e duplos; 91–100 com Power 3–12).
* mana_cost por Power: 0–3→0, 4–6→1, 7–9→2, 10–12→3. MANA GAIN: 2–4 entradas entre −3 e +3, cartas baratas ganham mais. Uma skill por carta em rodízio por grupos de 3 IDs.
* Card_ID 0 é inválido (constraint e validação). Tipos: SUMMON (ativo), SPELL/EQUIPMENT/ITEM/FIELD/CURSE (reservados: erro "não implementado").
* Foil (1/100) e Shiny (1/8192) são por cópia; **não há aquisição de cartas no MVP**, logo não há sorteio; as cartas iniciais nunca são Foil/Shiny.
* Imagens: placeholders em CSS. Para trocar por arte real edite `frontend/static/assets/manifest.json` (`cards`, `foil`, `shiny` por Card_ID) sem mexer no código.

## Importação (painel → Cartas → Importar)

JSON: lista ou `{"cards":[...]}` com `card_id,type,name,rarity,power,power_bonus,attack_bonus,damage,shield,mana_cost,elements[],mana_gains[{element,value}],skills[{slot,name,number,manacost,txt_key}]`.
CSV: colunas `card_id,type,name,rarity,power,power_bonus,attack_bonus,damage,shield,mana_cost,elements,mana_gains,skills` com `elements` = `F|I`, `mana_gains` = `F:2|I:-1`,
`skills` = `1:Fire Ball:2:1:skill.fire_ball.txt|...`. O relatório lista criadas, atualizadas, ignoradas, duplicadas e linhas com erro.
Textos de skill ficam em `locale/<idioma>/messages.json` (`skill.<chave>.txt`). Skill nova: classe em `engine/skills.py` + linha no banco.
