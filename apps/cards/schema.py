"""Validação e conversão de cartas (JSON/CSV) sem dependência de Django.

Usado pela importação do painel (P§13.1), pelos seeds e pelos testes.
"""
import csv
import io
import json

CARD_TYPES = ("SUMMON", "SPELL", "EQUIPMENT", "ITEM", "FIELD", "CURSE")
ELEMENTS = ("E", "S", "F", "W", "I", "A", "M", "U", "B")
CSV_COLUMNS = ["card_id", "type", "name", "rarity", "power", "power_bonus", "attack_bonus", "damage",
               "shield", "mana_cost", "elements", "mana_gains", "skills"]


def validate_card_dict(d: dict) -> list:
    """Retorna lista de mensagens de erro (vazia se a carta é válida)."""
    errs = []

    def is_int(v, lo=None, hi=None):
        return isinstance(v, int) and not isinstance(v, bool) and (lo is None or v >= lo) and (hi is None or v <= hi)

    if not is_int(d.get("card_id"), 1):
        errs.append("card_id deve ser inteiro >= 1 (Card_ID 0 é inválido)")
    if d.get("type") not in CARD_TYPES:
        errs.append("type inválido")
    if not str(d.get("name", "")).strip() or len(str(d.get("name", ""))) > 64:
        errs.append("name obrigatório (até 64 caracteres)")
    for f, lo, hi in (("power", 0, 99), ("power_bonus", -99, 99), ("attack_bonus", -99, 99),
                      ("damage", 0, 99), ("shield", 0, 99), ("mana_cost", 0, 6)):
        if not is_int(d.get(f, 0), lo, hi):
            errs.append(f"{f} deve ser inteiro entre {lo} e {hi}")
    els = d.get("elements", [])
    if not isinstance(els, list) or len(els) > 4 or len(set(els)) != len(els) \
            or any(e not in ELEMENTS for e in els):
        errs.append("elements: até 4 elementos válidos e distintos")
    gains = d.get("mana_gains", [])
    if not isinstance(gains, list) or len(gains) > 4:
        errs.append("mana_gains: no máximo 4")
    else:
        for g in gains:
            if not isinstance(g, dict) or g.get("element") not in ELEMENTS or not is_int(g.get("value"), -3, 3):
                errs.append("mana_gains: element válido e value entre -3 e 3")
                break
    skills = d.get("skills", [])
    if not isinstance(skills, list) or len(skills) > 3:
        errs.append("skills: no máximo 3")
    else:
        slots = set()
        for s in skills:
            ok = (isinstance(s, dict) and is_int(s.get("slot"), 1, 3) and str(s.get("name", "")).strip()
                  and is_int(s.get("manacost", 0), 0, 6))
            if not ok or s["slot"] in slots:
                errs.append("skills: slot 1-3 único, name e manacost válidos")
                break
            slots.add(s["slot"])
    return errs


def normalize_card_dict(d: dict) -> dict:
    """Completa defaults e normaliza tipos de uma carta já válida."""
    return {
        "card_id": int(d["card_id"]), "type": d["type"], "name": str(d["name"]).strip(),
        "rarity": str(d.get("rarity") or "common"), "power": int(d.get("power", 0)),
        "power_bonus": int(d.get("power_bonus", 0)), "attack_bonus": int(d.get("attack_bonus", 0)),
        "damage": int(d.get("damage", 0)), "shield": int(d.get("shield", 0)),
        "mana_cost": int(d.get("mana_cost", 0)), "elements": list(d.get("elements", [])),
        "mana_gains": [{"element": g["element"], "value": int(g["value"])} for g in d.get("mana_gains", [])],
        "skills": [{"slot": int(s["slot"]), "name": s["name"].strip(), "number": str(s.get("number", "")),
                    "manacost": int(s.get("manacost", 0)), "txt_key": s.get("txt_key") or
                    "skill." + s["name"].strip().lower().replace(" ", "_") + ".txt"}
                   for s in d.get("skills", [])],
    }


def parse_json(text: str) -> list:
    """Lê uma lista de cartas de um JSON (lista ou {"cards": [...]})."""
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("cards", [])
    if not isinstance(data, list):
        raise ValueError("JSON deve ser uma lista de cartas")
    return data


def _int(v, default=0):
    v = (v or "").strip()
    return int(v) if v else default


def parse_csv(text: str) -> list:
    """Converte CSV (colunas em CSV_COLUMNS) em lista de dicts de carta.

    elements: "F|I"; mana_gains: "F:2|I:-1"; skills: "1:Fire Ball:2:1:skill.fire_ball.txt|..."
    (slot:name:number:manacost:txt_key)."""
    cards = []
    for row in csv.DictReader(io.StringIO(text)):
        gains = [{"element": p.split(":")[0], "value": int(p.split(":")[1])}
                 for p in (row.get("mana_gains") or "").split("|") if p.strip()]
        skills = []
        for p in (row.get("skills") or "").split("|"):
            if p.strip():
                slot, name, number, cost, txt = (p.split(":") + [""] * 5)[:5]
                skills.append({"slot": int(slot), "name": name, "number": number,
                               "manacost": int(cost or 0), "txt_key": txt})
        cards.append({
            "card_id": _int(row.get("card_id"), 0), "type": (row.get("type") or "").strip(),
            "name": (row.get("name") or "").strip(), "rarity": (row.get("rarity") or "common").strip(),
            "power": _int(row.get("power")), "power_bonus": _int(row.get("power_bonus")),
            "attack_bonus": _int(row.get("attack_bonus")), "damage": _int(row.get("damage")),
            "shield": _int(row.get("shield")), "mana_cost": _int(row.get("mana_cost")),
            "elements": [e for e in (row.get("elements") or "").split("|") if e.strip()],
            "mana_gains": gains, "skills": skills,
        })
    return cards


def to_csv(cards: list) -> str:
    """Serializa cartas para o formato CSV aceito por `parse_csv`."""
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(CSV_COLUMNS)
    for c in cards:
        w.writerow([c["card_id"], c["type"], c["name"], c["rarity"], c["power"], c["power_bonus"],
                    c["attack_bonus"], c["damage"], c["shield"], c["mana_cost"], "|".join(c["elements"]),
                    "|".join(f'{g["element"]}:{g["value"]}' for g in c["mana_gains"]),
                    "|".join(f'{s["slot"]}:{s["name"]}:{s["number"]}:{s["manacost"]}:{s["txt_key"]}'
                             for s in c["skills"])])
    return out.getvalue()


def analyze_import(cards: list) -> dict:
    """Valida um lote e detecta Card_ID duplicado no próprio arquivo.

    Retorna {"valid": [...normalizadas], "errors": [(linha, [msgs])], "duplicates": [card_id]}."""
    valid, errors, dup, seen = [], [], [], set()
    for i, d in enumerate(cards, start=1):
        errs = validate_card_dict(d)
        if errs:
            errors.append((i, errs))
            continue
        n = normalize_card_dict(d)
        if n["card_id"] in seen:
            dup.append(n["card_id"])
            errors.append((i, ["Card_ID duplicado no arquivo"]))
            continue
        seen.add(n["card_id"])
        valid.append(n)
    return {"valid": valid, "errors": errors, "duplicates": dup}
