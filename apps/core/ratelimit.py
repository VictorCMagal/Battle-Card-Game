"""Limitador de taxa em memória (janela deslizante). Suficiente para um processo único."""
import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits = defaultdict(deque)


def allow(key: str, limit: int, window: float) -> bool:
    """True se a chave ainda pode agir (e registra a tentativa)."""
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        if len(_hits) > 5000:  # evita crescimento indefinido
            for k in [k for k, v in _hits.items() if not v]:
                _hits.pop(k, None)
        return True


def reset(key: str) -> None:
    with _lock:
        _hits.pop(key, None)
