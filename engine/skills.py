"""Registro de SKILLS ativas. Para criar uma skill nova basta registrar uma classe aqui
(e cadastrar a carta/skill no banco); o motor não precisa mudar.

Cada skill implementa `validate` (sem efeitos colaterais) e `execute`.
O custo de MANA e as regras gerais (1 skill por turno, não no turno da invocação,
não após ATTACK/MOVEMENT) são verificados pelo motor antes de chamar a skill.
"""
from .errors import GameError

SKILL_REGISTRY = {}


def register(key):
    """Decorator que registra a skill sob a chave normalizada (ex.: "fire_ball")."""
    def deco(cls):
        SKILL_REGISTRY[key] = cls()
        return cls
    return deco


NEIGHBORS_8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


@register("fire_ball")
class FireBall:
    """Custo 1. Seleciona SUMMON adversária face_up e causa 2 de dano (ignora Shield, D-16)."""
    damage = 2

    def validate(self, game, caster, target):
        try:
            tile = (int(target["x"]), int(target["y"]))
        except (TypeError, KeyError, ValueError):
            raise GameError("err.skill_invalid_target")
        card = game.board.get(tile)
        if (card is None or card.owner == caster.owner or card.is_avatar
                or card.type != "SUMMON" or not card.face_up):
            raise GameError("err.skill_invalid_target")

    def execute(self, game, caster, target):
        card = game.board[(int(target["x"]), int(target["y"]))]
        game.skill_damage(card, self.damage, credit=caster.owner, source=caster)


@register("teleport")
class Teleport:
    """Custo 2. Permite MOVEMENT duas vezes seguidas, sem ATTACK."""

    def validate(self, game, caster, target):
        return None

    def execute(self, game, caster, target):
        caster.teleport = True
        caster.moves_allowed = 2
        game.emit("teleport_ready", player=caster.owner, uid=caster.uid)


@register("explosion")
class Explosion:
    """Custo 3. 3 de dano em todas as cartas face_up nas 8 casas ao redor (inclui cartas
    próprias e Avatares, não a própria conjuradora; D-16). Avatar perde LIFE."""
    damage = 3

    def validate(self, game, caster, target):
        return None

    def execute(self, game, caster, target):
        hit = []
        for dx, dy in NEIGHBORS_8:
            card = game.board.get((caster.x + dx, caster.y + dy))
            if card is not None and card.face_up:
                hit.append(card)
        for card in hit:
            if card.is_avatar:
                game.damage_life(card.owner, self.damage, reason="explosion")
            else:
                game.skill_damage(card, self.damage, credit=caster.owner, source=caster)
