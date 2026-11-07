"""Internacionalização simples por dicionários JSON (locale/<idioma>/messages.json) (P§29).

Servidor e frontend usam as mesmas chaves. Para adicionar um idioma crie
locale/en_US/messages.json e defina IDIOMA=EN-US no .env."""
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings


def _dir(lang: str) -> str:
    return lang.replace("-", "_")


@lru_cache(maxsize=8)
def load_messages(lang: str) -> dict:
    path = Path(settings.BASE_DIR) / "locale" / _dir(lang) / "messages.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def t(key: str, lang: str = None, **params) -> str:
    """Traduz uma chave (com fallback para o idioma padrão e depois para a própria chave)."""
    lang = lang or settings.IDIOMA
    text = load_messages(lang).get(key) or load_messages("PT-BR").get(key) or key
    try:
        return text.format(**params)
    except (KeyError, IndexError, ValueError):
        return text
