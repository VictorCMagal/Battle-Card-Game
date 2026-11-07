"""APIs de conta: cadastro, disponibilidade, login, logout e dados do usuário logado."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from apps.core import ratelimit
from apps.core.errors import ServiceError
from apps.core.http import api, api_public, fail, json_body, ok
from apps.core.i18n import t

from . import rules, services


def _field_errors(errors: dict) -> JsonResponse:
    fields = {f: [{"key": k, "message": t(k)} for k in keys] for f, keys in errors.items()}
    return JsonResponse({"ok": False, "error": "err.validation", "message": t("err.validation"),
                         "fields": fields}, status=422)


@require_POST
@api_public
def register(request):
    """POST /api/contas/ {name, password, password2, email}"""
    d = json_body(request)
    name, email = str(d.get("name", "")), str(d.get("email", "")).strip()
    errors = rules.validate_registration(name, str(d.get("password", "")), str(d.get("password2", "")), email)
    if errors:
        return _field_errors(errors)
    conta = services.register_account(name, email, str(d["password"]))
    return ok({"user": services.user_payload(conta)}, 201)


@require_GET
@api_public
def availability(request):
    """GET /api/contas/disponibilidade/?name=&email= (checagem assíncrona do formulário)."""
    ip = request.META.get("REMOTE_ADDR", "?")
    if not ratelimit.allow(f"avail:{ip}", 30, 60):
        raise ServiceError("err.rate_limited", 429)
    name, email = request.GET.get("name"), request.GET.get("email")
    out = {"ok": True}
    if name is not None:
        errs = rules.validate_name(name)
        out["name"] = {"valid": not errs, "available": not errs and not services.name_taken(name),
                       "errors": [t(k) for k in errs]}
    if email is not None:
        errs = rules.validate_email(email)
        out["email"] = {"valid": not errs, "available": not errs and not services.email_taken(email),
                        "errors": [t(k) for k in errs]}
    return JsonResponse(out)


@require_POST
@api_public
def login_view(request):
    """POST /api/login/ {name, password}. Limita tentativas e mantém sessão única (D-26)."""
    d = json_body(request)
    name, password = str(d.get("name", ""))[:32], str(d.get("password", ""))[:128]
    key = f"login:{request.META.get('REMOTE_ADDR', '?')}:{name.lower()}"
    limit, window = settings.LOGIN_RATE
    if not ratelimit.allow(key, limit, window):
        raise ServiceError("err.rate_limited", 429)
    user = authenticate(request, username=name, password=password)
    if user is None:
        return fail("err.invalid_credentials", 401)
    old_key = user.last_session_key
    login(request, user)
    if not request.session.session_key:
        request.session.save()
    if old_key and old_key != request.session.session_key:
        Session.objects.filter(session_key=old_key).delete()
        try:  # derruba WebSockets da sessão anterior
            async_to_sync(get_channel_layer().group_send)(f"user_{user.id}", {"type": "force.close"})
        except Exception:  # noqa: BLE001
            pass
    user.last_session_key = request.session.session_key
    user.save(update_fields=["last_session_key"])
    ratelimit.reset(key)
    return ok({"user": services.user_payload(user)})


@require_POST
@api_public
def logout_view(request):
    if request.user.is_authenticated:
        request.user.last_session_key = None
        request.user.save(update_fields=["last_session_key"])
    logout(request)
    return ok()


@require_GET
@api
def me(request):
    return ok({"user": services.user_payload(request.user)})
