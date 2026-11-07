"""Registro de presença (usuários online) e contadores de conexão, por processo."""
import threading
import time

_lock = threading.RLock()
_users = {}        # user_id -> {"name", "server", "channels": set()}
STATS = {"started": time.time(), "ws_connections": 0, "ws_total": 0, "matches_total": 0}


def add(user_id: int, name: str, server_id, channel: str) -> bool:
    """Registra uma conexão. Retorna True se o usuário acabou de ficar online."""
    with _lock:
        entry = _users.get(user_id)
        first = entry is None
        if first:
            entry = _users[user_id] = {"name": name, "server": server_id, "channels": set()}
        entry["channels"].add(channel)
        if server_id is not None:
            entry["server"] = server_id
        STATS["ws_connections"] += 1
        STATS["ws_total"] += 1
        return first


def remove(user_id: int, channel: str) -> bool:
    """Remove uma conexão. Retorna True se o usuário ficou offline."""
    with _lock:
        entry = _users.get(user_id)
        if not entry:
            return False
        entry["channels"].discard(channel)
        STATS["ws_connections"] = max(0, STATS["ws_connections"] - 1)
        if not entry["channels"]:
            del _users[user_id]
            return True
        return False


def online_users(server_id=None) -> list:
    with _lock:
        return sorted((e["name"] for e in _users.values() if server_id in (None, e["server"])),
                      key=str.lower)


def count(server_id=None) -> int:
    return len(online_users(server_id))


def is_online(user_id: int) -> bool:
    with _lock:
        return user_id in _users


def find_by_name(name: str):
    """Retorna (user_id, name) de um usuário online pelo nome (sem diferenciar maiúsculas)."""
    with _lock:
        for uid, e in _users.items():
            if e["name"].lower() == name.lower():
                return uid, e["name"]
    return None
