"""APIs do editor de decks e Grimorium (todas exigem login e só tocam nos dados do próprio dono)."""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.http import api, json_body, ok

from . import services


@require_http_methods(["GET", "POST"])
@api
def decks(request):
    """GET lista decks+Grimorium; POST cria deck {slot, name}."""
    if request.method == "POST":
        d = json_body(request)
        deck = services.create_deck(request.user, int(d.get("slot", 0) or 0), d.get("name"))
        return ok({"deck_id": deck.id}, 201)
    return JsonResponse({"ok": True, **services.decks_payload(request.user)})


@require_http_methods(["PATCH", "DELETE"])
@api
def deck_detail(request, deck_id):
    if request.method == "DELETE":
        services.delete_deck(request.user, deck_id)
    else:
        services.rename_deck(request.user, deck_id, json_body(request).get("name"))
    return ok()


@require_POST
@api
def move(request):
    """POST {card_uid, kind: 'deck'|'grimorium', deck_id?}"""
    d = json_body(request)
    services.move_card(request.user, d.get("card_uid"), d.get("kind"), d.get("deck_id"))
    return ok()


@require_POST
@api
def select(request):
    """POST {slot} define o deck usado nas partidas."""
    services.select_deck(request.user, int(json_body(request).get("slot", 0) or 0))
    return ok()
