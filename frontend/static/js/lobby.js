(async function () {
  await BCG.init();
  const sid = parseInt(sessionStorage.getItem('bcg_server') || '0', 10);
  if (!sid) { location.href = '/servidores/'; return; }
  document.getElementById('logoutBtn').addEventListener('click', BCG.logout);
  const me = await BCG.api('GET', '/api/me/');
  if (me.ok) {
    document.getElementById('meName').textContent = me.user.name + ' · BP ' + me.user.battlepoints;
    if (me.user.is_admin) document.getElementById('panelLink').hidden = false;
  }
  const $ = (id) => document.getElementById(id);
  const chatLog = $('chatLog'), target = $('chatTarget');
  let myName = '', users = [];

  function addChat(m) {
    const line = BCG.el('div', { class: m.scope === 'private' ? 'priv' : '' }, [
      BCG.el('span', { class: 't', text: '[' + m.time + '] ' }),
      BCG.el('strong', { text: m.from + (m.scope === 'private' ? ' → ' + m.to : '') + ': ' }),
      BCG.el('span', { text: m.text })]);
    chatLog.append(line); chatLog.scrollTop = chatLog.scrollHeight;
  }
  function renderUsers(list) {
    users = list;
    const ul = $('userList'); ul.textContent = '';
    const keep = target.value;
    target.textContent = '';
    target.append(BCG.el('option', { value: '', text: BCG.t('chat.all') }));
    list.forEach((u) => {
      const li = BCG.el('li', {}, [BCG.el('span', { text: u })]);
      if (u !== myName) {
        li.append(BCG.el('button', { class: 'btn', text: BCG.t('lobby.message'), onclick: () => { target.value = u; $('chatInput').focus(); } }));
        li.append(BCG.el('button', { class: 'btn', text: BCG.t('lobby.invite'), onclick: () => sock.send({ type: 'invite', to: u }) }));
        target.append(BCG.el('option', { value: u, text: BCG.t('lobby.private_to', { to: u }) }));
      }
      ul.append(li);
    });
    if (list.includes(keep)) target.value = keep;
  }
  function renderRooms(rooms) {
    const body = $('roomRows'); body.textContent = '';
    if (!rooms.length) { body.append(BCG.el('tr', {}, [BCG.el('td', { colspan: '6', class: 'muted', text: BCG.t('lobby.no_rooms') })])); return; }
    rooms.forEach((r) => {
      const join = BCG.el('button', { class: 'btn primary', text: BCG.t('lobby.join') + (r.has_password ? ' 🔒' : ''), onclick: () => joinRoom(r) });
      if (!r.joinable) join.disabled = true;
      body.append(BCG.el('tr', {}, [BCG.el('td', { text: r.id }), BCG.el('td', { text: r.name }), BCG.el('td', { text: BCG.t('mode.' + r.mode) }),
        BCG.el('td', { text: BCG.t('status.' + r.status) }), BCG.el('td', { text: r.players.join(' x ') }), BCG.el('td', {}, [join])]));
    });
  }
  function joinRoom(r, pw) {
    let password = pw;
    if (r.has_password && password === undefined) { password = window.prompt(BCG.t('lobby.ask_password')); if (password === null) return; }
    sock.send({ type: 'join_room', room_id: r.id, password: password || '' });
  }

  const sock = BCG.connect('/ws/lobby/' + sid + '/', {
    message(d) {
      switch (d.type) {
        case 'lobby_state': myName = d.you; renderUsers(d.users); renderRooms(d.rooms);
          if (d.room_id) location.href = '/sala/?r=' + d.room_id; break;
        case 'users': renderUsers(d.users); break;
        case 'rooms': renderRooms(d.rooms); break;
        case 'chat': addChat(d); break;
        case 'room_joined': location.href = '/sala/?r=' + d.room_id; break;
        case 'room_found':
          if (!d.room) BCG.toast(BCG.t('lobby.room_not_found'), 'error'); else joinRoom(d.room); break;
        case 'invite': {
          const box = $('inviteBox'); box.textContent = ''; box.hidden = false;
          box.append(BCG.el('span', { text: BCG.t('lobby.invite_received', { from: d.from, room: d.room_id }) + ' ' }));
          box.append(BCG.el('button', { class: 'btn primary', text: BCG.t('lobby.join'), onclick: () => { box.hidden = true; joinRoom({ id: d.room_id, has_password: d.has_password }); } }));
          box.append(BCG.el('button', { class: 'btn', text: BCG.t('common.close'), onclick: () => { box.hidden = true; } }));
          break; }
        case 'notify': BCG.toast(d.text, 'ok'); break;
        case 'error': BCG.toast(d.message, 'error'); break;
      }
    },
    close(code) { if (code === 4404) location.href = '/servidores/'; if (code === 4401 || code === 4000) location.href = '/login/'; },
  });

  $('createForm').addEventListener('submit', (ev) => {
    ev.preventDefault(); const f = ev.target;
    sock.send({ type: 'create_room', name: f.name.value, mode: f.mode.value, password: f.password.value });
  });
  $('findBtn').addEventListener('click', () => { const v = parseInt($('findId').value, 10); if (v) sock.send({ type: 'find_room', room_id: v }); });
  $('chatForm').addEventListener('submit', (ev) => {
    ev.preventDefault(); const text = $('chatInput').value.trim(); if (!text) return;
    if (target.value) sock.send({ type: 'private_chat', to: target.value, text }); else sock.send({ type: 'chat', text });
    $('chatInput').value = '';
  });
})();
