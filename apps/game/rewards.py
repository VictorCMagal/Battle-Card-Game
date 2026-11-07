"""Recompensas de fim de partida (O§1 Battlepoints, D-07, D-21, D-23). Função pura.

* vitória por LIFE: vencedor +100 BP, perdedor +50 BP; empate: +25 para ambos
* AFK / abandono / desconexão expirada: perdedor 0 BP, vencedor +10 BP
* magicdust: +1 por carta destruída pelo jogador (`stats[slot]["destroyed"]`)
* victory_counts: +1 ao vencedor
* modo debug e partidas sem resultado: nada é concedido
"""
WIN_BP, LOSE_BP, DRAW_BP, FORFEIT_WIN_BP = 100, 50, 25, 10


def compute_rewards(result, mode, stats=None) -> dict:
    zero = {"battlepoints": 0, "magicdust": 0, "victories": 0}
    out = {"A": dict(zero), "B": dict(zero)}
    if not result or mode == "debug" or result.get("type") not in ("win", "draw"):
        return out  # sem resultado, debug ou partida cancelada: nada é concedido
    stats = stats or {}
    for slot in ("A", "B"):
        out[slot]["magicdust"] = int(stats.get(slot, {}).get("destroyed", 0))
    if result["type"] == "draw":
        out["A"]["battlepoints"] = out["B"]["battlepoints"] = DRAW_BP
        return out
    winner, loser = result["winner"], result["loser"]
    out[winner]["victories"] = 1
    if result["reason"] == "life":
        out[winner]["battlepoints"], out[loser]["battlepoints"] = WIN_BP, LOSE_BP
    else:
        out[winner]["battlepoints"], out[loser]["battlepoints"] = FORFEIT_WIN_BP, 0
    return out
