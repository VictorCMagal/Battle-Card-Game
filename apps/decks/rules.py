"""Regras puras de decks/Grimorium (O§2.2/O§2.3) e geração do deck inicial (D-03)."""
import random
from collections import Counter

DECK_SIZE = 40
MAX_COPIES = 3
GRIMORIUM_MAX = 500
DECK_SLOTS = 6
FREE_SLOTS = 3  # slots 4-6 exigem premium_check


def random_starter_card_ids(available_ids, rng=None, size=DECK_SIZE, max_copies=MAX_COPIES):
    """Sorteia `size` Card_ID com no máximo `max_copies` iguais (deck inicial, D-03).

    Levanta ValueError se o catálogo for pequeno demais."""
    rng = rng or random.SystemRandom()
    pool = [cid for cid in available_ids for _ in range(max_copies)]
    if len(pool) < size:
        raise ValueError("Catálogo insuficiente para gerar o deck inicial")
    rng.shuffle(pool)
    return pool[:size]


def can_add_to_deck(card_ids_in_deck, card_id) -> str:
    """Retorna "" se a carta pode entrar no deck, ou a chave do erro."""
    if len(card_ids_in_deck) >= DECK_SIZE:
        return "err.deck_full"
    if Counter(card_ids_in_deck)[card_id] >= MAX_COPIES:
        return "err.deck_max_copies"
    return ""


def can_add_to_grimorium(current_count) -> str:
    return "err.grimorium_full" if current_count >= GRIMORIUM_MAX else ""


def slot_allowed(slot: int, premium: bool) -> bool:
    """Slots 1-3 livres; 4-6 só com premium_check."""
    return 1 <= slot <= DECK_SLOTS and (slot <= FREE_SLOTS or premium)
