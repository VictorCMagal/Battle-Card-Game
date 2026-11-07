"""Definições imutáveis de cartas (CardDef) e instâncias em jogo (CardInstance)."""
from dataclasses import dataclass
from typing import Optional, Tuple

from .constants import CARD_TYPES, ELEMENTS


def skill_key(name: str) -> str:
    """Normaliza o nome de uma skill para a chave do registro ("Fire Ball" -> "fire_ball")."""
    return name.strip().lower().replace(" ", "_")


@dataclass(frozen=True)
class ManaGain:
    """Uma configuração de MANA GAIN: ao atacar carta com `element`, ganha/perde `value`."""
    element: str
    value: int


@dataclass(frozen=True)
class SkillDef:
    """Skill de uma carta (skillX_name, skillX_number, skillX_manacost, skillX_txt)."""
    slot: int
    name: str
    number: str
    manacost: int
    txt_key: str  # chave de i18n, nunca o texto literal

    @property
    def key(self) -> str:
        return skill_key(self.name)


@dataclass(frozen=True)
class CardDef:
    """Definição de uma carta (dados vindos do banco). Card_ID 0 é inválido."""
    card_id: int
    type: str
    name: str
    elements: Tuple[str, ...]
    power: int
    power_bonus: int = 0
    attack_bonus: int = 0
    shield: int = 0
    mana_cost: int = 0
    mana_gains: Tuple[ManaGain, ...] = ()
    skills: Tuple[SkillDef, ...] = ()
    rarity: str = "common"

    def __post_init__(self):
        if self.card_id < 1:
            raise ValueError("Card_ID 0 (ou negativo) é inválido")
        if self.type not in CARD_TYPES:
            raise ValueError(f"TYPE inválido: {self.type}")
        if len(self.elements) > 4 or any(e not in ELEMENTS for e in self.elements):
            raise ValueError("Elementos inválidos (0 a 4 elementos válidos)")
        if len(self.skills) > 3 or len(self.mana_gains) > 4:
            raise ValueError("Máximo de 3 skills e 4 MANA GAIN")


@dataclass
class CardInstance:
    """Carta em uma partida (mão, deck, arena ou descarte). Também representa o Avatar."""
    uid: str
    owner: str                       # "A" ou "B"
    card_id: Optional[int] = None    # None para o Avatar
    defn: Optional[CardDef] = None
    is_avatar: bool = False
    face_up: bool = False
    damage: int = 0
    power_bonus: int = 0
    attack_bonus: int = 0
    shield: int = 0
    x: int = -1
    y: int = -1
    mana_paid: bool = False          # MANA COST cobrado nesta permanência na arena
    summoned_turn: int = -1
    moves_used: int = 0
    moves_allowed: int = 1
    skill_used: bool = False
    attacked: bool = False
    teleport: bool = False
    is_foil: bool = False
    is_shiny: bool = False

    # --- atributos derivados -------------------------------------------------
    @property
    def name(self) -> str:
        return "Avatar" if self.is_avatar else self.defn.name

    @property
    def type(self) -> str:
        return "AVATAR" if self.is_avatar else self.defn.type

    @property
    def elements(self):
        return () if self.is_avatar else self.defn.elements

    @property
    def power(self) -> int:
        return 0 if self.is_avatar else self.defn.power

    @property
    def mana_cost(self) -> int:
        return 0 if self.is_avatar else self.defn.mana_cost

    @property
    def effective_power(self) -> int:
        """Power efetivo = Power + Power_Bonus - Damage (D-10)."""
        return self.power + self.power_bonus - self.damage

    def reset_for_hand(self):
        """Zera o estado de arena (carta que volta à mão/descarte)."""
        self.damage = self.power_bonus = self.attack_bonus = 0
        self.shield = 0 if self.is_avatar else self.defn.shield
        self.mana_paid = False
        self.x = self.y = -1
        self.moves_used = 0
        self.skill_used = self.attacked = self.teleport = False
        self.face_up = False

    def view(self, full: bool) -> dict:
        """Representação enviada ao cliente. `full=False` oculta tudo menos o dono."""
        base = {"uid": self.uid, "owner": self.owner, "face_up": self.face_up,
                "is_avatar": self.is_avatar, "x": self.x, "y": self.y}
        if self.is_avatar:
            base.update(name="Avatar", type="AVATAR")
            return base
        if not full:
            return base
        d = self.defn
        base.update(
            card_id=d.card_id, name=d.name, type=d.type, elements=list(d.elements),
            power=self.power, power_bonus=self.power_bonus, attack_bonus=self.attack_bonus,
            damage=self.damage, shield=self.shield, mana_cost=d.mana_cost,
            effective_power=self.effective_power, is_foil=self.is_foil, is_shiny=self.is_shiny,
            mana_gains=[{"element": g.element, "value": g.value} for g in d.mana_gains],
            skills=[{"slot": s.slot, "key": s.key, "name": s.name, "number": s.number,
                     "manacost": s.manacost, "txt_key": s.txt_key} for s in d.skills],
            skill_used=self.skill_used, moves_left=self.moves_allowed - self.moves_used,
            rarity=d.rarity,
        )
        return base


def make_avatar(owner: str, x: int, y: int) -> CardInstance:
    """Cria a carta Avatar do jogador (sempre face_up)."""
    return CardInstance(uid=f"avatar-{owner}", owner=owner, is_avatar=True, face_up=True, x=x, y=y)
