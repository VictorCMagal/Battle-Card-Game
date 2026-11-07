"""Regras de decks e Grimorium com transações e travas (select_for_update)."""
import uuid

from django.db import transaction

from apps.cards.models import Carta
from apps.core.errors import ServiceError

from . import rules
from .models import Deck, DeckCarta, Grimorium, GrimoriumCarta


def ensure_grimorium(owner) -> Grimorium:
    """Garante o Grimorium da conta (1 por conta) e o vincula em Conta.grimorium."""
    if owner.grimorium_id:
        return owner.grimorium
    g = Grimorium.objects.filter(owner=owner).first() or Grimorium.objects.create(owner=owner)
    owner.grimorium = g
    owner.save(update_fields=["grimorium"])
    return g


@transaction.atomic
def create_deck(owner, slot: int, name: str = None) -> Deck:
    """Cria o deck vazio do slot (4-6 só com premium_check)."""
    if not rules.slot_allowed(slot, owner.premium_check):
        raise ServiceError("err.slot_locked", 403)
    if Deck.objects.filter(owner=owner, slot=slot).exists():
        raise ServiceError("err.slot_in_use", 409)
    deck = Deck.objects.create(owner=owner, slot=slot, name=(name or f"Deck {slot}")[:32])
    setattr(owner, f"deck_{slot}", deck)
    owner.save(update_fields=[f"deck_{slot}"])
    return deck


@transaction.atomic
def create_starter_setup(owner, rng=None, deck_count: int = 1) -> None:
    """Deck(s) inicial(is) com 40 cartas aleatórias (máx. 3 iguais por deck), sem Foil/Shiny,
    e Grimorium vazio (D-03). Contas de teste usam deck_count=3."""
    ids = list(Carta.objects.filter(type="SUMMON", card_id__gte=1).values_list("card_id", flat=True))
    ensure_grimorium(owner)
    try:
        for slot in range(1, deck_count + 1):
            deck = create_deck(owner, slot)
            chosen = rules.random_starter_card_ids(ids, rng)
            DeckCarta.objects.bulk_create([DeckCarta(deck=deck, carta_id=cid) for cid in chosen])
    except ValueError:
        raise ServiceError("err.catalog_insufficient", 500)
    owner.acc_status = 1  # starter deck selecionado
    owner.selected_deck = 1
    owner.save(update_fields=["acc_status", "selected_deck"])


def _cards_payload(qs):
    return [{"card_uid": str(c.card_uid), "card_id": c.carta_id, "is_foil": c.is_foil, "is_shiny": c.is_shiny}
            for c in qs.order_by("carta_id", "id")]


def decks_payload(owner) -> dict:
    """Estado completo do editor: 6 slots + Grimorium."""
    decks = {d.slot: d for d in Deck.objects.filter(owner=owner)}
    slots = []
    for slot in range(1, rules.DECK_SLOTS + 1):
        d = decks.get(slot)
        item = {"slot": slot, "locked": not rules.slot_allowed(slot, owner.premium_check),
                "deck_id": d.id if d else None, "name": d.name if d else None, "count": 0, "cards": []}
        if d:
            item["cards"] = _cards_payload(d.cards)
            item["count"] = len(item["cards"])
        slots.append(item)
    g = ensure_grimorium(owner)
    gcards = _cards_payload(g.cards)
    return {"selected": owner.selected_deck, "deck_size": rules.DECK_SIZE, "max_copies": rules.MAX_COPIES,
            "slots": slots, "grimorium": {"id": g.id, "count": len(gcards), "max": rules.GRIMORIUM_MAX,
                                          "cards": gcards}}


@transaction.atomic
def move_card(owner, card_uid: str, kind: str, deck_id=None) -> None:
    """Move uma cópia entre decks/Grimorium do mesmo dono, validando os limites do destino."""
    try:
        uid = uuid.UUID(str(card_uid))
    except ValueError:
        raise ServiceError("err.card_not_found", 404)
    src = (DeckCarta.objects.select_for_update().filter(card_uid=uid, deck__owner=owner).first()
           or GrimoriumCarta.objects.select_for_update().filter(card_uid=uid, grimorium__owner=owner).first())
    if src is None:
        raise ServiceError("err.card_not_found", 404)
    if kind == "deck":
        dest = Deck.objects.select_for_update().filter(id=deck_id, owner=owner).first()
        if dest is None:
            raise ServiceError("err.deck_not_found", 404)
        if isinstance(src, DeckCarta) and src.deck_id == dest.id:
            return
        err = rules.can_add_to_deck(list(dest.cards.values_list("carta_id", flat=True)), src.carta_id)
        if err:
            raise ServiceError(err, 409)
        new = DeckCarta(deck=dest, carta_id=src.carta_id, is_foil=src.is_foil, is_shiny=src.is_shiny, card_uid=src.card_uid)
    elif kind == "grimorium":
        dest = Grimorium.objects.select_for_update().get(id=ensure_grimorium(owner).id)
        if isinstance(src, GrimoriumCarta):
            return
        err = rules.can_add_to_grimorium(dest.cards.count())
        if err:
            raise ServiceError(err, 409)
        new = GrimoriumCarta(grimorium=dest, carta_id=src.carta_id, is_foil=src.is_foil, is_shiny=src.is_shiny,
                             card_uid=src.card_uid)
    else:
        raise ServiceError("err.invalid_destination")
    src.delete()   # libera o card_uid (unique) antes de recriar no destino
    new.save()


@transaction.atomic
def select_deck(owner, slot: int) -> None:
    deck = Deck.objects.filter(owner=owner, slot=slot).first()
    if deck is None or not rules.slot_allowed(slot, owner.premium_check):
        raise ServiceError("err.deck_not_found", 404)
    owner.selected_deck = slot
    owner.save(update_fields=["selected_deck"])


@transaction.atomic
def rename_deck(owner, deck_id: int, name: str) -> None:
    name = (name or "").strip()
    if not name or len(name) > 32:
        raise ServiceError("err.deck_name")
    if not Deck.objects.filter(id=deck_id, owner=owner).update(name=name):
        raise ServiceError("err.deck_not_found", 404)


@transaction.atomic
def delete_deck(owner, deck_id: int) -> None:
    deck = Deck.objects.select_for_update().filter(id=deck_id, owner=owner).first()
    if deck is None:
        raise ServiceError("err.deck_not_found", 404)
    if deck.cards.exists():
        raise ServiceError("err.deck_not_empty", 409)
    deck.delete()


def build_battle_deck(owner) -> list:
    """Deck selecionado em formato do motor. Exige exatamente 40 cartas (D-05)."""
    deck = Deck.objects.filter(owner=owner, slot=owner.selected_deck).first()
    if deck is None or not rules.slot_allowed(deck.slot, owner.premium_check):
        raise ServiceError("err.no_deck_selected")
    cards = list(deck.cards.all())
    if len(cards) != rules.DECK_SIZE:
        raise ServiceError("err.deck_incomplete", count=len(cards), size=rules.DECK_SIZE)
    return [{"uid": str(c.card_uid), "card_id": c.carta_id, "is_foil": c.is_foil, "is_shiny": c.is_shiny}
            for c in cards]
