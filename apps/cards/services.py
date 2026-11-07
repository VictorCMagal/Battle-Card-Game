"""Acesso ao catálogo: conversão para o motor, cache, importação e exportação."""
import threading

from django.db import transaction

from engine import CardDef, Combo, ComboTable, ManaGain, SkillDef

from . import schema
from .models import Carta, CartaElemento, CartaManaGain, CartaSkill, Combinacao

_lock = threading.Lock()
_cache = {"catalog": None, "combos": None}


def invalidate_cache() -> None:
    """Chamar após qualquer alteração de cartas/combinações."""
    with _lock:
        _cache["catalog"] = _cache["combos"] = None


def carta_to_def(c: Carta) -> CardDef:
    return CardDef(
        card_id=c.card_id, type=c.type, name=c.name, rarity=c.rarity,
        elements=tuple(e.element for e in sorted(c.elementos.all(), key=lambda x: x.slot)),
        power=c.power, power_bonus=c.power_bonus, attack_bonus=c.attack_bonus, shield=c.shield,
        mana_cost=c.mana_cost,
        mana_gains=tuple(ManaGain(g.element, g.value) for g in sorted(c.managains.all(), key=lambda x: x.slot)),
        skills=tuple(SkillDef(s.slot, s.name, s.number, s.manacost, s.txt_key)
                     for s in sorted(c.skills.all(), key=lambda x: x.slot)))


def load_catalog() -> dict:
    """Catálogo {card_id: CardDef} (em cache até `invalidate_cache`)."""
    with _lock:
        if _cache["catalog"] is None:
            qs = Carta.objects.prefetch_related("elementos", "managains", "skills")
            _cache["catalog"] = {c.card_id: carta_to_def(c) for c in qs}
        return _cache["catalog"]


def load_combos() -> ComboTable:
    with _lock:
        if _cache["combos"] is None:
            _cache["combos"] = ComboTable([
                Combo(name=c.nome, effect_type=c.effect_type, effect_value=c.effect_value,
                      block_card_id=c.block_card_id, block_element=c.block_element or None,
                      incoming_card_id=c.incoming_card_id, incoming_element=c.incoming_element or None)
                for c in Combinacao.objects.filter(ativo=True)])
        return _cache["combos"]


def def_to_payload(d: CardDef) -> dict:
    return {"card_id": d.card_id, "type": d.type, "name": d.name, "rarity": d.rarity,
            "elements": list(d.elements), "power": d.power, "power_bonus": d.power_bonus,
            "attack_bonus": d.attack_bonus, "shield": d.shield, "mana_cost": d.mana_cost,
            "mana_gains": [{"element": g.element, "value": g.value} for g in d.mana_gains],
            "skills": [{"slot": s.slot, "name": s.name, "number": s.number, "manacost": s.manacost,
                        "txt_key": s.txt_key} for s in d.skills]}


@transaction.atomic
def upsert_card(n: dict) -> bool:
    """Cria/atualiza uma carta normalizada. Retorna True se foi criada."""
    obj, created = Carta.objects.update_or_create(card_id=n["card_id"], defaults={
        "type": n["type"], "name": n["name"], "rarity": n["rarity"], "power": n["power"],
        "power_bonus": n["power_bonus"], "attack_bonus": n["attack_bonus"], "damage": n["damage"],
        "shield": n["shield"], "mana_cost": n["mana_cost"]})
    obj.elementos.all().delete()
    obj.managains.all().delete()
    obj.skills.all().delete()
    CartaElemento.objects.bulk_create([CartaElemento(carta=obj, slot=i, element=e)
                                       for i, e in enumerate(n["elements"], 1)])
    CartaManaGain.objects.bulk_create([CartaManaGain(carta=obj, slot=i, element=g["element"], value=g["value"])
                                       for i, g in enumerate(n["mana_gains"], 1)])
    CartaSkill.objects.bulk_create([CartaSkill(carta=obj, slot=s["slot"], name=s["name"], number=s["number"],
                                               manacost=s["manacost"], txt_key=s["txt_key"]) for s in n["skills"]])
    return created


def import_cards(raw_cards: list, overwrite: bool = True) -> dict:
    """Importa uma lista de cartas (já parseada de JSON/CSV) e devolve o relatório.

    Cartas inválidas ou duplicadas no arquivo são ignoradas e relatadas. Com `overwrite=False`,
    Card_ID já existentes no banco também são ignorados (relatados em `existing`)."""
    analysis = schema.analyze_import(raw_cards)
    created = updated = 0
    existing = []
    present = set(Carta.objects.filter(card_id__in=[c["card_id"] for c in analysis["valid"]])
                  .values_list("card_id", flat=True))
    for n in analysis["valid"]:
        if n["card_id"] in present and not overwrite:
            existing.append(n["card_id"])
            continue
        created_now = upsert_card(n)
        created += int(created_now)
        updated += int(not created_now)
    invalidate_cache()
    return {"created": created, "updated": updated, "existing": existing,
            "errors": analysis["errors"], "duplicates": analysis["duplicates"]}


def export_cards() -> list:
    """Exporta o catálogo atual no formato JSON de importação."""
    return [def_to_payload(d) | {"damage": 0} for d in load_catalog().values()]
