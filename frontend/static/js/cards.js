/* Renderização de cartas com placeholders CSS (substituíveis via assets/manifest.json). */
(function () {
  const BCG = window.BCG;
  BCG.ELEMENT_COLORS = { E: '#8d6e3b', S: '#7e57c2', F: '#e64a19', W: '#c62828', I: '#4fc3f7', A: '#90a4ae', M: '#78909c', U: '#6a1b9a', B: '#6d4c41' };
  BCG.catalog = {};
  BCG.manifest = { cards: {}, foil: {}, shiny: {} };

  BCG.loadCatalog = async function () {
    if (Object.keys(BCG.catalog).length) return;
    const r = await BCG.api('GET', '/api/cartas/');
    (r.cards || []).forEach((c) => { BCG.catalog[c.card_id] = c; });
    try { BCG.manifest = await (await fetch('/static/assets/manifest.json')).json(); } catch (e) { /* placeholders */ }
  };

  BCG.elementName = (e) => BCG.t('el.' + e);

  /* card: objeto de carta (do catálogo ou da view do jogo). opts.mini reduz detalhes. */
  BCG.renderCard = function (card, opts) {
    opts = opts || {};
    const el = BCG.el('div', { class: 'card' + (opts.mini ? ' mini' : '') });
    if (card.uid) el.dataset.uid = card.uid;
    if (card.is_avatar) {
      el.classList.add('avatar', 'owner-' + card.owner);
      el.append(BCG.el('div', { class: 'name', text: BCG.t('arena.avatar') + ' ' + card.owner }));
      return el;
    }
    if (card.face_up === false && !card.name) { el.classList.add('down', 'owner-' + card.owner); return el; }
    if (card.face_up === false) el.classList.add('down-mine');
    const first = (card.elements || [])[0];
    const color = BCG.ELEMENT_COLORS[first] || '#546e7a';
    const second = BCG.ELEMENT_COLORS[(card.elements || [])[1]] || color;
    el.style.background = 'linear-gradient(160deg,' + color + ',' + second + ' 70%, #1a2130)';
    const art = (BCG.manifest.cards || {})[card.card_id];
    if (art) { el.style.backgroundImage = 'url(/static/' + art + ')'; el.style.backgroundSize = 'cover'; }
    if (card.is_foil) el.classList.add('foil');
    if (card.is_shiny) el.classList.add('shiny');
    el.append(BCG.el('div', { class: 'name', text: card.name || '' }));
    if (!opts.mini) el.append(BCG.el('div', { class: 'els', text: (card.elements || []).join(' ') }));
    const eff = card.effective_power !== undefined ? card.effective_power : card.power;
    const cls = 'power' + ((card.damage || 0) > 0 ? ' hurt' : '') + ((card.power_bonus || 0) > 0 ? ' buff' : '');
    el.append(BCG.el('div', { class: cls, text: String(eff) }));
    el.append(BCG.el('div', { class: 'cost', text: String(card.mana_cost) }));
    if ((card.shield || 0) > 0) el.append(BCG.el('div', { class: 'shield', text: String(card.shield) }));
    if (card.card_id) el.dataset.cardId = card.card_id;
    return el;
  };
})();
