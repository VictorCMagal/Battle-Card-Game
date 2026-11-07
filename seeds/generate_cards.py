#!/usr/bin/env python3
"""Gera as 100 cartas iniciais (O§6) de forma DETERMINÍSTICA.

Saídas: seeds/cards.json, seeds/cards.csv e sql/20_seed_cards.sql.
Uso: python seeds/generate_cards.py
Regras (decisões D-08): 1-40 = Earth/Fire/Ice/Air (Power 1-10, nome Elemento+ID); 41-100 usam
elementos diferentes (W, M, U, B, S e combinações de 2). Skills em rodízio por grupos de 3 cartas
consecutivas. MANA GAIN: 2 a 4 entradas entre -3 e +3; cartas mais baratas ganham mais mana.
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from apps.cards.schema import ELEMENTS, to_csv  # noqa: E402
from engine.constants import ELEMENTS as ELEMENT_NAMES, mana_cost_for_power  # noqa: E402

SKILLS = [("Fire Ball", "2", 1), ("Teleport", "2", 2), ("Explosion", "3", 3)]
DUAL = [("F", "W"), ("I", "S"), ("E", "M"), ("A", "B"), ("U", "S"), ("W", "M"), ("B", "I"),
        ("F", "U"), ("E", "S"), ("A", "M")]


def base_elements(cid):
    """Elementos e Power de cada carta conforme o grupo do Card_ID."""
    if cid <= 40:
        return ["EFIA"[(cid - 1) // 10]], (cid - 1) % 10 + 1
    if cid <= 90:
        return ["WMUBS"[(cid - 41) // 10]], (cid - 41) % 10 + 1
    return list(DUAL[cid - 91]), cid - 91 + 3          # 91-100: Power 3..12


def mana_gains(cid, cost):
    """2-4 entradas; cartas baratas ganham mais, caras perdem mais (balanceamento)."""
    rng = random.Random(cid * 7919 + 13)
    n = 2 + cid % 3
    pos = {0: 3, 1: 2, 2: 1, 3: 1}[cost]
    neg = {0: 1, 1: 1, 2: 2, 3: 3}[cost]
    elems = rng.sample(list(ELEMENTS), n)
    return [{"element": e, "value": pos if i % 2 == 0 else -neg} for i, e in enumerate(elems)]


def build():
    cards = []
    for cid in range(1, 101):
        elements, power = base_elements(cid)
        cost = mana_cost_for_power(power)
        sname, snum, scost = SKILLS[((cid - 1) // 3) % 3]
        cards.append({
            "card_id": cid, "type": "SUMMON", "name": f"{ELEMENT_NAMES[elements[0]]}{cid}",
            "rarity": "common", "power": power, "power_bonus": 0, "attack_bonus": 0, "damage": 0,
            "shield": 0, "mana_cost": cost, "elements": elements, "mana_gains": mana_gains(cid, cost),
            "skills": [{"slot": 1, "name": sname, "number": snum, "manacost": scost,
                        "txt_key": "skill." + sname.lower().replace(" ", "_") + ".txt"}],
        })
    return cards


def q(v):
    return "'" + str(v).replace("'", "''") + "'"


def to_sql(cards):
    lines = ["-- Gerado por seeds/generate_cards.py. NÃO edite à mão.",
             "-- Requer as tabelas criadas pelas migrations (nomes de tabela do original).",
             "SET NAMES utf8mb4;", "START TRANSACTION;",
             "DELETE FROM Carta_Elemento WHERE carta_id BETWEEN 1 AND 100;",
             "DELETE FROM Carta_ManaGain WHERE carta_id BETWEEN 1 AND 100;",
             "DELETE FROM Carta_Skill WHERE carta_id BETWEEN 1 AND 100;"]
    for c in cards:
        lines.append(
            "INSERT INTO Carta (card_id, type, name, rarity, power, power_bonus, attack_bonus, damage, shield, mana_cost) "
            f"VALUES ({c['card_id']}, {q(c['type'])}, {q(c['name'])}, {q(c['rarity'])}, {c['power']}, {c['power_bonus']}, "
            f"{c['attack_bonus']}, {c['damage']}, {c['shield']}, {c['mana_cost']}) ON DUPLICATE KEY UPDATE "
            "type=VALUES(type), name=VALUES(name), rarity=VALUES(rarity), power=VALUES(power), "
            "mana_cost=VALUES(mana_cost);")
        for i, e in enumerate(c["elements"], 1):
            lines.append(f"INSERT INTO Carta_Elemento (carta_id, slot, element) VALUES ({c['card_id']}, {i}, {q(e)});")
        for i, g in enumerate(c["mana_gains"], 1):
            lines.append("INSERT INTO Carta_ManaGain (carta_id, slot, element, value) VALUES "
                         f"({c['card_id']}, {i}, {q(g['element'])}, {g['value']});")
        for s in c["skills"]:
            lines.append("INSERT INTO Carta_Skill (carta_id, slot, name, number, manacost, txt_key) VALUES "
                         f"({c['card_id']}, {s['slot']}, {q(s['name'])}, {q(s['number'])}, {s['manacost']}, {q(s['txt_key'])});")
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def main():
    cards = build()
    with open(os.path.join(ROOT, "seeds", "cards.json"), "w", encoding="utf-8") as f:
        json.dump({"cards": cards}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "seeds", "cards.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(to_csv(cards))
    with open(os.path.join(ROOT, "sql", "20_seed_cards.sql"), "w", encoding="utf-8") as f:
        f.write(to_sql(cards))
    print(f"{len(cards)} cartas geradas")


if __name__ == "__main__":
    main()
