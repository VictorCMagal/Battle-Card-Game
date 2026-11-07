(async function () {
  await BCG.init();
  document.getElementById('logoutBtn').addEventListener('click', BCG.logout);
  const body = document.getElementById('serverRows');
  const r = await BCG.api('GET', '/api/servidores/');
  (r.servers || []).forEach((s) => {
    const btn = BCG.el('button', { class: 'btn primary', text: BCG.t('servers.enter'), onclick: () => {
      sessionStorage.setItem('bcg_server', String(s.id)); location.href = '/lobby/'; } });
    body.append(BCG.el('tr', {}, [
      BCG.el('td', { text: s.name }), BCG.el('td', { text: s.online ? BCG.t('index.online') : BCG.t('index.offline') }),
      BCG.el('td', { text: String(s.users_online) }), BCG.el('td', {}, [btn])]));
  });
})();
