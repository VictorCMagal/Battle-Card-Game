/* Sala + arena. O servidor é autoritativo: o cliente só envia pedidos (cmd) e desenha a view
   recebida. Cartas ocultas do adversário nunca chegam ao navegador. */
(async function () {
  await BCG.init();
  const roomId = parseInt(new URLSearchParams(location.search).get('r') || '0', 10);
  if (!roomId) { location.href = '/lobby/'; return; }
  const $ = (id) => document.getElementById(id);
  const other = (s) => (s === 'A' ? 'B' : 'A');
  let room = null, mySlot = null, view = null, users = {}, offset = 0, deadline = 0, pendingSkill = null, coinDeadline = 0;
  let lastResult = null;

  const sock = BCG.connect('/ws/sala/' + roomId + '/', {
    open() { sock.send({ type: 'sync' }); },
    message: onMessage,
    close(code) { if (code === 4401 || code === 4403 || code === 4000) location.href = '/lobby/'; },
  });
  const send = (o) => sock.send(o);
  const cmd = (c) => send({ type: 'cmd', cmd: c });

  // ------------------------------------------------------------------ mensagens
  function onMessage(d) {
    switch (d.type) {
      case 'room_state': room = d.room; if (d.slot) mySlot = d.slot; renderRoom(); break;
      case 'chat': addLine('chatLog', d); break;
      case 'error': BCG.toast(d.message, 'error'); break;
      case 'left': location.href = '/lobby/'; break;
      case 'notify': BCG.toast(d.text, 'ok'); break;
      case 'coin_state': showCoin(d); break;
      case 'coin_result':
        $('coinText').textContent = BCG.t('coin.result', { s: d.initiative || '', p: d.first || '' });
        document.querySelectorAll('#coinOverlay [data-symbol]').forEach((b) => { b.disabled = true; });
        $('coinOverlay').hidden = false; break;
      case 'match_state': onState(d); break;
      case 'match_end': onEnd(d); break;
      case 'opponent_status':
        BCG.toast(d.connected ? BCG.t('notify.opp_reconnected') : BCG.t('notify.opp_disconnected', { s: d.seconds }), d.connected ? 'ok' : 'error'); break;
    }
  }

  function addLine(boxId, m) {
    const box = $(boxId);
    box.append(BCG.el('div', {}, [BCG.el('span', { class: 't', text: '[' + (m.time || BCG.time()) + '] ' }),
      BCG.el('strong', { text: (m.from || '') + (m.from ? ': ' : '') }), BCG.el('span', { text: m.text || '' })]));
    box.scrollTop = box.scrollHeight;
  }

  // ------------------------------------------------------------------ sala
  function renderRoom() {
    $('roomTitle').textContent = room.name + ' (#' + room.id + ')';
    $('roomStatus').textContent = BCG.t('status.' + room.status) + ' · ' + BCG.t('mode.' + room.mode);
    const ul = $('slotList'); ul.textContent = '';
    ['A', 'B'].forEach((s) => {
      const name = room.slots[s];
      ul.append(BCG.el('li', {}, [BCG.el('strong', { text: s + ': ' }),
        BCG.el('span', { text: name ? name + (s === mySlot ? ' (' + BCG.t('room.you') + ')' : '') : BCG.t('room.slot_free') }),
        BCG.el('span', { text: room.ready[s] ? ' ✓ READY' : '' })]));
    });
    const mine = !!(mySlot && room.ready[mySlot]);
    $('readyBtn').textContent = mine ? BCG.t('room.not_ready') : BCG.t('room.ready');
    $('readyBtn').disabled = room.status === 'BATTLE';
    $('roomMsg').textContent = room.mode === 'debug' ? BCG.t('room.debug_hint') : (!room.slots.B ? BCG.t('room.waiting') : '');
  }
  $('readyBtn').addEventListener('click', () => send({ type: 'ready', value: !(room && mySlot && room.ready[mySlot]) }));
  $('leaveBtn').addEventListener('click', () => send({ type: 'leave' }));
  $('chatForm').addEventListener('submit', (ev) => {
    ev.preventDefault(); const t = $('chatInput').value.trim(); if (t) send({ type: 'chat', text: t }); $('chatInput').value = '';
  });

  // ------------------------------------------------------------------ X / O
  function showCoin(d) {
    offset = Date.now() / 1000 - d.server_time; coinDeadline = d.deadline;
    $('coinOverlay').hidden = false;
    $('coinText').textContent = d.your_choice ? BCG.t('coin.chosen', { s: d.your_choice }) : BCG.t('coin.pick');
    document.querySelectorAll('#coinOverlay [data-symbol]').forEach((b) => {
      b.disabled = !!d.your_choice || d.taken.includes(b.dataset.symbol);
    });
  }
  document.querySelectorAll('#coinOverlay [data-symbol]').forEach((b) => b.addEventListener('click', () => send({ type: 'coin', symbol: b.dataset.symbol })));

  // ------------------------------------------------------------------ estado da partida
  const ctrl = () => (view.mode === 'debug' ? view.current : view.you);
  const isMyTurn = () => view && view.phase === 'ACTION' && (view.mode === 'debug' || view.current === view.you);
  const cardAt = (x, y) => (view.board.find((c) => c.x === x && c.y === y) || null);
  const byUid = (uid) => view.board.find((c) => c.uid === uid) || null;
  const selection = () => view.players[ctrl()].selection;

  function onState(d) {
    view = d.view; users = d.users || {}; offset = Date.now() / 1000 - d.server_time; deadline = d.deadline;
    $('coinOverlay').hidden = true; $('roomPanel').hidden = true; $('arenaWrap').hidden = false;
    (d.events || []).forEach((ev) => { const t = eventText(ev); if (t) addLine('eventLog', { text: t }); });
    if (!isMyTurn()) pendingSkill = null;
    render();
  }

  function eventText(ev) {
    const key = 'ev.' + ev.type;
    if (BCG.messages[key] === undefined) return null;
    const p = Object.assign({}, ev);
    if (ev.card) p.name = ev.card.name || '?';
    if (ev.reason) p.reason = BCG.messages['reason.' + ev.reason] || ev.reason;
    if (ev.skill) p.skill = BCG.messages['skill.' + ev.skill + '.name'] || ev.skill;
    return BCG.t(key, p);
  }

  function neighbors(x, y, diag) {
    const out = [];
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      if (!dx && !dy) continue; if (!diag && dx && dy) continue;
      const nx = x + dx, ny = y + dy; if (nx >= 0 && nx < 5 && ny >= 0 && ny < 5) out.push(nx + ',' + ny);
    }
    return out;
  }
  const avatarOf = (slot) => view.board.find((c) => c.is_avatar && c.owner === slot);

  function highlights() {
    const hl = {}; const me = ctrl(); const sel = selection();
    if (!isMyTurn()) return hl;
    if (pendingSkill) { view.board.forEach((c) => { if (c.owner !== me && !c.is_avatar && c.face_up) hl[c.x + ',' + c.y] = 'hl-target'; }); return hl; }
    if (!sel) return hl;
    if (sel.zone === 'hand') { const av = avatarOf(me); neighbors(av.x, av.y, true).forEach((k) => { hl[k] = 'hl-summon'; }); }
    else { const c = byUid(sel.uid); if (c) neighbors(c.x, c.y, false).forEach((k) => { hl[k] = 'hl-move'; }); }
    return hl;
  }

  function render() {
    renderBars(); renderBoard(); renderHand();
    const my = isMyTurn();
    $('endTurnBtn').disabled = !my; $('doubleCastBtn').disabled = !my;
    $('turnInfo').textContent = BCG.t('arena.turn', { n: view.turn }) + ' · ' + (view.mode === 'debug' ? BCG.t('arena.debug_turn', { p: view.current }) : (my ? BCG.t('arena.your_turn') : BCG.t('arena.opp_turn')));
  }

  function bar(slot, title) {
    const p = view.players[slot];
    return [BCG.el('strong', { text: title + ' (' + slot + ')' }), BCG.el('span', { class: 'life', text: BCG.t('arena.life') + ' ' + p.life }),
      BCG.el('span', { class: 'mana', text: BCG.t('arena.mana') + ' ' + p.mana }), BCG.el('span', { text: BCG.t('arena.hand') + ' ' + p.hand_count }),
      BCG.el('span', { text: BCG.t('arena.deck') + ' ' + p.deck_count }), BCG.el('span', { text: BCG.t('arena.discard') + ' ' + p.discard.length })];
  }
  function renderBars() {
    const me = ctrl(), opp = other(me);
    const fill = (id, slot, title) => { const b = $(id); b.textContent = ''; bar(slot, title).forEach((n) => b.append(n)); };
    fill('oppBar', opp, users[opp] || BCG.t('arena.opponent')); fill('meBar', me, users[me] || BCG.t('arena.you'));
  }

  function renderBoard() {
    const board = $('board'); board.textContent = '';
    const flip = view.mode !== 'debug' && view.you === 'A';
    const hl = highlights(); const mySel = selection(); const oppSel = view.players[other(ctrl())].selection;
    for (let dy = 0; dy < 5; dy++) {
      const y = flip ? 4 - dy : dy;
      for (let x = 0; x < 5; x++) {
        const cell = BCG.el('div', { class: 'cell ' + (hl[x + ',' + y] || '') });
        cell.dataset.x = x; cell.dataset.y = y;
        const c = cardAt(x, y);
        if (c) {
          cell.append(BCG.renderCard(c));
          if (mySel && mySel.zone === 'board' && mySel.uid === c.uid) cell.classList.add('sel');
          if (oppSel && oppSel.zone === 'board' && oppSel.uid === c.uid) cell.classList.add('opp-sel');
          cell.addEventListener('mouseenter', () => inspect(c));
        }
        cell.addEventListener('click', () => onCell(x, y));
        board.append(cell);
      }
    }
  }

  function renderHand() {
    const me = ctrl(), hand = $('hand'); hand.textContent = ''; const sel = selection();
    view.players[me].hand.forEach((c) => {
      const el = BCG.renderCard(c);
      if (sel && sel.zone === 'hand' && sel.uid === c.uid) el.classList.add('sel');
      el.addEventListener('click', () => { if (!isMyTurn()) return; cmd({ type: 'select', uid: sel && sel.uid === c.uid ? null : c.uid }); });
      el.addEventListener('mouseenter', () => inspect(c));
      hand.append(el);
    });
  }

  // ------------------------------------------------------------------ interação
  function onCell(x, y) {
    if (!view || view.phase !== 'ACTION') return;
    if (!isMyTurn()) { BCG.toast(BCG.t('err.not_your_turn'), 'error'); return; }
    const me = ctrl(), card = cardAt(x, y), sel = selection();
    if (pendingSkill) {
      if (card && card.owner !== me && !card.is_avatar && card.face_up) cmd({ type: 'use_skill', uid: pendingSkill.uid, slot: pendingSkill.slot, target: { x, y } });
      pendingSkill = null; render(); return;
    }
    if (sel && sel.zone === 'hand') {
      const av = avatarOf(me);
      if (neighbors(av.x, av.y, true).includes(x + ',' + y)) { cmd({ type: 'summon', uid: sel.uid, x, y, face_up: $('faceUp').checked }); return; }
    }
    if (sel && sel.zone === 'board') {
      const sc = byUid(sel.uid);
      if (sc && neighbors(sc.x, sc.y, false).includes(x + ',' + y)) {
        if (sc.is_avatar && (!card || card.owner === me)) {
          if (card && !window.confirm(BCG.t('arena.confirm_destroy'))) return;
          cmd({ type: 'walk_avatar', x, y }); return;
        }
        if (!sc.is_avatar && (!card || card.owner !== me)) { cmd({ type: 'move', uid: sc.uid, x, y }); return; }
      }
    }
    if (card && card.owner === me) {
      if (sel && sel.uid === card.uid) {
        if (!card.is_avatar && card.skills && card.skills.length) openSkills(card); else cmd({ type: 'select', uid: null });
      } else cmd({ type: 'select', uid: card.uid });
    }
  }

  function openSkills(card) {
    const list = $('skillList'); list.textContent = '';
    card.skills.forEach((s) => {
      const name = BCG.messages['skill.' + s.key + '.name'] || s.name;
      list.append(BCG.el('button', { class: 'btn', text: name + ' — ' + BCG.t('arena.skill_cost', { n: s.manacost }) + ' — ' + BCG.t(s.txt_key), onclick: () => {
        $('skillPopup').hidden = true;
        if (s.key === 'fire_ball') { pendingSkill = { uid: card.uid, slot: s.slot }; BCG.toast(BCG.t('arena.select_target')); render(); }
        else cmd({ type: 'use_skill', uid: card.uid, slot: s.slot, target: {} });
      } }));
    });
    $('skillPopup').hidden = false;
  }
  $('skillClose').addEventListener('click', () => { $('skillPopup').hidden = true; });
  $('endTurnBtn').addEventListener('click', () => cmd({ type: 'end_turn' }));
  $('doubleCastBtn').addEventListener('click', () => cmd({ type: 'double_cast' }));
  document.addEventListener('contextmenu', (ev) => {   // clique direito desmarca (O§3.3)
    if ($('arenaWrap').hidden) return;
    ev.preventDefault(); pendingSkill = null;
    if (view && isMyTurn() && selection()) cmd({ type: 'select', uid: null }); else if (view) render();
  });

  function showDiscard(slot) {
    $('discardTitle').textContent = BCG.t('arena.discard') + ' (' + slot + ')';
    const box = $('discardCards'); box.textContent = '';
    view.players[slot].discard.forEach((c) => box.append(BCG.renderCard(c, { mini: true })));
    $('discardModal').hidden = false;
  }
  $('discardMeBtn').addEventListener('click', () => view && showDiscard(ctrl()));
  $('discardOppBtn').addEventListener('click', () => view && showDiscard(other(ctrl())));
  $('discardClose').addEventListener('click', () => { $('discardModal').hidden = true; });

  function inspect(c) {
    const box = $('inspector'); box.textContent = ''; box.classList.remove('muted');
    if (c.is_avatar) { box.append(BCG.el('strong', { text: BCG.t('arena.avatar') + ' ' + c.owner })); return; }
    if (!c.name) { box.append(BCG.el('span', { class: 'muted', text: BCG.t('arena.face_down') })); return; }
    box.append(BCG.el('strong', { text: c.name + ' (#' + c.card_id + ')' }));
    box.append(BCG.el('div', { text: BCG.t('type.' + c.type) + ' · ' + (c.elements || []).map(BCG.elementName).join(', ') }));
    box.append(BCG.el('div', { text: BCG.t('arena.power') + ' ' + c.effective_power + ' (' + c.power + (c.power_bonus ? ' +' + c.power_bonus : '') + (c.damage ? ' −' + c.damage : '') + ') · ' + BCG.t('arena.shield') + ' ' + c.shield + ' · ' + BCG.t('arena.cost') + ' ' + c.mana_cost }));
    if ((c.mana_gains || []).length) box.append(BCG.el('div', { text: BCG.t('arena.mana_gain') + ': ' + c.mana_gains.map((g) => g.element + (g.value > 0 ? '+' : '') + g.value).join(' ') }));
    (c.skills || []).forEach((s) => box.append(BCG.el('div', { text: '• ' + (BCG.messages['skill.' + s.key + '.name'] || s.name) + ' (' + s.manacost + '): ' + BCG.t(s.txt_key) })));
  }

  // ------------------------------------------------------------------ timers e fim
  setInterval(() => {
    const now = Date.now() / 1000 - offset;
    if (!$('coinOverlay').hidden && coinDeadline) $('coinTimer').textContent = Math.max(0, Math.ceil(coinDeadline - now)) + 's';
    if (view && view.phase === 'ACTION') {
      const rem = Math.max(0, deadline - now), t = $('timer');
      t.textContent = Math.ceil(rem) + 's'; t.classList.toggle('warn', rem <= 15);
    }
  }, 250);

  function onEnd(d) {
    const r = d.result || {}; let title;
    if (r.type === 'draw') title = BCG.t('result.draw');
    else if (r.type === 'win') title = (view && view.mode === 'debug') ? BCG.t('result.winner', { p: r.winner }) : (r.winner === mySlotInMatch() ? BCG.t('result.win') : BCG.t('result.lose'));
    else title = BCG.t('result.aborted');
    $('resultTitle').textContent = title;
    const mine = (d.rewards || {})[mySlotInMatch()] || { battlepoints: 0, magicdust: 0 };
    $('resultText').textContent = (BCG.messages['result.reason.' + r.reason] || '') + ' · ' + BCG.t('result.bp', { n: mine.battlepoints }) + ' · ' + BCG.t('result.magicdust', { n: mine.magicdust });
    lastResult = d; $('coinOverlay').hidden = true; $('resultOverlay').hidden = false;
  }
  const mySlotInMatch = () => mySlot || (view && view.you) || 'A';
  $('resultClose').addEventListener('click', () => {
    $('resultOverlay').hidden = true; $('arenaWrap').hidden = true; $('roomPanel').hidden = false; view = null; pendingSkill = null;
    send({ type: 'sync' });
  });
})();
