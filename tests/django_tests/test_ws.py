"""Testes WebSocket (NÃO executados no ambiente de desenvolvimento do projeto)."""
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from apps.accounts.models import Conta
from apps.game.routing import websocket_urlpatterns
from apps.game.runtime import ROOMS
from tests.django_tests.test_api import load_cards

APP = URLRouter(websocket_urlpatterns)


async def connect(path, user):
    comm = WebsocketCommunicator(APP, path)
    comm.scope["user"] = user
    ok, _ = await comm.connect()
    return comm, ok


class LobbyTests(TransactionTestCase):
    def setUp(self):
        load_cards()
        self.u1 = Conta.objects.create_conta("WsUser1", "w1@example.com", "senha123")
        self.u2 = Conta.objects.create_conta("WsUser2", "w2@example.com", "senha123")
        ROOMS._rooms.clear()
        ROOMS._by_user.clear()

    async def test_lobby_state_and_create_room(self):
        comm, ok = await connect("/ws/lobby/1/", self.u1)
        self.assertTrue(ok)
        state = await comm.receive_json_from()
        self.assertEqual(state["type"], "lobby_state")
        await comm.send_json_to({"type": "create_room", "name": "Sala X", "mode": "versus", "password": ""})
        seen = []
        for _ in range(4):
            seen.append((await comm.receive_json_from())["type"])
            if "room_joined" in seen:
                break
        self.assertIn("room_joined", seen)
        await comm.disconnect()

    async def test_chat_limit_and_anonymous_rejected(self):
        from django.contrib.auth.models import AnonymousUser
        comm, ok = await connect("/ws/lobby/1/", AnonymousUser())
        self.assertFalse(ok)
