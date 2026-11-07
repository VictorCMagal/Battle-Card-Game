(function () {
  const $ = (id) => document.getElementById(id);
  const cell = (t) => { const td = document.createElement('td'); td.textContent = String(t); return td; };
  function fill(id, rows) {
    const body = $(id); body.textContent = '';
    rows.forEach((r) => { const tr = document.createElement('tr'); r.forEach((c) => tr.append(cell(c))); body.append(tr); });
  }
  function connect() {
    const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws/admin/monitor/');
    ws.onopen = () => { $('mConn').textContent = 'Conectado (atualiza a cada 2 s).'; };
    ws.onclose = (ev) => { $('mConn').textContent = 'Desconectado.'; if (ev.code !== 4403) setTimeout(connect, 3000); };
    ws.onmessage = (ev) => {
      const d = JSON.parse(ev.data); if (d.type !== 'snapshot') return;
      $('mUsers').textContent = d.users_online; $('mWs').textContent = d.ws_connections; $('mRooms').textContent = d.rooms.length;
      $('mMatches').textContent = d.matches.length; $('mTotal').textContent = d.matches_total; $('mUptime').textContent = d.uptime;
      $('mUserList').textContent = d.users.join(', ') || '–';
      fill('mRoomRows', d.rooms.map((r) => [r.id, r.name, r.mode, r.status, r.players.join(' x ')]));
      fill('mMatchRows', d.matches.map((m) => [m.room, m.mode, m.phase, m.turn, m.players.join(' x ')]));
      fill('mErrRows', d.errors.slice().reverse().map((e) => [new Date(e.time * 1000).toLocaleTimeString(), e.level, e.logger, e.message]));
    };
  }
  connect();
})();
