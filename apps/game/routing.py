"""Rotas WebSocket."""
from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/lobby/<int:server_id>/", consumers.LobbyConsumer.as_asgi()),
    path("ws/sala/<int:room_id>/", consumers.RoomConsumer.as_asgi()),
    path("ws/admin/monitor/", consumers.MonitorConsumer.as_asgi()),
]
