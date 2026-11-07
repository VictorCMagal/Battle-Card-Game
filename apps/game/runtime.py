"""Estado em memória do servidor de jogo: salas e partidas ativas (P§19).

* `ROOMS` (RoomManager): salas e vínculo usuário->sala. Toda mutação ocorre no event loop do
  Channels (um processo Daphne); o RLock protege apenas a leitura feita por views HTTP.
* `GameSession`: uma partida em andamento. Contém o `Game` (motor puro), timers (X/O, turno,
  reconexão), projeção de estado por jogador e persistência final no MySQL.

Limitação documentada: o estado das partidas vive no processo; reiniciar o servidor encerra as
partidas em andamento (sem retomada). Para escalar horizontalmente seria necessário mover este
estado para um armazenamento compartilhado.
"""
import asyncio
import hashlib
import hmac
import logging
import os
import random
import threading
import time
from datetime import datetime, timezone as dt_timezone
from typing import Dict, List, Optional

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from apps.core import presence
from apps.core.errors import ServiceError
from engine import Game, GameError, public_events
from engine.constants import COIN_SECONDS, TURN_SECONDS, TURN_WARNING_SECONDS
from engine.initiative import draw_initiative, resolve_symbols

log = logging.getLogger("bcg.match")
ALLOWED_COMMANDS = {"walk_avatar", "summon", "double_cast", "move", "use_skill", "end_turn", "select"}
CMD_KEYS = {"type", "uid", "x", "y", "face_up", "slot", "target"}


# --------------------------------------------------------------------------- envio de mensagens
async def group_push(group: str, data: dict) -> None:
    """Envia `data` a todos os consumers do grupo (handler `push` dos consumers)."""
    layer = get_channel_layer()
    if layer is not None:
        await layer.group_send(group, {"type": "push", "data": data})


async def push_user(user_id: int, data: dict) -> None:
    await group_push(f"user_{user_id}", data)


# --------------------------------------------------------------------------- salas
class Room:
    """Sala de duelo. Slot A é o dono; B entra depois (nunca em sala debug)."""

    def __init__(self, room_id, server_id, name, mode, password, host):
        self.id, self.server_id, self.name, self.mode = room_id, server_id, name, mode
        self.salt = os.urandom(8).hex() if password else ""
        self.pw_hash = self._hash(password) if password else ""
        self.players: Dict[str, Optional[dict]] = {"A": host, "B": None}
        self.ready = {"A": False, "B": False}
        self.session: Optional["GameSession"] = None
        self.starting = False
        self.connected: Dict[int, int] = {}
        self.created = time.time()

    def _hash(self, password: str) -> str:
        return hashlib.sha256((self.salt + password).encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return not self.pw_hash or hmac.compare_digest(self.pw_hash, self._hash(password or ""))

    def slot_of(self, user_id: int) -> Optional[str]:
        for slot, p in self.players.items():
            if p and p["id"] == user_id:
                return slot
        return None

    @property
    def status(self) -> str:
        if self.session and self.session.active:
            return "BATTLE"
        return "READY" if self.players["B"] else "OPEN"

    def public(self) -> dict:
        names = [p["name"] for p in self.players.values() if p]
        return {"id": self.id, "name": self.name, "mode": self.mode, "status": self.status,
                "players": names, "has_password": bool(self.pw_hash),
                "joinable": self.mode == "versus" and self.status == "OPEN"}

    def state(self) -> dict:
        """Estado detalhado enviado aos ocupantes da sala."""
        return {**self.public(), "slots": {s: (p["name"] if p else None) for s, p in self.players.items()},
                "ready": dict(self.ready)}


class RoomManager:
    def __init__(self):
        self._rooms: Dict[int, Room] = {}
        self._by_user: Dict[int, int] = {}
        self._next = 1
        self._lock = threading.RLock()

    def get(self, room_id: int) -> Optional[Room]:
        return self._rooms.get(room_id)

    def room_of_user(self, user_id: int) -> Optional[Room]:
        rid = self._by_user.get(user_id)
        return self._rooms.get(rid) if rid else None

    def create(self, server_id, user: dict, name: str, mode: str, password: str) -> Room:
        with self._lock:
            if self.room_of_user(user["id"]):
                raise ServiceError("err.already_in_room")
            room = Room(self._next, server_id, name, mode, password, user)
            self._next += 1
            self._rooms[room.id] = room
            self._by_user[user["id"]] = room.id
            return room

    def join(self, room_id: int, user: dict, password: str) -> Room:
        with self._lock:
            if self.room_of_user(user["id"]):
                raise ServiceError("err.already_in_room")
            room = self._rooms.get(room_id)
            if room is None:
                raise ServiceError("err.room_not_found", 404)
            if room.mode == "debug" or room.status != "OPEN":
                raise ServiceError("err.room_not_joinable", 409)
            if not room.check_password(password):
                raise ServiceError("err.room_wrong_password", 403)
            room.players["B"] = user
            room.ready = {"A": False, "B": False}
            self._by_user[user["id"]] = room.id
            return room

    def leave(self, room: Room, user_id: int) -> Optional[Room]:
        """Remove o usuário. B vira A se A sair; sala vazia é removida (retorna None)."""
        with self._lock:
            slot = room.slot_of(user_id)
            if slot is None:
                return room
            self._by_user.pop(user_id, None)
            room.players[slot] = None
            room.ready = {"A": False, "B": False}
            if slot == "A" and room.players["B"]:
                room.players["A"], room.players["B"] = room.players["B"], None
            if not any(room.players.values()):
                self._rooms.pop(room.id, None)
                return None
            return room

    def list_public(self, server_id=None) -> List[dict]:
        with self._lock:
            return [r.public() for r in sorted(self._rooms.values(), key=lambda r: r.id)
                    if server_id in (None, r.server_id)]

    def all_rooms(self) -> List[Room]:
        with self._lock:
            return list(self._rooms.values())


ROOMS = RoomManager()


# --------------------------------------------------------------------------- carga e persistência (síncronas)
def load_match_data(room: Room) -> dict:
    """Carrega decks dos jogadores, catálogo e combinações (executa em thread de banco)."""
    from apps.accounts.models import Conta
    from apps.cards.services import load_catalog, load_combos
    from apps.decks.services import build_battle_deck
    decks = {}
    for slot in ("A", "B"):
        src = room.players["A"] if room.mode == "debug" else room.players[slot]
        decks[slot] = build_battle_deck(Conta.objects.get(id=src["id"]))
    return {"decks": decks, "catalog": load_catalog(), "combos": load_combos()}


def persist_match(session: "GameSession") -> int:
    """Grava histórico e aplica recompensas (executa em thread de banco). Retorna o id."""
    from django.db import transaction
    from django.db.models import F
    from django.utils import timezone

    from apps.accounts.models import Conta
    from .models import HistoricoEvento, HistoricoPartida

    result = session.game.result or {}
    with transaction.atomic():
        h = HistoricoPartida.objects.create(
            servidor_id=session.room.server_id, modo=session.mode,
            jogador_a_id=session.users["A"]["id"], jogador_b_id=session.users["B"]["id"],
            iniciada_em=session.started_at, finalizada_em=timezone.now(),
            resultado=result.get("type", "aborted"), vencedor=result.get("winner") or "",
            motivo=result.get("reason", ""), turnos=session.game.turn)
        HistoricoEvento.objects.bulk_create([
            HistoricoEvento(partida=h, seq=ev["seq"], turno=ev.get("turn", 0), jogador=ev.get("player") or "",
                            tipo=ev["type"], payload={k: v for k, v in ev.items()
                                                      if k not in ("seq", "turn", "type", "player")})
            for ev in session.game.events], batch_size=500)
        if session.mode != "debug":
            for slot, r in session.rewards.items():
                Conta.objects.filter(id=session.users[slot]["id"]).update(
                    cur_battlepoints=F("cur_battlepoints") + r["battlepoints"],
                    cur_magicdust=F("cur_magicdust") + r["magicdust"],
                    victory_counts=F("victory_counts") + r["victories"])
        return h.id


# --------------------------------------------------------------------------- partida
class GameSession:
    """Uma partida em andamento. Todas as ações do jogador passam por `handle_*` (autoritativo)."""
    ACTIVE = ("COIN", "COIN_RESULT", "PLAYING")

    def __init__(self, room: Room, data: dict):
        from .rewards import compute_rewards  # noqa: F401 (importação antecipada)
        self.room = room
        self.mode = room.mode
        self.users = {"A": room.players["A"], "B": room.players["A"] if room.mode == "debug" else room.players["B"]}
        self.rng = random.SystemRandom()
        self.game = Game(data["catalog"], mode=self.mode, rng=self.rng, combos=data["combos"])
        # uids únicos por jogador (no debug os dois decks vêm do mesmo usuário)
        self.game.setup(*[[{**c, "uid": f"{s}-{c['uid']}"} for c in data["decks"][s]] for s in ("A", "B")])
        self.phase = "COIN"
        self.choices = {"A": None, "B": None}
        self.symbols: Optional[dict] = None
        self.deadline = 0.0
        self.rewards = {"A": {"battlepoints": 0, "magicdust": 0, "victories": 0},
                        "B": {"battlepoints": 0, "magicdust": 0, "victories": 0}}
        self.started_at = datetime.now(dt_timezone.utc)
        self.disconnected: Dict[int, asyncio.Task] = {}
        self._tasks: List[asyncio.Task] = []
        self._timer: Optional[asyncio.Task] = None
        self._sent = 0
        self.match_db_id = None
        presence.STATS["matches_total"] += 1

    @property
    def active(self) -> bool:
        return self.phase in self.ACTIVE

    def slots_of(self, user_id: int) -> List[str]:
        return [s for s in ("A", "B") if self.users[s]["id"] == user_id]

    def _user_ids(self) -> List[int]:
        return sorted({u["id"] for u in self.users.values()})

    # --- início -------------------------------------------------------------------------
    async def start(self) -> None:
        """Debug pula a escolha X/O; 1x1 abre a janela de 10 s (O§3.1)."""
        log.info("match start room=%s mode=%s", self.room.id, self.mode)
        if self.mode == "debug":
            self.symbols = {"A": "X", "B": "O"}
            await self._announce_initiative()
            return
        self.deadline = time.time() + COIN_SECONDS
        await self._push_coin()
        self._spawn(self._coin_timeout())

    def _spawn(self, coro) -> asyncio.Task:
        task = asyncio.ensure_future(coro)
        self._tasks.append(task)
        return task

    async def _coin_timeout(self):
        await asyncio.sleep(COIN_SECONDS)
        if self.phase == "COIN":
            await self._resolve_coin()

    async def choose_symbol(self, user_id: int, symbol: str) -> None:
        if self.phase != "COIN":
            raise GameError("err.wrong_phase")
        slot = self.slots_of(user_id)[0]
        if symbol not in ("X", "O"):
            raise GameError("err.invalid_symbol")
        if self.choices[slot] is not None:
            raise GameError("err.symbol_already_chosen")   # só pode ser escolhida uma vez
        if symbol in self.choices.values():
            raise GameError("err.symbol_taken")
        self.choices[slot] = symbol
        await self._push_coin()
        if all(self.choices.values()):
            await self._resolve_coin()

    async def _resolve_coin(self):
        if self.phase != "COIN":
            return
        a, b = resolve_symbols(self.choices["A"], self.choices["B"], self.rng)
        self.symbols = {"A": a, "B": b}
        await self._announce_initiative()

    async def _announce_initiative(self):
        sym, first = draw_initiative(self.symbols["A"], self.symbols["B"], self.rng)
        self.phase = "COIN_RESULT"
        await self._broadcast({"type": "coin_result", "symbols": self.symbols, "initiative": sym, "first": first})
        self._spawn(self._begin_after_delay(first))

    async def _begin_after_delay(self, first):
        await asyncio.sleep(0 if self.mode == "debug" else 3)
        if self.phase != "COIN_RESULT":
            return
        self.game.start(first)
        self.phase = "PLAYING"
        await self._after_events()

    # --- comandos ---------------------------------------------------------------------
    async def handle_command(self, user_id: int, raw: dict) -> None:
        if self.phase != "PLAYING":
            raise GameError("err.wrong_phase")
        cmd = {k: v for k, v in (raw or {}).items() if k in CMD_KEYS}
        if cmd.get("type") not in ALLOWED_COMMANDS:
            raise GameError("err.unknown_command")
        slots = self.slots_of(user_id)
        if self.mode == "debug":
            cmd["player"] = self.game.current
        else:
            cmd["player"] = slots[0]
        self.game.apply(cmd)
        await self._after_events()

    async def _after_events(self):
        """Empurra estado/eventos novos, reinicia o timer se o turno mudou e trata o fim."""
        new = self.game.events[self._sent:]
        self._sent = len(self.game.events)
        turn_changed = any(e["type"] in ("turn_start",) for e in new)
        if self.game.result:
            await self._finish(new)
            return
        if turn_changed or self._timer is None:
            self._arm_timer()
        await self._push_state(new)

    def _arm_timer(self):
        if self._timer:
            self._timer.cancel()
        self.deadline = time.time() + TURN_SECONDS
        self._timer = self._spawn(self._turn_timeout(self.game.turn))

    async def _turn_timeout(self, turn: int):
        try:
            await asyncio.sleep(TURN_SECONDS)
        except asyncio.CancelledError:
            return
        if self.phase == "PLAYING" and self.game.turn == turn:
            self.game.expire_turn()
            await self._after_events()

    # --- envio -------------------------------------------------------------------------
    def _state_payload(self, user_id: int, events: list) -> dict:
        debug = self.mode == "debug"
        viewer = self.game.current if debug else self.slots_of(user_id)[0]
        return {"type": "match_state", "view": self.game.view_for(viewer, reveal_all=debug),
                "events": public_events(events, viewer, reveal_all=debug), "deadline": self.deadline,
                "server_time": time.time(), "turn_seconds": TURN_SECONDS, "warning_seconds": TURN_WARNING_SECONDS,
                "symbols": self.symbols, "users": {s: u["name"] for s, u in self.users.items()}}

    async def _push_state(self, events: list):
        for uid in self._user_ids():
            await push_user(uid, self._state_payload(uid, events))

    async def _push_coin(self):
        for uid in self._user_ids():
            slot = self.slots_of(uid)[0]
            await push_user(uid, {"type": "coin_state", "deadline": self.deadline, "server_time": time.time(),
                                  "you": slot, "your_choice": self.choices[slot],
                                  "taken": [c for c in self.choices.values() if c],
                                  "chosen": {s: bool(c) for s, c in self.choices.items()}})

    async def _broadcast(self, data: dict):
        for uid in self._user_ids():
            await push_user(uid, data)

    async def snapshot_for(self, user_id: int):
        """Reenvia o estado atual a um jogador que (re)conectou."""
        if self.phase == "COIN":
            await self._push_coin()
        elif self.phase == "PLAYING":
            await push_user(user_id, self._state_payload(user_id, []))
        elif self.phase == "COIN_RESULT":
            await push_user(user_id, {"type": "coin_result", "symbols": self.symbols})

    # --- fim ---------------------------------------------------------------------------
    async def _finish(self, new_events: Optional[list] = None):
        from .rewards import compute_rewards
        if self.phase == "FINISHED":
            return
        self.phase = "FINISHED"
        for t in self._tasks + list(self.disconnected.values()):
            if t is not asyncio.current_task():
                t.cancel()
        self.rewards = compute_rewards(self.game.result, self.mode, self.game.stats)
        if new_events:
            await self._push_state(new_events)
        try:
            self.match_db_id = await database_sync_to_async(persist_match)(self)
        except Exception:  # noqa: BLE001
            log.exception("falha ao persistir partida da sala %s", self.room.id)
        log.info("match end room=%s result=%s", self.room.id, self.game.result)
        await self._broadcast({"type": "match_end", "result": self.game.result, "rewards": self.rewards,
                               "users": {s: u["name"] for s, u in self.users.items()}, "history_id": self.match_db_id})
        self.room.session = None
        self.room.ready = {"A": False, "B": False}
        await group_push(f"room_{self.room.id}", {"type": "room_state", "room": self.room.state()})
        await group_push(f"lobby_{self.room.server_id}", {"type": "rooms", "rooms": ROOMS.list_public(self.room.server_id)})

    async def forfeit_user(self, user_id: int, reason: str):
        """Abandono/desconexão expirada: o usuário perde (D-21, D-23)."""
        if not self.active:
            return
        slots = self.slots_of(user_id)
        if self.phase != "PLAYING":   # ainda na fase X/O: partida cancelada, sem pontos
            self.game.result = {"type": "aborted", "winner": None, "loser": None, "reason": reason}
            await self._finish()
            return
        self.game.forfeit(slots[0], reason)
        await self._after_events()

    # --- conexão ------------------------------------------------------------------------
    async def player_disconnected(self, user_id: int):
        if user_id in self.disconnected or not self.active:
            return
        from django.conf import settings as dj
        await self._broadcast({"type": "opponent_status", "connected": False, "seconds": dj.RECONNECT_SECONDS,
                               "user_id": user_id})
        self.disconnected[user_id] = asyncio.ensure_future(self._reconnect_timeout(user_id, dj.RECONNECT_SECONDS))

    async def _reconnect_timeout(self, user_id: int, seconds: int):
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            return
        if self.active and user_id in self.disconnected:
            await self.forfeit_user(user_id, "disconnect")

    async def player_reconnected(self, user_id: int):
        task = self.disconnected.pop(user_id, None)
        if task:
            task.cancel()
            await self._broadcast({"type": "opponent_status", "connected": True, "user_id": user_id})
        await self.snapshot_for(user_id)


# --------------------------------------------------------------------------- monitoramento
def monitor_snapshot() -> dict:
    from apps.core.logbuffer import RECENT
    rooms = ROOMS.all_rooms()
    return {
        "uptime": int(time.time() - presence.STATS["started"]),
        "users_online": presence.count(), "users": presence.online_users(),
        "ws_connections": presence.STATS["ws_connections"], "ws_total": presence.STATS["ws_total"],
        "matches_total": presence.STATS["matches_total"],
        "rooms": [r.state() for r in rooms],
        "matches": [{"room": r.id, "mode": r.mode, "phase": r.session.phase, "turn": r.session.game.turn,
                     "players": [u["name"] for u in {u["id"]: u for u in r.session.users.values()}.values()]}
                    for r in rooms if r.session],
        "errors": list(RECENT)[-20:],
    }
