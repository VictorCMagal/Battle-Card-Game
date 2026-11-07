"""Logs com rotação por categoria (P§10): django, ws, match, app. Nunca registra senhas."""
import re


def build_logging(log_dir, level="INFO"):
    log_dir.mkdir(parents=True, exist_ok=True)

    def file_handler(name):
        return {"class": "logging.handlers.RotatingFileHandler", "filename": str(log_dir / f"{name}.log"),
                "maxBytes": 5 * 1024 * 1024, "backupCount": 5, "encoding": "utf-8",
                "formatter": "std", "filters": ["redact"]}

    return {
        "version": 1, "disable_existing_loggers": False,
        "filters": {"redact": {"()": "config.logging_conf.RedactFilter"}},
        "formatters": {"std": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "std", "filters": ["redact"]},
            "django": file_handler("django"), "ws": file_handler("ws"),
            "match": file_handler("match"), "app": file_handler("app"),
            "ring": {"class": "apps.core.logbuffer.RingBufferHandler", "level": "ERROR"},
        },
        "loggers": {
            "django": {"handlers": ["django", "console", "ring"], "level": level, "propagate": False},
            "bcg.ws": {"handlers": ["ws", "console", "ring"], "level": level, "propagate": False},
            "bcg.match": {"handlers": ["match", "console", "ring"], "level": level, "propagate": False},
            "bcg": {"handlers": ["app", "console", "ring"], "level": level, "propagate": False},
        },
    }


import logging  # noqa: E402

_SECRET = re.compile(r"(password|senha|token|secret|sessionid)\s*[=:]\s*\S+", re.I)


class RedactFilter(logging.Filter):
    """Remove valores sensíveis das mensagens antes de gravar."""

    def filter(self, record):
        try:
            msg = record.getMessage()
        except Exception:  # noqa: BLE001
            return True
        record.msg, record.args = _SECRET.sub(r"\1=***", msg), ()
        return True
