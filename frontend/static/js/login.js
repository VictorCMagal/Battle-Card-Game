(async function () {
  await BCG.init();
  const form = document.getElementById('loginForm'), err = document.getElementById('loginError');
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault(); err.textContent = '';
    const r = await BCG.api('POST', '/api/login/', { name: form.name.value, password: form.password.value });
    if (r.ok) location.href = '/servidores/';
    else err.textContent = r.message || BCG.t('err.internal');
  });
})();
