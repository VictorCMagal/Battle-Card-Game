# WebSockets

Autenticação pela sessão do Django; origem validada (`AllowedHostsOriginValidator`). Limites: 8 KB por mensagem, 40 mensagens/5 s por conexão.
Mensagens JSON `{type, ...}`. Códigos de fechamento: 4401 sem login, 4403 sem permissão, 4404 não encontrado, 4000 sessão substituída.

## `/ws/lobby/<servidor>/`
Cliente→servidor: `chat{text}`, `private_chat{to,text}`, `create_room{name,mode,password}`, `join_room{room_id,password}`,
`find_room{room_id}`, `invite{to}`, `ping`. Servidor→cliente: `lobby_state`, `users`, `rooms`, `chat`, `room_joined`, `room_found`, `invite`, `notify`, `error`.

## `/ws/sala/<id>/`
Cliente→servidor: `chat{text}`, `ready{value}`, `leave`, `coin{symbol}`, `cmd{cmd}`, `sync`.
`cmd.type`: `walk_avatar{x,y}`, `summon{uid,x,y,face_up}`, `double_cast`, `move{uid,x,y}`, `use_skill{uid,slot,target}`, `end_turn`, `select{uid|null}`.
O jogador do comando é sempre definido pelo servidor (o cliente não escolhe `player`).
Servidor→cliente: `room_state`, `chat`, `coin_state`, `coin_result`, `match_state{view,events,deadline,server_time}`,
`match_end{result,rewards}`, `opponent_status`, `error`, `left`.

## `/ws/admin/monitor/`
Somente ADMIN/DEV: `snapshot` a cada 2 s (usuários, conexões, salas, partidas, erros recentes).

Reconexão: o cliente reconecta com backoff; ao abrir envia `sync` e o servidor reenvia sala e estado da partida.
Partida em andamento: janela de 120 s; os timers continuam; expirada, o ausente perde sem BP e o adversário recebe 10.
