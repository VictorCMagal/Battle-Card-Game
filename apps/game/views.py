from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.core.http import api

from .runtime import ROOMS


@require_GET
@api
def rooms(request):
    """GET /api/salas/?server=ID -> snapshot das salas (a criação/entrada usa WebSocket)."""
    try:
        sid = int(request.GET.get("server", 0)) or None
    except ValueError:
        sid = None
    return JsonResponse({"ok": True, "rooms": ROOMS.list_public(sid)})
