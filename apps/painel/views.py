"""Painel administrativo (P§22). Páginas server-side simples; monitor em tempo real por WebSocket."""
import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import Conta
from apps.cards import schema, services as card_services
from apps.cards.models import Carta
from apps.chat.services import purge_old
from apps.core.models import ConfigServidor, Servidor
from apps.decks.models import Deck, Grimorium
from apps.game.models import HistoricoEvento, HistoricoPartida

from .access import staff_required
from .forms import CartaForm, ConfigForm, ContaAdminForm, ImportForm, ServidorForm


def _page(request, qs, per=40):
    return Paginator(qs, per).get_page(request.GET.get("page"))


@staff_required
def dashboard(request):
    return render(request, "painel/dashboard.html", {"nav": "dashboard"})


# ----------------------------------------------------------------------------------- contas
@staff_required
def contas(request):
    q = request.GET.get("q", "").strip()
    qs = Conta.objects.all().order_by("id")
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(email__icontains=q)
    return render(request, "painel/contas.html", {"nav": "contas", "page": _page(request, qs), "q": q})


@staff_required
def conta_edit(request, conta_id):
    conta = Conta.objects.filter(id=conta_id).first()
    if conta is None:
        raise Http404
    form = ContaAdminForm(request.POST or None, instance=conta, editor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta atualizada.")
        return redirect("painel_contas")
    return render(request, "painel/form.html", {"nav": "contas", "title": f"Conta: {conta.name}", "form": form})


# ----------------------------------------------------------------------------------- cartas
@staff_required
def cartas(request):
    q = request.GET.get("q", "").strip()
    qs = Carta.objects.all()
    if q:
        qs = qs.filter(name__icontains=q) | (qs.filter(card_id=int(q)) if q.isdigit() else qs.none())
    return render(request, "painel/cartas.html", {"nav": "cartas", "page": _page(request, qs.order_by("card_id")), "q": q})


def _carta_initial(c: Carta) -> dict:
    return {"card_id": c.card_id, "type": c.type, "name": c.name, "rarity": c.rarity, "power": c.power,
            "power_bonus": c.power_bonus, "attack_bonus": c.attack_bonus, "damage": c.damage,
            "shield": c.shield, "mana_cost": c.mana_cost,
            "elements": "|".join(e.element for e in c.elementos.order_by("slot")),
            "mana_gains": "|".join(f"{g.element}:{g.value}" for g in c.managains.order_by("slot")),
            "skills": "|".join(f"{s.slot}:{s.name}:{s.number}:{s.manacost}:{s.txt_key}" for s in c.skills.order_by("slot"))}


@staff_required
def carta_edit(request, card_id=None):
    existing = Carta.objects.filter(card_id=card_id).first() if card_id else None
    if card_id and existing is None:
        raise Http404
    form = CartaForm(request.POST or None, initial=_carta_initial(existing) if existing else None)
    if request.method == "POST" and form.is_valid():
        n = schema.normalize_card_dict(form.to_card_dict())
        if not existing and Carta.objects.filter(card_id=n["card_id"]).exists():
            form.add_error("card_id", "Card_ID já existe.")
        else:
            card_services.upsert_card(n)
            card_services.invalidate_cache()
            messages.success(request, "Carta salva.")
            return redirect("painel_cartas")
    return render(request, "painel/form.html", {"nav": "cartas", "form": form,
                                                "title": "Editar carta" if existing else "Nova carta"})


@staff_required
@require_POST
def carta_delete(request, card_id):
    try:
        Carta.objects.filter(card_id=card_id).delete()
        card_services.invalidate_cache()
        messages.success(request, "Carta removida.")
    except ProtectedError:
        messages.error(request, "Carta em uso em decks/Grimorium: não pode ser removida.")
    return redirect("painel_cartas")


@staff_required
def cartas_import(request):
    form, report = ImportForm(request.POST or None, request.FILES or None), None
    if request.method == "POST" and form.is_valid():
        f = form.cleaned_data["arquivo"]
        try:
            text = f.read().decode("utf-8-sig")
            raw = schema.parse_json(text) if f.name.lower().endswith(".json") else schema.parse_csv(text)
            report = card_services.import_cards(raw, overwrite=form.cleaned_data["sobrescrever"])
        except (ValueError, UnicodeDecodeError) as e:
            form.add_error("arquivo", f"Arquivo inválido: {e}")
    return render(request, "painel/import.html", {"nav": "cartas", "form": form, "report": report})


@staff_required
def cartas_export(request):
    data = json.dumps({"cards": card_services.export_cards()}, ensure_ascii=False, indent=1)
    resp = HttpResponse(data, content_type="application/json; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="cartas.json"'
    return resp


# ----------------------------------------------------------------------------------- decks / histórico
@staff_required
def decks(request):
    qs = Deck.objects.select_related("owner").annotate(n=Count("cards")).order_by("owner_id", "slot")
    return render(request, "painel/decks.html", {"nav": "decks", "page": _page(request, qs),
                                                 "grims": Grimorium.objects.select_related("owner").annotate(n=Count("cards"))[:200]})


@staff_required
def deck_detail(request, deck_id):
    deck = Deck.objects.select_related("owner").filter(id=deck_id).first()
    if deck is None:
        raise Http404
    return render(request, "painel/cards_in.html", {"nav": "decks", "title": f"Deck {deck.name} ({deck.owner.name})",
                                                    "cards": deck.cards.select_related("carta").order_by("carta_id")})


@staff_required
def grimorium_detail(request, grim_id):
    g = Grimorium.objects.select_related("owner").filter(id=grim_id).first()
    if g is None:
        raise Http404
    return render(request, "painel/cards_in.html", {"nav": "decks", "title": f"Grimorium de {g.owner.name}",
                                                    "cards": g.cards.select_related("carta").order_by("carta_id")})


@staff_required
def historico(request):
    qs = HistoricoPartida.objects.select_related("jogador_a", "jogador_b")
    return render(request, "painel/historico.html", {"nav": "historico", "page": _page(request, qs)})


@staff_required
def historico_detail(request, partida_id):
    p = HistoricoPartida.objects.select_related("jogador_a", "jogador_b").filter(id=partida_id).first()
    if p is None:
        raise Http404
    ev = HistoricoEvento.objects.filter(partida=p).order_by("seq")
    return render(request, "painel/historico_detail.html", {"nav": "historico", "p": p, "page": _page(request, ev, 100)})


# ----------------------------------------------------------------------------------- configurações
@staff_required
def config(request):
    sform, cform = ServidorForm(prefix="s"), ConfigForm(prefix="c")
    if request.method == "POST":
        if "add_server" in request.POST:
            sform = ServidorForm(request.POST, prefix="s")
            if sform.is_valid():
                sform.save()
                messages.success(request, "Servidor salvo.")
                return redirect("painel_config")
        elif "add_config" in request.POST:
            cform = ConfigForm(request.POST, prefix="c")
            if cform.is_valid():
                ConfigServidor.objects.update_or_create(key=cform.cleaned_data["key"],
                                                        defaults={"value": cform.cleaned_data["value"]})
                messages.success(request, "Configuração salva.")
                return redirect("painel_config")
        elif "toggle_server" in request.POST:
            s = Servidor.objects.filter(id=request.POST.get("id")).first()
            if s:
                s.active = not s.active
                s.save(update_fields=["active"])
            return redirect("painel_config")
        elif "purge_chat" in request.POST:
            messages.success(request, f"{purge_old()} mensagens antigas removidas.")
            return redirect("painel_config")
    return render(request, "painel/config.html", {"nav": "config", "sform": sform, "cform": cform,
                                                  "servers": Servidor.objects.all(), "configs": ConfigServidor.objects.all()})
