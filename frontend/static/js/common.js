/* Utilidades comuns do frontend: API (CSRF), i18n, toasts, WebSocket com reconexão.
   Nunca usa innerHTML com dados de usuário (apenas textContent) para evitar XSS. */
(function () {
  const BCG = (window.BCG = { messages: {} });

  BCG.csrf = () => (document.querySelector('meta[name="csrf-token"]') || {}).content || '';

  BCG.t = function (key, params) {
    let s = BCG.messages[key];
    if (s === undefined) return key;
    if (params) for (const k in params) s = s.split('{' + k + '}').join(String(params[k]));
    return s;
  };

  BCG.applyI18n = function (root) {
    (root || document).querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = BCG.t(el.dataset.i18n); });
    (root || document).querySelectorAll('[data-i18n-placeholder]').forEach((el) => { el.placeholder = BCG.t(el.dataset.i18nPlaceholder); });
  };

  BCG.init = async function () {
    try {
      const r = await fetch('/api/i18n/', { credentials: 'same-origin' });
      BCG.messages = (await r.json()).messages || {};
    } catch (e) { /* segue com chaves cruas */ }
    BCG.applyI18n();
  };

  BCG.api = async function (method, url, body) {
    const opts = { method, credentials: 'same-origin', headers: { 'X-CSRFToken': BCG.csrf() } };
    if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    try {
      const r = await fetch(url, opts);
      const data = await r.json().catch(() => ({ ok: false, message: BCG.t('err.internal') }));
      data.status = r.status;
      if (r.status === 401 && !url.includes('/api/login/')) location.href = '/login/';
      return data;
    } catch (e) { return { ok: false, message: BCG.t('common.connection_lost'), status: 0 }; }
  };

  BCG.el = function (tag, attrs, children) {
    const el = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === 'class') el.className = attrs[k];
      else if (k === 'text') el.textContent = attrs[k];
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), attrs[k]);
      else el.setAttribute(k, attrs[k]);
    }
    (children || []).forEach((c) => el.append(c));
    return el;
  };

  BCG.toast = function (msg, kind) {
    const box = document.getElementById('toasts');
    if (!box) return;
    const el = BCG.el('div', { class: 'toast ' + (kind || ''), text: msg });
    box.append(el);
    setTimeout(() => el.remove(), 5000);
  };

  BCG.wsUrl = (path) => (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + path;

  /* WebSocket com reconexão exponencial. Códigos 4401/4403/4404/4000/1009 não reconectam. */
  BCG.connect = function (path, handlers) {
    let ws, delay = 1000, closed = false;
    const api = {
      send(obj) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj)); },
      close() { closed = true; if (ws) ws.close(); },
    };
    function open() {
      ws = new WebSocket(BCG.wsUrl(path));
      ws.onopen = () => { delay = 1000; if (handlers.open) handlers.open(); };
      ws.onmessage = (ev) => { let d; try { d = JSON.parse(ev.data); } catch (e) { return; } handlers.message(d); };
      ws.onclose = (ev) => {
        if (handlers.close) handlers.close(ev.code);
        if (closed || [4401, 4403, 4404, 4000, 1009].includes(ev.code)) return;
        setTimeout(open, delay); delay = Math.min(delay * 2, 10000);
      };
    }
    open();
    return api;
  };

  BCG.logout = async function () { await BCG.api('POST', '/api/logout/', {}); location.href = '/'; };
  BCG.time = () => new Date().toLocaleTimeString();
})();
