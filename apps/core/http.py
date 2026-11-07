"""Helpers de resposta/entrada JSON para as views."""
import json
from functools import wraps

from django.http import JsonResponse

from .errors import ServiceError
from .i18n import t


def json_body(request) -> dict:
    """Lê o corpo JSON (objeto). Retorna {} se vazio e levanta ServiceError se inválido."""
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ServiceError("err.invalid_json")
    if not isinstance(data, dict):
        raise ServiceError("err.invalid_json")
    return data


def ok(data=None, status=200):
    return JsonResponse({"ok": True, **(data or {})}, status=status)


def fail(code, status=400, **params):
    return JsonResponse({"ok": False, "error": code, "message": t(code, **params)}, status=status)


def api(view):
    """Converte ServiceError em JSON e exige login (use `api_public` para rotas abertas)."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return fail("err.login_required", 401)
        try:
            return view(request, *args, **kwargs)
        except ServiceError as e:
            return fail(e.code, e.status, **e.params)
    return wrapper


def api_public(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except ServiceError as e:
            return fail(e.code, e.status, **e.params)
    return wrapper
