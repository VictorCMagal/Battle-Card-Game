(async function () {
  await BCG.init();
  const form = document.getElementById('registerForm');
  const hint = (n) => document.getElementById(n + 'Hint');
  const setHint = (n, msg, ok) => { const h = hint(n); h.textContent = msg || ''; h.className = 'hint ' + (ok ? 'ok' : 'error'); };
  let timer;

  // espelho das regras do servidor (accounts/rules.py); o servidor sempre revalida
  const validName = (v) => /^[A-Za-z0-9]{4,16}$/.test(v);
  const validPw = (v) => v.length >= 6 && v.length <= 32;
  const validEmail = (v) => { const i = v.indexOf('@'); return v.length > 3 && v.length <= 64 && i > 0 && v.indexOf('@', i + 1) < 0 && !/\s/.test(v) && /\.[^.]/.test(v.slice(i + 1)) && !v.endsWith('.'); };

  async function checkAvailability() {
    const q = new URLSearchParams();
    const name = form.name.value, email = form.email.value.trim();
    if (validName(name)) q.set('name', name);
    if (validEmail(email)) q.set('email', email);
    if (![...q.keys()].length) return;
    const r = await BCG.api('GET', '/api/contas/disponibilidade/?' + q.toString());
    if (!r.ok) return;
    if (r.name) setHint('name', r.name.available ? BCG.t('account.name_ok') : BCG.t('account.name_taken'), r.name.available);
    if (r.email) setHint('email', r.email.available ? BCG.t('account.email_ok') : BCG.t('account.email_taken'), r.email.available);
  }
  function local() {
    setHint('name', validName(form.name.value) || !form.name.value ? '' : BCG.t('err.name_chars') + ' (4–16)');
    setHint('password', validPw(form.password.value) || !form.password.value ? '' : BCG.t('err.password_length'));
    setHint('password2', !form.password2.value || form.password.value === form.password2.value ? '' : BCG.t('err.password_mismatch'));
    setHint('email', validEmail(form.email.value.trim()) || !form.email.value ? '' : BCG.t('err.email_format'));
    clearTimeout(timer); timer = setTimeout(checkAvailability, 400);
  }
  form.addEventListener('input', local);

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const body = { name: form.name.value, password: form.password.value, password2: form.password2.value, email: form.email.value.trim() };
    const r = await BCG.api('POST', '/api/contas/', body);
    if (r.ok) { BCG.toast(BCG.t('account.created'), 'ok'); setTimeout(() => { location.href = '/login/'; }, 900); return; }
    if (r.fields) for (const f in r.fields) setHint(f === 'password' ? 'password' : f, r.fields[f].map((e) => e.message).join(' '));
    else BCG.toast(r.message || BCG.t('err.internal'), 'error');
  });
})();
