"""Buffer circular com os últimos erros, exibido no painel de monitoramento (P§23)."""
import logging
from collections import deque

RECENT = deque(maxlen=200)


class RingBufferHandler(logging.Handler):
    def emit(self, record):
        try:
            RECENT.append({"time": record.created, "level": record.levelname, "logger": record.name,
                           "message": record.getMessage()[:500]})
        except Exception:  # noqa: BLE001
            pass
