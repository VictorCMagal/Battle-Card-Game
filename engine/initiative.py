"""Escolha de X/O e iniciativa (O§3.1). Funções puras, sem I/O."""
import random
from typing import Optional, Tuple

from .errors import GameError

SYMBOLS = ("X", "O")


def resolve_symbols(choice_a: Optional[str], choice_b: Optional[str], rng=None) -> Tuple[str, str]:
    """Resolve os símbolos finais de A e B após as escolhas/timeout.

    * ninguém escolheu -> sorteio (um X, outro O)
    * só um escolheu   -> o outro recebe o símbolo restante
    * ambos escolheram -> devem ser diferentes
    """
    rng = rng or random.SystemRandom()
    for c in (choice_a, choice_b):
        if c is not None and c not in SYMBOLS:
            raise GameError("err.invalid_symbol")
    if choice_a is None and choice_b is None:
        a = rng.choice(SYMBOLS)
        return a, ("O" if a == "X" else "X")
    if choice_a is None:
        return ("O" if choice_b == "X" else "X"), choice_b
    if choice_b is None:
        return choice_a, ("O" if choice_a == "X" else "X")
    if choice_a == choice_b:
        raise GameError("err.symbol_taken")
    return choice_a, choice_b


def draw_initiative(symbol_a: str, symbol_b: str, rng=None) -> Tuple[str, str]:
    """O servidor sorteia o símbolo de iniciativa. Retorna (símbolo, slot que começa)."""
    rng = rng or random.SystemRandom()
    sym = rng.choice(SYMBOLS)
    return sym, ("A" if symbol_a == sym else "B")
