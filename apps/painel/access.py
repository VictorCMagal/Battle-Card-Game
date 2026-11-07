"""Controle de acesso do painel: apenas contas ADMIN/DEV. Alterar contas privilegiadas é
exclusivo de DEV."""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden


def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), "/login/")
        if not request.user.is_staff:
            return HttpResponseForbidden("Acesso restrito a administradores.")
        return view(request, *args, **kwargs)
    return wrapper
