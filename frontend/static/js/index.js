(async function () {
  await BCG.init();
  const r = await BCG.api('GET', '/api/status/');
  document.getElementById('serverStatus').textContent = r.ok ? BCG.t('index.online') : BCG.t('index.offline');
  document.getElementById('usersOnline').textContent = r.ok ? r.users_online : '–';
})();
