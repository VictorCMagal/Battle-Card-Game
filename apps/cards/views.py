from django.views.decorators.http import require_GET
from django.http import JsonResponse

from apps.core.http import api

from . import services


@require_GET
@api
def catalog(request):
    """GET /api/cartas/ -> catálogo completo (usado pelo editor de decks e pela arena)."""
    return JsonResponse({"ok": True, "cards": [services.def_to_payload(d) for d in services.load_catalog().values()]})
