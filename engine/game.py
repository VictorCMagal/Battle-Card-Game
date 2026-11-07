"""Motor da partida (servidor autoritativo).

Python puro: não conhece Django, banco, WebSocket nem interface (P§7). Recebe comandos
(dicts) em `Game.apply` e devolve a lista de eventos gerados. Qualquer violação de regra
levanta `GameError` sem alterar o estado (todas as validações ocorrem antes das mutações).

Fluxo de um turno: START (efeitos + compra + DECK BURN) -> ACTION (comandos) -> ENDING
(meditação, troca de jogador). O timer de 45 s é controlado pela camada de serviço, que
chama `expire_turn()`.

Interpretações aprovadas (docs/decisoes.md): D-09 a D-19.
"""
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import skills as skills_mod
from .cards import CardDef, CardInstance, make_avatar
from .combos import Combo, ComboTable
from .constants import (AFK_LIMIT, AVATAR_START, BOARD_H, BOARD_W, COUNTER_USES_EFFECTIVE_POWER,
                        DOUBLE_CAST_COST, HAND_MAX, HAND_START, LIFE_START, MANA_MAX, MANA_MIN,
                        MANA_START)
from .errors import GameError

NEIGHBORS_4 = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # N, S, O, L
NEIGHBORS_8 = NEIGHBORS_4 + [(1, -1), (1, 1), (-1, 1), (-1, -1)]


def other(slot: str) -> str:
    """Retorna o slot do adversário."""
    return "B" if slot == "A" else "A"


@dataclass
class PlayerState:
    """Variáveis de cada jogador na partida (O§3.1)."""
    slot: str
    avatar: CardInstance
    deck: List[CardInstance] = field(default_factory=list)   # Deck_da_Batalha
    hand: List[CardInstance] = field(default_factory=list)   # PLAYER_HANDS
    discard: List[CardInstance] = field(default_factory=list)  # DISCARD_PILE (pública)
    life: int = LIFE_START
    mana: int = MANA_START
    selection: Optional[str] = None
    afk_count: int = 0


class Game:
    """Estado e regras de uma partida 1x1 (ou debug)."""

    def __init__(self, catalog: Dict[int, CardDef], mode: str = "versus", rng=None,
                 combos: Optional[ComboTable] = None):
        self.catalog = catalog
        self.mode = mode
        self.rng = rng or random.SystemRandom()
        self.combos = combos or ComboTable()
        self.players: Dict[str, PlayerState] = {}
        self.board: Dict[Tuple[int, int], CardInstance] = {}
        self.turn = 0
        self.current: Optional[str] = None
        self.phase = "SETUP"
        self.result: Optional[dict] = None
        self.events: List[dict] = []
        self.stats = {"A": {"destroyed": 0}, "B": {"destroyed": 0}}
        # flags do turno atual
        self.summons_done = 0
        self.summon_cap = 1
        self.double_cast_used = False
        self.walked = False
        self.actions_this_turn = 0
        self._handlers = {
            "walk_avatar": self._cmd_walk, "summon": self._cmd_summon,
            "double_cast": self._cmd_double_cast, "move": self._cmd_move,
            "use_skill": self._cmd_skill, "end_turn": self._cmd_end_turn,
            "select": self._cmd_select,
        }

    # ------------------------------------------------------------------ utilidades
    def emit(self, type_: str, secret: Optional[dict] = None, **data) -> dict:
        """Registra um evento. `secret` guarda dados ocultos ao adversário."""
        ev = {"seq": len(self.events) + 1, "turn": self.turn, "type": type_, **data}
        if secret:
            ev["secret"] = secret
        self.events.append(ev)
        return ev

    @staticmethod
    def in_board(x: int, y: int) -> bool:
        return 0 <= x < BOARD_W and 0 <= y < BOARD_H

    def _is_discarded(self, card: CardInstance) -> bool:
        return any(c is card for c in self.players[card.owner].discard)

    def _on_board(self, card: CardInstance) -> bool:
        return self.board.get((card.x, card.y)) is card

    def find_board_card(self, uid: str) -> Optional[CardInstance]:
        for card in self.board.values():
            if card.uid == uid:
                return card
        return None

    def _find_hand(self, slot: str, uid: str) -> Optional[CardInstance]:
        for card in self.players[slot].hand:
            if card.uid == uid:
                return card
        return None

    def spawn(self, slot: str, card_id: int, x: int, y: int, face_up: bool = True,
              uid: Optional[str] = None, paid: bool = True) -> CardInstance:
        """Coloca uma carta diretamente na arena (usado por testes e ferramentas de debug)."""
        defn = self.catalog[card_id]
        card = CardInstance(uid=uid or uuid.uuid4().hex, owner=slot, card_id=card_id, defn=defn,
                            face_up=face_up, shield=defn.shield, mana_paid=paid, x=x, y=y,
                            summoned_turn=-1)
        card.power_bonus = defn.power_bonus
        card.attack_bonus = defn.attack_bonus
        self.board[(x, y)] = card
        return card

    # ------------------------------------------------------------------ preparação
    def setup(self, deck_a: List[dict], deck_b: List[dict]) -> None:
        """Copia os decks para o Deck_da_Batalha, embaralha, cria Avatares e distribui 5 cartas.

        Cada entrada do deck: {"uid", "card_id", "is_foil", "is_shiny"}.
        """
        for slot, deck in (("A", deck_a), ("B", deck_b)):
            cards = []
            for entry in deck:
                cid = int(entry["card_id"])
                if cid < 1 or cid not in self.catalog:
                    raise GameError("err.invalid_card", card_id=cid)
                defn = self.catalog[cid]
                inst = CardInstance(uid=str(entry.get("uid") or uuid.uuid4().hex), owner=slot,
                                    card_id=cid, defn=defn, shield=defn.shield,
                                    is_foil=bool(entry.get("is_foil")),
                                    is_shiny=bool(entry.get("is_shiny")))
                inst.power_bonus, inst.attack_bonus = defn.power_bonus, defn.attack_bonus
                cards.append(inst)
            self.rng.shuffle(cards)
            ax, ay = AVATAR_START[slot]
            avatar = make_avatar(slot, ax, ay)
            self.players[slot] = PlayerState(slot=slot, avatar=avatar, deck=cards)
            self.board[(ax, ay)] = avatar
        for slot in ("A", "B"):
            self._draw(slot, HAND_START)
        self.phase = "READY"

    def start(self, first_player: str) -> None:
        """Inicia o duelo: o vencedor da iniciativa começa o turno 1."""
        self.turn = 1
        self.current = first_player
        self.emit("match_start", first=first_player)
        self._begin_turn()

    # ------------------------------------------------------------------ cartas / zonas
    def _give(self, slot: str, card: CardInstance) -> None:
        """Entrega uma carta à mão; acima de HAND_MAX a carta é descartada."""
        pl = self.players[slot]
        if len(pl.hand) >= HAND_MAX:
            self._to_discard(card)
            self.emit("hand_overflow", player=slot, secret={"card_id": card.card_id})
            return
        card.reset_for_hand()
        pl.hand.append(card)
        self.emit("draw", player=slot, secret={"card_id": card.card_id, "uid": card.uid})

    def _draw(self, slot: str, n: int) -> int:
        pl = self.players[slot]
        drawn = 0
        while drawn < n and pl.deck:
            self._give(slot, pl.deck.pop(0))
            drawn += 1
        return drawn

    def _to_discard(self, card: CardInstance) -> None:
        """Move a carta para a DISCARD_PILE do dono (visível a todos)."""
        pl = self.players[card.owner]
        if self._on_board(card):
            del self.board[(card.x, card.y)]
        pl.hand = [c for c in pl.hand if c is not card]
        if pl.selection == card.uid:
            pl.selection = None
        card.reset_for_hand()
        card.face_up = True
        pl.discard.append(card)

    def discard(self, card: CardInstance, credit: Optional[str] = None, reason: str = "destroyed") -> None:
        """Descarta/destrói uma carta e registra o evento. `credit` ganha magicdust (+1)."""
        view = card.view(True)
        self._to_discard(card)
        if credit is not None:
            self.stats[credit]["destroyed"] += 1
        self.emit("card_destroyed", player=card.owner, card=view, reason=reason, credit=credit)

    def _move_card(self, card: CardInstance, x: int, y: int) -> None:
        if self._on_board(card):
            del self.board[(card.x, card.y)]
        card.x, card.y = x, y
        self.board[(x, y)] = card

    def damage_life(self, slot: str, amount: int, reason: str = "") -> None:
        """Reduz LIFE (o fim da partida é verificado ao final da ação)."""
        if amount <= 0:
            return
        self.players[slot].life -= amount
        self.emit("life_changed", player=slot, delta=-amount, life=self.players[slot].life, reason=reason)

    def _change_mana(self, slot: str, delta: int, reason: str = "") -> None:
        pl = self.players[slot]
        new = max(MANA_MIN, min(MANA_MAX, pl.mana + delta))
        if new != pl.mana:
            pl.mana = new
            self.emit("mana_changed", player=slot, delta=delta, mana=new, reason=reason)

    # ------------------------------------------------------------------ mana cost / flip
    def _pay_mana(self, card: CardInstance) -> bool:
        """MANA COST (O§3.3): cobrado uma vez por permanência na arena.
        Sem MANA suficiente: carta descartada e LIFE -= (custo - MANA); MANA vai a 0 (D-11)."""
        if card.mana_paid:
            return True
        cost, pl = card.mana_cost, self.players[card.owner]
        if cost <= 0:
            card.mana_paid = True
            return True
        if pl.mana >= cost:
            pl.mana -= cost
            card.mana_paid = True
            self.emit("mana_paid", player=card.owner, uid=card.uid, cost=cost, mana=pl.mana)
            return True
        shortfall = cost - pl.mana
        pl.mana = 0
        self.emit("mana_cost_failed", player=card.owner, uid=card.uid, cost=cost, shortfall=shortfall)
        self.damage_life(card.owner, shortfall, reason="mana_cost")
        self.discard(card, reason="mana_cost")
        return False

    def _flip_up(self, card: CardInstance) -> bool:
        """FLIP EFFECT: face_down -> face_up. Retorna False se a carta foi descartada pelo custo."""
        if card.face_up:
            return True
        card.face_up = True
        self.emit("flip", player=card.owner, card=card.view(True))
        self._trigger("on_flip", card)
        return self._pay_mana(card)

    def _trigger(self, name: str, *args) -> None:
        """Ponto de extensão para efeitos de cartas (placeholders no MVP)."""
        return None

    # ------------------------------------------------------------------ turnos
    def _begin_turn(self) -> None:
        """FASE START: efeitos de início, compra até 5 e DECK BURN."""
        self.phase = "START"
        slot = self.current
        pl = self.players[slot]
        self.summons_done, self.summon_cap = 0, 1
        self.double_cast_used = self.walked = False
        self.actions_this_turn = 0
        for card in self.board.values():
            if card.owner == slot:
                card.moves_used, card.moves_allowed = 0, 1
                card.skill_used = card.attacked = card.teleport = False
        self.emit("turn_start", player=slot, turn=self.turn)
        self._trigger("on_start_the_turn", slot)  # placeholder (O§3.3)
        need = HAND_START - len(pl.hand)
        if need > 0:
            drawn = self._draw(slot, need)
            missing = need - drawn
            if missing > 0:  # DECK BURN: 1 LIFE por carta que faltou (D-14)
                self.emit("deck_burn", player=slot, missing=missing)
                self.damage_life(slot, missing, reason="deck_burn")
        self.phase = "ACTION"
        self._check_end()

    def _end_turn(self) -> None:
        """FASE ENDING: MEDITATION, limpa seleção e passa a vez."""
        self.phase = "ENDING"
        slot = self.current
        if not self.walked:  # MEDITATION: +1 MANA se o Avatar não andou
            self._change_mana(slot, 1, reason="meditation")
        self.players[slot].selection = None
        self.emit("turn_end", player=slot)
        self.turn += 1
        self.current = other(slot)
        self._begin_turn()

    def expire_turn(self) -> List[dict]:
        """Chamado pelo serviço quando o timer de 45 s zera. Aplica a regra de AFK (D-13)."""
        if self.result:
            return []
        start = len(self.events)
        slot = self.current
        pl = self.players[slot]
        pl.afk_count = pl.afk_count + 1 if self.actions_this_turn == 0 else 0
        self.emit("turn_timeout", player=slot, afk_count=pl.afk_count)
        if pl.afk_count >= AFK_LIMIT and self.mode != "debug":
            self._set_result("win", winner=other(slot), reason="afk", loser=slot)
        else:
            self._end_turn()
            self._check_end()
        return self.events[start:]

    def forfeit(self, slot: str, reason: str = "abandon") -> List[dict]:
        """Jogador abandonou/ficou desconectado: perde sem Battlepoints (D-21, D-23)."""
        if self.result:
            return []
        start = len(self.events)
        self._set_result("win", winner=other(slot), reason=reason, loser=slot)
        return self.events[start:]

    def _set_result(self, kind: str, winner: Optional[str] = None, reason: str = "life",
                    loser: Optional[str] = None) -> None:
        self.result = {"type": kind, "winner": winner, "loser": loser, "reason": reason}
        self.phase = "FINISHED"
        self.emit("match_end", **self.result)

    def _check_end(self) -> None:
        """LIFE <= 0 encerra; ambos <= 0 na mesma ação = DRAW (O§3.1, D-19)."""
        if self.result:
            return
        a, b = self.players["A"].life, self.players["B"].life
        if a <= 0 and b <= 0:
            self._set_result("draw", reason="life")
        elif a <= 0:
            self._set_result("win", winner="B", loser="A", reason="life")
        elif b <= 0:
            self._set_result("win", winner="A", loser="B", reason="life")

    # ------------------------------------------------------------------ entrada de comandos
    def apply(self, cmd: dict) -> List[dict]:
        """Valida e aplica um comando. Retorna os eventos gerados.

        Comandos: walk_avatar{x,y}, summon{uid,x,y,face_up}, double_cast, move{uid,x,y},
        use_skill{uid,slot,target}, end_turn, select{uid|None}. Todos com `player`.
        """
        if self.result or self.phase == "FINISHED":
            raise GameError("err.match_finished")
        handler = self._handlers.get(cmd.get("type"))
        if handler is None:
            raise GameError("err.unknown_command")
        if cmd.get("player") not in ("A", "B"):
            raise GameError("err.invalid_player")
        start = len(self.events)
        handler(cmd["player"], cmd)
        self._check_end()
        if not self.result and cmd["type"] != "select" and self.phase == "ACTION" \
                and self._exhausted():
            self.emit("auto_end", player=self.current)
            self._end_turn()
            self._check_end()
        return self.events[start:]

    def _require_turn(self, player: str) -> PlayerState:
        if player != self.current:
            raise GameError("err.not_your_turn")
        if self.phase != "ACTION":
            raise GameError("err.wrong_phase")
        return self.players[player]

    def _note_action(self, player: str) -> None:
        self.actions_this_turn += 1
        self.players[player].afk_count = 0

    # ------------------------------------------------------------------ select / end turn
    def _cmd_select(self, player: str, cmd: dict) -> None:
        pl = self._require_turn(player)
        uid = cmd.get("uid")
        if uid is None:
            pl.selection = None
            self.emit("select", player=player, zone=None)
            return
        if self._find_hand(player, uid):
            zone = "hand"
        else:
            card = self.find_board_card(uid)
            if card is None or card.owner != player:
                raise GameError("err.invalid_selection")
            zone = "board"
        pl.selection = uid
        self.emit("select", player=player, zone=zone, uid=uid if zone == "board" else None,
                  secret={"uid": uid})

    def _cmd_end_turn(self, player: str, cmd: dict) -> None:
        self._require_turn(player)
        self._note_action(player)  # END TURN manual conta como ação (D-13)
        self._end_turn()

    # ------------------------------------------------------------------ WALKING_AVATAR
    def _cmd_walk(self, player: str, cmd: dict) -> None:
        pl = self._require_turn(player)
        if self.walked:
            raise GameError("err.already_walked")
        x, y = self._xy(cmd)
        av = pl.avatar
        if abs(av.x - x) + abs(av.y - y) != 1 or not self.in_board(x, y):
            raise GameError("err.invalid_tile")
        occ = self.board.get((x, y))
        if occ is not None and occ.owner != player:
            raise GameError("err.tile_occupied_enemy")
        if occ is not None:  # carta própria no destino é destruída (O§3.3)
            self.discard(occ, reason="avatar_walk")
        self._move_card(av, x, y)
        self.walked = True
        self._note_action(player)
        self.emit("avatar_moved", player=player, x=x, y=y)

    @staticmethod
    def _xy(cmd: dict) -> Tuple[int, int]:
        try:
            return int(cmd["x"]), int(cmd["y"])
        except (KeyError, TypeError, ValueError):
            raise GameError("err.invalid_tile")

    # ------------------------------------------------------------------ SUMMONING
    def summon_tiles(self, player: str) -> List[Tuple[int, int]]:
        """Blocos adjacentes e diagonais ao Avatar dentro da arena."""
        av = self.players[player].avatar
        return [(av.x + dx, av.y + dy) for dx, dy in NEIGHBORS_8 if self.in_board(av.x + dx, av.y + dy)]

    def _cmd_summon(self, player: str, cmd: dict) -> None:
        pl = self._require_turn(player)
        if self.summons_done >= self.summon_cap:
            raise GameError("err.summon_limit")
        card = self._find_hand(player, str(cmd.get("uid")))
        if card is None:
            raise GameError("err.card_not_in_hand")
        if card.type != "SUMMON":
            raise GameError("err.type_not_implemented", type=card.type)
        x, y = self._xy(cmd)
        if (x, y) not in self.summon_tiles(player):
            raise GameError("err.invalid_tile")
        face_up = bool(cmd.get("face_up", True))
        occ = self.board.get((x, y))
        enemy = other(player)
        if occ is not None and occ.is_avatar and occ.owner == enemy:
            if self.players[enemy].life > card.power:  # só como golpe final (D-09a)
                raise GameError("err.summon_on_avatar")
        # --- validações concluídas: a partir daqui o estado muda ---
        pl.hand = [c for c in pl.hand if c is not card]
        card.reset_for_hand()
        card.power_bonus, card.attack_bonus, card.shield = (card.defn.power_bonus,
                                                            card.defn.attack_bonus, card.defn.shield)
        self.summons_done += 1
        self._note_action(player)
        if occ is None:
            self._place_summon(card, x, y, face_up)
        elif occ.is_avatar:  # Avatar adversário: ataque direto, sempre face_up (D-09a)
            card.face_up = False
            if self._flip_up(card):
                self.emit("attack_avatar", player=player, uid=card.uid, x=x, y=y)
                self.damage_life(enemy, card.power + card.attack_bonus, reason="summon_attack")
                self.discard(card, reason="consumed")
        elif occ.owner == player:
            combo = self.combos.find(occ, card)
            if combo:
                self._apply_combo(combo, occ, card, from_hand=True)
            else:  # sem combinação: descarta a carta do bloco e a nova ocupa (D-09b)
                self.discard(occ, reason="replaced")
                self._place_summon(card, x, y, face_up)
        else:  # carta adversária: ATTACK (D-09c)
            res = self._attack_card(card, occ, origin=None)
            if res == "aborted_target":  # alvo descartado ao ser revelado: bloco livre
                self._place_summon(card, x, y, face_up)
            elif res == "done" and not self._is_discarded(card) and not self._on_board(card):
                self.discard(card, reason="attack_failed")  # sobreviveu sem destruir o alvo

    def _place_summon(self, card: CardInstance, x: int, y: int, face_up: bool) -> None:
        card.x, card.y = x, y
        card.summoned_turn = self.turn
        card.face_up = False
        self.board[(x, y)] = card
        self.emit("summoned", player=card.owner, uid=card.uid, x=x, y=y, face_up=face_up,
                  secret={"card_id": card.card_id})
        if face_up:
            self._flip_up(card)  # revela e cobra MANA COST

    def _cmd_double_cast(self, player: str, cmd: dict) -> None:
        pl = self._require_turn(player)
        if self.summons_done < 1:
            raise GameError("err.double_cast_needs_summon")
        if self.double_cast_used:
            raise GameError("err.double_cast_used")
        if pl.mana < DOUBLE_CAST_COST:
            raise GameError("err.not_enough_mana")
        pl.mana -= DOUBLE_CAST_COST
        self.double_cast_used = True
        self.summon_cap = 2
        self._note_action(player)
        self.emit("double_cast", player=player, mana=pl.mana)

    # ------------------------------------------------------------------ MOVEMENT / ATTACK / STACK
    def _cmd_move(self, player: str, cmd: dict) -> None:
        self._require_turn(player)
        card = self.find_board_card(str(cmd.get("uid")))
        if card is None or card.owner != player or card.is_avatar:
            raise GameError("err.invalid_card")
        if card.summoned_turn == self.turn:
            raise GameError("err.cooldown_summoned")  # Cooldown Effect
        if card.moves_used >= card.moves_allowed:
            raise GameError("err.already_moved")
        x, y = self._xy(cmd)
        if abs(card.x - x) + abs(card.y - y) != 1 or not self.in_board(x, y):
            raise GameError("err.invalid_tile")
        occ = self.board.get((x, y))
        enemy = other(player)
        if occ is not None and occ.owner == player and occ.is_avatar:
            raise GameError("err.tile_own_avatar")
        if occ is not None and occ.owner == enemy and card.teleport:
            raise GameError("err.teleport_no_attack")
        combo = None
        if occ is not None and occ.owner == player:  # STACK
            combo = self.combos.find(occ, card)
            if combo is None:
                raise GameError("err.no_combination")
        # --- mutações ---
        card.moves_used += 1
        self._note_action(player)
        if occ is None:
            self._move_card(card, x, y)
            self.emit("card_moved", player=player, uid=card.uid, x=x, y=y)
        elif occ.owner == player:
            self._apply_combo(combo, occ, card, from_hand=False)
        elif occ.is_avatar:
            card.attacked = True
            self.emit("attack_avatar", player=player, uid=card.uid, x=x, y=y)
            self.damage_life(enemy, max(0, card.effective_power) + card.attack_bonus, reason="attack")
        else:
            card.attacked = True
            self._attack_card(card, occ, origin=(card.x, card.y))

    def _apply_combo(self, combo: Combo, block: CardInstance, incoming: CardInstance,
                     from_hand: bool) -> None:
        """Aplica FUSÃO/COMBINAÇÃO. A carta que chega é consumida (vai ao descarte)."""
        self.emit("combo", player=incoming.owner, name=combo.name, block=block.uid)
        if combo.effect_type == "create_card":
            defn = self.catalog.get(int(combo.effect_value))
            if defn is None:
                raise GameError("err.invalid_card", card_id=combo.effect_value)
            bx, by, face_up, paid = block.x, block.y, block.face_up, block.mana_paid
            self.discard(block, reason="fusion")
            self.discard(incoming, reason="fusion")
            new = self.spawn(block.owner, defn.card_id, bx, by, face_up=face_up, paid=paid)
            new.summoned_turn = self.turn
            self.emit("card_created", player=block.owner, card=new.view(face_up), x=bx, y=by)
        else:
            if combo.effect_type == "power_delta":
                block.power_bonus += int(combo.effect_value)
            elif combo.effect_type == "shield_delta":
                block.shield += int(combo.effect_value)
            self.discard(incoming, reason="combined")

    def _attack_value(self, card: CardInstance) -> int:
        """Poder de ataque = Power efetivo (>= 0) + Attack_Bonus."""
        return max(0, card.effective_power) + card.attack_bonus

    def _apply_mana_gain(self, attacker: CardInstance, target: CardInstance) -> None:
        """MANA GAIN: soma os valores cujo elemento coincide com o do alvo (D-17)."""
        if attacker.is_avatar or not target.elements:
            return
        total = sum(g.value for g in attacker.defn.mana_gains if g.element in target.elements)
        if total:
            self._change_mana(attacker.owner, total, reason="mana_gain")

    def _attack_card(self, attacker: CardInstance, target: CardInstance, origin) -> str:
        """Combate entre cartas (Damage System, O§5).

        Retorna "done", "aborted_target" (alvo descartado ao ser revelado) ou
        "aborted_attacker" (atacante descartado ao ser revelado).
        `origin` é o bloco do atacante (None quando ele vem da mão).
        """
        tx, ty = target.x, target.y
        if not self._flip_up(target):
            return "aborted_target"
        if not self._flip_up(attacker):
            return "aborted_attacker"
        self.emit("attack", player=attacker.owner, uid=attacker.uid, target=target.uid, x=tx, y=ty)
        # Damage System (O§5): dano ao bloqueador e contra-ataque no atacante
        t_before, a_before = target.effective_power, attacker.effective_power
        dmg = max(0, self._attack_value(attacker) - target.shield)
        counter_src = t_before if COUNTER_USES_EFFECTIVE_POWER else target.power
        counter = max(0, counter_src - attacker.shield)
        target.damage += dmg
        attacker.damage += counter
        self.emit("damage", target=target.uid, amount=dmg, attacker=attacker.uid, counter=counter)
        self._apply_mana_gain(attacker, target)
        target_dead = target.effective_power <= 0
        attacker_dead = attacker.effective_power <= 0
        t_owner, a_owner = target.owner, attacker.owner
        if target_dead:  # excesso de dano atinge o LIFE do dono (D-10)
            self.discard(target, credit=a_owner, reason="attack")
            self.damage_life(t_owner, dmg - t_before, reason="excess")
        if attacker_dead:  # excesso do contra-ataque também atinge o LIFE do dono do atacante
            self.discard(attacker, credit=t_owner, reason="counter")
            self.damage_life(a_owner, counter - a_before, reason="excess")
        elif target_dead:  # atacante vencedor ocupa o bloco do alvo (D-10)
            self._move_card(attacker, tx, ty)
            if origin is None:
                attacker.summoned_turn = self.turn
            self.emit("attacker_occupies", player=a_owner, uid=attacker.uid, x=tx, y=ty)
        return "done"

    # ------------------------------------------------------------------ SKILLS
    def skill_damage(self, card: CardInstance, amount: int, credit: Optional[str], source=None) -> None:
        """Dano de skill: ignora Shield; excesso não atinge o LIFE (D-16)."""
        card.damage += amount
        self.emit("skill_damage", target=card.uid, amount=amount, x=card.x, y=card.y)
        if card.effective_power <= 0:
            self.discard(card, credit=credit, reason="skill")

    def _cmd_skill(self, player: str, cmd: dict) -> None:
        pl = self._require_turn(player)
        card = self.find_board_card(str(cmd.get("uid")))
        if card is None or card.owner != player or card.is_avatar:
            raise GameError("err.invalid_card")
        if not card.face_up:
            raise GameError("err.skill_face_down")
        if card.summoned_turn == self.turn:
            raise GameError("err.skill_summon_turn")
        if card.skill_used or card.moves_used > 0 or card.attacked:
            raise GameError("err.skill_not_available")
        try:
            slot = int(cmd.get("slot"))
        except (TypeError, ValueError):
            raise GameError("err.invalid_skill")
        skill = next((s for s in card.defn.skills if s.slot == slot), None)
        impl = skills_mod.SKILL_REGISTRY.get(skill.key) if skill else None
        if impl is None:
            raise GameError("err.invalid_skill")
        if pl.mana < skill.manacost:
            raise GameError("err.not_enough_mana")
        target = cmd.get("target") or {}
        impl.validate(self, card, target)
        pl.mana -= skill.manacost
        card.skill_used = True
        self._note_action(player)
        self.emit("skill_used", player=player, uid=card.uid, skill=skill.key, mana=pl.mana)
        impl.execute(self, card, target)

    # ------------------------------------------------------------------ auto END TURN
    def _exhausted(self) -> bool:
        """True quando o jogador esgotou todas as funções possíveis (O§3.3 ENDING)."""
        slot = self.current
        pl = self.players[slot]
        av = pl.avatar
        if not self.walked:
            for dx, dy in NEIGHBORS_4:
                x, y = av.x + dx, av.y + dy
                occ = self.board.get((x, y))
                if self.in_board(x, y) and (occ is None or occ.owner == slot):
                    return False
        if pl.hand and self.summons_done < self.summon_cap and self.summon_tiles(slot):
            return False
        if (pl.hand and self.summons_done >= 1 and not self.double_cast_used
                and pl.mana >= DOUBLE_CAST_COST):
            return False
        for card in list(self.board.values()):
            if card.owner != slot or card.is_avatar or card.summoned_turn == self.turn:
                continue
            if card.moves_used < card.moves_allowed:
                for dx, dy in NEIGHBORS_4:
                    x, y = card.x + dx, card.y + dy
                    occ = self.board.get((x, y))
                    if self.in_board(x, y) and not (occ and occ.is_avatar and occ.owner == slot):
                        return False
            if (card.face_up and not card.skill_used and card.moves_used == 0 and not card.attacked
                    and any(s.manacost <= pl.mana and s.key in skills_mod.SKILL_REGISTRY
                            for s in card.defn.skills)):
                return False
        return True

    # ------------------------------------------------------------------ projeção para o cliente
    def view_for(self, viewer: str, reveal_all: bool = False) -> dict:
        """Estado visível ao jogador `viewer`. Cartas ocultas do adversário não vazam (P§8.1).

        `reveal_all` (modo debug) expõe os dois lados ao mesmo usuário."""
        def sel(slot):
            pl = self.players[slot]
            if pl.selection is None:
                return None
            for i, c in enumerate(pl.hand):
                if c.uid == pl.selection:
                    return {"zone": "hand", "index": i, "uid": c.uid if (slot == viewer or reveal_all) else None}
            return {"zone": "board", "uid": pl.selection}

        players = {}
        for slot, pl in self.players.items():
            see = reveal_all or slot == viewer
            players[slot] = {
                "slot": slot, "life": pl.life, "mana": pl.mana, "deck_count": len(pl.deck),
                "hand_count": len(pl.hand), "afk_count": pl.afk_count,
                "hand": [c.view(True) for c in pl.hand] if see else [],
                "discard": [c.view(True) for c in pl.discard], "selection": sel(slot),
            }
        board = []
        for card in self.board.values():
            full = card.is_avatar or card.face_up or reveal_all or card.owner == viewer
            board.append(card.view(full))
        return {
            "mode": self.mode, "turn": self.turn, "current": self.current, "phase": self.phase,
            "result": self.result, "you": viewer, "summons_done": self.summons_done,
            "summon_cap": self.summon_cap, "walked": self.walked,
            "double_cast_used": self.double_cast_used, "players": players, "board": board,
        }


def public_events(events: List[dict], viewer: str, reveal_all: bool = False) -> List[dict]:
    """Remove dados secretos dos eventos que o `viewer` não pode ver."""
    out = []
    for ev in events:
        ev = dict(ev)
        if "secret" in ev and not (reveal_all or ev.get("player") == viewer):
            ev.pop("secret")
        out.append(ev)
    return out
