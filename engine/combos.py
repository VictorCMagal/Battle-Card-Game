"""Tabela de FUSÃO/COMBINAÇÃO configurável por dados (O§3.3 SUMMONING e STACK).

Nenhuma combinação é embutida no código (P§15.14): a tabela vem do banco
(`Combinacao`) e está vazia na entrega.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Combo:
    """Regra de combinação entre a carta do bloco (`block`) e a carta que chega (`incoming`).

    effect_type:
      * create_card  -> effect_value é o Card_ID da carta resultante (substitui a carta que chega)
      * power_delta  -> soma effect_value ao Power_Bonus da carta do bloco
      * shield_delta -> soma effect_value ao Shield da carta do bloco
    """
    name: str
    effect_type: str
    effect_value: int
    block_card_id: Optional[int] = None
    block_element: Optional[str] = None
    incoming_card_id: Optional[int] = None
    incoming_element: Optional[str] = None

    def matches(self, block, incoming) -> bool:
        conds = (self.block_card_id, self.block_element, self.incoming_card_id, self.incoming_element)
        if all(c is None for c in conds):
            return False  # nunca casa "tudo"
        if self.block_card_id is not None and block.card_id != self.block_card_id:
            return False
        if self.block_element is not None and self.block_element not in block.elements:
            return False
        if self.incoming_card_id is not None and incoming.card_id != self.incoming_card_id:
            return False
        if self.incoming_element is not None and self.incoming_element not in incoming.elements:
            return False
        return True


class ComboTable:
    """Conjunto de combinações ativas."""

    def __init__(self, combos: Optional[List[Combo]] = None):
        self.combos = list(combos or [])

    def find(self, block, incoming) -> Optional[Combo]:
        for combo in self.combos:
            if combo.matches(block, incoming):
                return combo
        return None
