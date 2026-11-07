"""Validação, limitação de taxa e persistência de mensagens de chat."""
import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.core import ratelimit
from apps.core.errors import ServiceError

from .models import ChatMensagem

_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def clean_text(text) -> str:
    """Remove controles, aplica trim e limita a 126 caracteres. Erro se vazio/maior."""
    text = _CTRL.sub(" ", str(text or "")).strip()
    if not text:
        raise ServiceError("err.chat_empty")
    if len(text) > settings.CHAT_MAX_LEN:
        raise ServiceError("err.chat_too_long", max=settings.CHAT_MAX_LEN)
    return text


def check_rate(user_id: int) -> None:
    limit, window = settings.CHAT_RATE
    if not ratelimit.allow(f"chat:{user_id}", limit, window):
        raise ServiceError("err.rate_limited", 429)


def save_message(canal: str, user, text: str):
    return ChatMensagem.objects.create(canal=canal[:40], sender=user, sender_name=user.name, texto=text)


def time_now() -> str:
    """Hora local do servidor (fuso configurável) para exibir no chat."""
    return timezone.localtime().strftime("%H:%M:%S")


def purge_old() -> int:
    """Remove mensagens além da retenção configurada. Retorna quantas foram apagadas."""
    limit = timezone.now() - timedelta(days=settings.CHAT_RETENTION_DAYS)
    return ChatMensagem.objects.filter(criado_em__lt=limit).delete()[0]
