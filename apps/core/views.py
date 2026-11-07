"""Páginas HTML (templates mínimos; lógica no JS) e APIs de status/servidores/i18n."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from . import presence
from .http import api_public
from .i18n import load_messages
from .models import Servidor


def page(template: str, protected: bool = False):
    """Fábrica de views de página. O template injeta o token CSRF em <meta>."""
    def view(request):
        return render(request, template, {"idioma": settings.IDIOMA})
    return login_required(view) if protected else view


@api_public
def status(request):
    """Status do servidor para o index.html (O§1)."""
    return JsonResponse({"ok": True, "online": True, "users_online": presence.count(),
                         "servers": Servidor.objects.filter(active=True).count()})


@api_public
def servidores(request):
    """Lista servidores com ocupação (tela de seleção de servidor)."""
    items = [{"id": s.id, "name": s.name, "online": True, "users_online": presence.count(s.id)}
             for s in Servidor.objects.filter(active=True).order_by("id")]
    return JsonResponse({"ok": True, "servers": items})


@api_public
def i18n(request):
    """Dicionário de textos do idioma atual para o frontend."""
    return JsonResponse({"ok": True, "lang": settings.IDIOMA, "messages": load_messages(settings.IDIOMA)})
