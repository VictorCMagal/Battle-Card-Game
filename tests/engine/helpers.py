"""Utilitários de teste do motor: catálogo pequeno e Game determinístico."""
from engine import CardDef, Game, ManaGain, SkillDef


class NoShuffle:
    """RNG determinístico: não embaralha, choice pega o primeiro."""
    def shuffle(self, x):
        pass

    def choice(self, seq):
        return seq[0]


def card(cid, power, elements=("F",), cost=0, shield=0, gains=(), skills=(), type_="SUMMON", **kw):
    return CardDef(card_id=cid, type=type_, name=f"C{cid}", elements=tuple(elements), power=power,
                   mana_cost=cost, shield=shield, mana_gains=tuple(ManaGain(*g) for g in gains),
                   skills=tuple(SkillDef(*s) for s in skills), **kw)


def catalog(*cards):
    return {c.card_id: c for c in cards}


def new_game(cat, deck_a=None, deck_b=None, mode="versus", first="A"):
    """Cria jogo com decks de 10 cópias do menor Card_ID (ou os fornecidos) e inicia."""
    ids = sorted(cat)
    deck_a = deck_a or [ids[0]] * 10
    deck_b = deck_b or [ids[0]] * 10
    g = Game(cat, mode=mode, rng=NoShuffle())
    g.setup([{"uid": f"a{i}", "card_id": c} for i, c in enumerate(deck_a)],
            [{"uid": f"b{i}", "card_id": c} for i, c in enumerate(deck_b)])
    g.start(first)
    return g
