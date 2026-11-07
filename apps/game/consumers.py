"""Consumers WebSocket: lobby (chat, salas, presença, convites), sala/partida e monitor."""
import asyncio
import logging
import re

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from apps.chat import services as chat
from apps.core import presence, ratelimit
from apps.core.errors import ServiceError
from apps.core.i18n import t
from engine import GameError

from .runtime import ROOMS, GameSession, group_push, load_match_data, monitor_snapshot, push_user

log = logging.getLogger("bcg.ws")
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


class BaseConsumer(AsyncJsonWebsocketConsumer):
    """Base: tamanho/taxa de mensagens, tratamento de erros e handlers de grupo."""
    registered = False

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if text_data is None or len(text_data) > 8192:   # limite de tamanho (P§8)
            await self.close(code=1009)
            return
        if not ratelimit.allow(f"ws:{self.channel_name}", 40, 5.0):
            await self.send_json({"type": "error", "code": "err.rate_limited", "message": t("err.rate_limited")})
            return
        await super().receive(text_data=text_data, bytes_data=bytes_data, **kwargs)

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            return
        try:
            await self.dispatch_message(content)
        except (ServiceError, GameError) as e:
            await self.send_json({"type": "error", "code": e.code, "message": t(e.code, **getattr(e, "params", {}))})
        except Exception:  # noqa: BLE001
            log.exception("erro no consumer %s", type(self).__name__)
            await self.send_json({"type": "error", "code": "err.internal", "message": t("err.internal")})

    async def dispatch_message(self, content):  # pragma: no cover - sobrescrito
        raise NotImplementedError

    # handlers de mensagens de grupo (type "push" / "force.close")
    async def push(self, event):
        await self.send_json(event["data"])

    async def force_close(self, event):
        await self.close(code=4000)

    async def reject(self, code):
        await self.close(code=code)


def clean_name(text: str, max_len: int) -> str:
    text = _CTRL.sub(" ", str(text or "")).strip()
    if not text or len(text) > max_len:
        raise ServiceError("err.room_name")
    return text


@database_sync_to_async
def server_exists(server_id: int) -> bool:
    from apps.core.models import Servidor
    return Servidor.objects.filter(id=server_id, active=True).exists()


@database_sync_to_async
def validate_deck_ready(user_id: int) -> None:
    from apps.accounts.models import Conta
    from apps.decks.services import build_battle_deck
    build_battle_deck(Conta.objects.get(id=user_id))


@database_sync_to_async
def save_chat(canal, user, text):
    return chat.save_message(canal, user, text)


async def rooms_changed(server_id: int):
    await group_push(f"lobby_{server_id}", {"type": "rooms", "rooms": ROOMS.list_public(server_id)})


async def do_leave(room, user_id: int):
    """Sai da sala (abandono se houver partida) e avisa sala e lobby."""
    if room.session and room.session.active:
        await room.session.forfeit_user(user_id, "abandon")
    remaining = ROOMS.leave(room, user_id)
    if remaining:
        await group_push(f"room_{room.id}", {"type": "room_state", "room": remaining.state()})
    await rooms_changed(room.server_id)


# ------------------------------------------------------------------------------------- lobby
class LobbyConsumer(BaseConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.reject(4401)
        self.server_id = int(self.scope["url_route"]["kwargs"]["server_id"])
        if not await server_exists(self.server_id):
            return await self.reject(4404)
        self.uid, self.uname, self.user = user.id, user.name, user
        await self.accept()
        for g in (f"lobby_{self.server_id}", f"user_{self.uid}"):
            await self.channel_layer.group_add(g, self.channel_name)
        presence.add(self.uid, self.uname, self.server_id, self.channel_name)
        self.registered = True
        room = ROOMS.room_of_user(self.uid)
        await self.send_json({"type": "lobby_state", "you": self.uname, "room_id": room.id if room else None,
                              "users": presence.online_users(self.server_id),
                              "rooms": ROOMS.list_public(self.server_id)})
        await group_push(f"lobby_{self.server_id}", {"type": "users", "users": presence.online_users(self.server_id)})

    async def disconnect(self, code):
        if not self.registered:
            return
        await self.channel_layer.group_discard(f"lobby_{self.server_id}", self.channel_name)
        await self.channel_layer.group_discard(f"user_{self.uid}", self.channel_name)
        presence.remove(self.uid, self.channel_name)
        await group_push(f"lobby_{self.server_id}", {"type": "users", "users": presence.online_users(self.server_id)})

    async def dispatch_message(self, c):
        kind = c.get("type")
        me = {"id": self.uid, "name": self.uname}
        if kind == "chat":
            text = chat.clean_text(c.get("text"))
            chat.check_rate(self.uid)
            await save_chat(f"lobby:{self.server_id}", self.user, text)
            await group_push(f"lobby_{self.server_id}", {"type": "chat", "scope": "lobby", "from": self.uname,
                                                         "text": text, "time": chat.time_now()})
        elif kind == "private_chat":
            text = chat.clean_text(c.get("text"))
            chat.check_rate(self.uid)
            target = presence.find_by_name(str(c.get("to", "")))
            if not target or target[0] == self.uid:
                raise ServiceError("err.user_offline")
            await save_chat(f"priv:{min(self.uid, target[0])}-{max(self.uid, target[0])}", self.user, text)
            msg = {"type": "chat", "scope": "private", "from": self.uname, "to": target[1],
                   "text": text, "time": chat.time_now()}
            await push_user(target[0], msg)
            await push_user(self.uid, msg)
        elif kind == "create_room":
            name = clean_name(c.get("name"), 24)
            mode = c.get("mode") if c.get("mode") in ("versus", "debug") else "versus"
            pw = str(c.get("password") or "")[:16]
            room = ROOMS.create(self.server_id, me, name, mode, pw)
            await self.send_json({"type": "room_joined", "room_id": room.id})
            await rooms_changed(self.server_id)
        elif kind == "join_room":
            room = ROOMS.join(int(c.get("room_id", 0)), me, str(c.get("password") or ""))
            await group_push(f"room_{room.id}", {"type": "room_state", "room": room.state()})
            await self.send_json({"type": "room_joined", "room_id": room.id})
            await rooms_changed(self.server_id)
        elif kind == "find_room":
            room = ROOMS.get(int(c.get("room_id", 0) or 0))
            await self.send_json({"type": "room_found", "room": room.public() if room else None})
        elif kind == "invite":
            room = ROOMS.room_of_user(self.uid)
            target = presence.find_by_name(str(c.get("to", "")))
            if not room or not room.public()["joinable"]:
                raise ServiceError("err.invite_no_room")
            if not target or target[0] == self.uid:
                raise ServiceError("err.user_offline")
            await push_user(target[0], {"type": "invite", "from": self.uname, "room_id": room.id,
                                        "has_password": room.public()["has_password"]})
            await self.send_json({"type": "notify", "key": "notify.invite_sent", "text": t("notify.invite_sent")})
        elif kind == "ping":
            await self.send_json({"type": "pong"})


# ------------------------------------------------------------------------------------- sala
class RoomConsumer(BaseConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.reject(4401)
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        room = ROOMS.get(self.room_id)
        if room is None or room.slot_of(user.id) is None:
            return await self.reject(4403)
        self.uid, self.uname, self.user = user.id, user.name, user
        await self.accept()
        for g in (f"room_{self.room_id}", f"user_{self.uid}"):
            await self.channel_layer.group_add(g, self.channel_name)
        presence.add(self.uid, self.uname, room.server_id, self.channel_name)
        self.registered = True
        room.connected[self.uid] = room.connected.get(self.uid, 0) + 1
        await self.send_json({"type": "room_state", "room": room.state(), "you": self.uname,
                              "slot": room.slot_of(self.uid)})
        if room.session and room.session.active:
            await room.session.player_reconnected(self.uid)
        await group_push(f"room_{self.room_id}", {"type": "room_state", "room": room.state()})

    async def disconnect(self, code):
        if not self.registered:
            return
        await self.channel_layer.group_discard(f"room_{self.room_id}", self.channel_name)
        await self.channel_layer.group_discard(f"user_{self.uid}", self.channel_name)
        presence.remove(self.uid, self.channel_name)
        room = ROOMS.get(self.room_id)
        if room is None:
            return
        room.connected[self.uid] = max(0, room.connected.get(self.uid, 1) - 1)
        if room.connected[self.uid] == 0 and room.slot_of(self.uid):
            if room.session and room.session.active:
                await room.session.player_disconnected(self.uid)
            else:
                asyncio.ensure_future(self._idle_leave())

    async def _idle_leave(self):
        """Sala sem conexão do jogador por ROOM_IDLE_SECONDS: ele sai (a sala nunca fica vazia)."""
        await asyncio.sleep(settings.ROOM_IDLE_SECONDS)
        room = ROOMS.get(self.room_id)
        if (room and room.slot_of(self.uid) and room.connected.get(self.uid, 0) == 0
                and not (room.session and room.session.active)):
            await do_leave(room, self.uid)

    async def dispatch_message(self, c):
        room = ROOMS.get(self.room_id)
        if room is None or room.slot_of(self.uid) is None:
            await self.send_json({"type": "left"})
            return await self.close()
        kind = c.get("type")
        if kind == "chat":
            text = chat.clean_text(c.get("text"))
            chat.check_rate(self.uid)
            await save_chat(f"sala:{room.id}", self.user, text)
            await group_push(f"room_{room.id}", {"type": "chat", "scope": "room", "from": self.uname,
                                                 "text": text, "time": chat.time_now()})
        elif kind == "ready":
            await self._ready(room, bool(c.get("value", True)))
        elif kind == "leave":
            await do_leave(room, self.uid)
            await self.send_json({"type": "left"})
            await self.close()
        elif kind == "coin":
            if not room.session:
                raise GameError("err.wrong_phase")
            await room.session.choose_symbol(self.uid, str(c.get("symbol")))
        elif kind == "cmd":
            if not room.session:
                raise GameError("err.wrong_phase")
            await room.session.handle_command(self.uid, c.get("cmd") or {})
        elif kind == "sync":
            await self.send_json({"type": "room_state", "room": room.state(), "you": self.uname,
                                  "slot": room.slot_of(self.uid)})
            if room.session:
                await room.session.snapshot_for(self.uid)

    async def _ready(self, room, value: bool):
        if room.session and room.session.active:
            raise ServiceError("err.match_in_progress")
        slot = room.slot_of(self.uid)
        if room.mode == "debug" and slot != "A":
            raise ServiceError("err.room_not_joinable")
        if value:
            await validate_deck_ready(self.uid)   # exige deck selecionado com 40 cartas (D-05)
        room.ready[slot] = value
        await group_push(f"room_{room.id}", {"type": "room_state", "room": room.state()})
        both = room.ready["A"] and (room.mode == "debug" or room.ready["B"])
        present = all(room.connected.get(p["id"], 0) > 0 for p in room.players.values() if p)
        if both and present and not room.starting and not room.session:
            await self._start_match(room)

    async def _start_match(self, room):
        room.starting = True
        try:
            data = await database_sync_to_async(load_match_data)(room)
            room.session = GameSession(room, data)
            await group_push(f"room_{room.id}", {"type": "room_state", "room": room.state()})
            await rooms_changed(room.server_id)
            await room.session.start()
        except ServiceError as e:
            room.ready = {"A": False, "B": False}
            await group_push(f"room_{room.id}", {"type": "error", "code": e.code, "message": t(e.code, **e.params)})
            await group_push(f"room_{room.id}", {"type": "room_state", "room": room.state()})
        finally:
            room.starting = False


# ------------------------------------------------------------------------------------- monitor
class MonitorConsumer(BaseConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated or not user.is_staff:
            return await self.reject(4403)
        await self.accept()
        self.task = asyncio.ensure_future(self._loop())

    async def _loop(self):
        try:
            while True:
                await self.send_json({"type": "snapshot", **monitor_snapshot()})
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            return

    async def disconnect(self, code):
        task = getattr(self, "task", None)
        if task:
            task.cancel()

    async def dispatch_message(self, content):
        return None
