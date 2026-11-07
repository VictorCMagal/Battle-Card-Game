"""Constantes das regras do BATTLE CARD-GAME (documento original, seções 3 e 4).

Todos os valores numéricos de regra ficam aqui para facilitar ajustes futuros
sem tocar na lógica do motor.
"""

LIFE_START = 20            # LIFE inicial (O§3.1)
MANA_START = 1             # MANA inicial
MANA_MAX = 6
MANA_MIN = 0
HAND_START = 5             # mão inicial e alvo de compra na fase START
HAND_MAX = 6               # cartas acima disso são descartadas
HAND_MIN = 0
DECK_SIZE = 40             # tamanho exigido do Deck_da_Batalha (O§2.2 / O§3.1)
MAX_COPIES_PER_DECK = 3    # máximo de Card_ID iguais por deck

BOARD_W = 5
BOARD_H = 5
AVATAR_START = {"A": (2, 0), "B": (2, 4)}

TURN_SECONDS = 45          # duração do turno (O§3.3)
TURN_WARNING_SECONDS = 15  # contador visual
COIN_SECONDS = 10          # escolha X/O
AFK_LIMIT = 3              # turnos consecutivos sem ação

DOUBLE_CAST_COST = 1

# Contra-ataque: o original usa "Cardblocking.Power" (valor bruto). Se True, usa o
# Power efetivo (Power + Power_Bonus - Damage). Decisão D-10: valor bruto.
COUNTER_USES_EFFECTIVE_POWER = False

ELEMENTS = {
    "E": "Earth", "S": "Sorcery", "F": "Fire", "W": "Warrior", "I": "Ice",
    "A": "Air", "M": "Metal", "U": "Undead", "B": "Beast",
}
CARD_TYPES = ("SUMMON", "SPELL", "EQUIPMENT", "ITEM", "FIELD", "CURSE")

# Tabela de custo de MANA por Power (O§6)
def mana_cost_for_power(power: int) -> int:
    """Retorna o mana_cost padrão para um Power (0-3:0, 4-6:1, 7-9:2, 10-12:3)."""
    if power <= 3:
        return 0
    if power <= 6:
        return 1
    if power <= 9:
        return 2
    return 3
