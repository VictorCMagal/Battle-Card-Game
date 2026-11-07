(async function () {
  await BCG.init();
  await BCG.loadCatalog();
  const $ = (id) => document.getElementById(id);
  let data = null, current = 1;

  async function load() {
    const r = await BCG.api('GET', '/api/decks/');
    if (!r.ok) { BCG.toast(r.message, 'error'); return; }
    data = r; if (!data.slots.find((s) => s.slot === current)) current = data.selected || 1;
    render();
  }
  async function move(uid, kind, deckId) {
    const r = await BCG.api('POST', '/api/decks/mover/', { card_uid: uid, kind, deck_id: deckId });
    if (!r.ok) BCG.toast(r.message, 'error'); else load();
  }
  function cardNode(c, onClick) {
    const def = Object.assign({}, BCG.catalog[c.card_id] || { name: '#' + c.card_id, elements: [], power: 0, mana_cost: 0 }, { is_foil: c.is_foil, is_shiny: c.is_shiny });
    const el = BCG.renderCard(def, { mini: true });
    el.draggable = true; el.title = def.name + ' (#' + c.card_id + ')';
    el.addEventListener('click', onClick);
    el.addEventListener('dragstart', (ev) => ev.dataTransfer.setData('text/plain', c.card_uid));
    return el;
  }
  function dropZone(el, kind, deckId) {
    el.ondragover = (ev) => ev.preventDefault();
    el.ondrop = (ev) => { ev.preventDefault(); const uid = ev.dataTransfer.getData('text/plain'); if (uid) move(uid, kind, deckId); };
  }
  function render() {
    const tabs = $('slotTabs'); tabs.textContent = '';
    data.slots.forEach((s) => {
      const label = s.name || BCG.t('decks.slot', { n: s.slot });
      const b = BCG.el('button', { class: 'btn' + (s.slot === current ? ' primary' : ''), text: label + (s.slot === data.selected ? ' ★' : '') + (s.locked ? ' 🔒' : '') });
      if (s.locked) b.disabled = true;
      b.addEventListener('click', () => { current = s.slot; render(); });
      tabs.append(b);
    });
    const slot = data.slots.find((s) => s.slot === current);
    const box = $('deckCards'); box.textContent = '';
    $('selectDeckBtn').disabled = !slot.deck_id; $('renameBtn').disabled = !slot.deck_id;
    if (!slot.deck_id) {
      box.append(BCG.el('p', { class: 'muted', text: BCG.t('decks.empty') }));
      box.append(BCG.el('button', { class: 'btn primary', text: BCG.t('decks.create'), onclick: async () => {
        const r = await BCG.api('POST', '/api/decks/', { slot: current }); if (!r.ok) BCG.toast(r.message, 'error'); else load(); } }));
      $('deckCount').textContent = '';
    } else {
      $('deckCount').textContent = BCG.t('decks.count', { n: slot.count, max: data.deck_size });
      slot.cards.forEach((c) => box.append(cardNode(c, () => move(c.card_uid, 'grimorium'))));
      dropZone(box, 'deck', slot.deck_id);
    }
    const g = $('grimCards'); g.textContent = '';
    data.grimorium.cards.forEach((c) => g.append(cardNode(c, () => { if (slot.deck_id) move(c.card_uid, 'deck', slot.deck_id); })));
    $('grimCount').textContent = data.grimorium.count + '/' + data.grimorium.max;
    dropZone(g, 'grimorium');
  }
  $('selectDeckBtn').addEventListener('click', async () => {
    const r = await BCG.api('POST', '/api/decks/selecionar/', { slot: current });
    if (r.ok) { BCG.toast(BCG.t('decks.selected', { n: current }), 'ok'); load(); } else BCG.toast(r.message, 'error'); });
  $('renameBtn').addEventListener('click', async () => {
    const slot = data.slots.find((s) => s.slot === current); const name = window.prompt(BCG.t('decks.name_prompt'), slot.name || '');
    if (!name) return; const r = await BCG.api('PATCH', '/api/decks/' + slot.deck_id + '/', { name });
    if (!r.ok) BCG.toast(r.message, 'error'); else load(); });
  load();
})();
