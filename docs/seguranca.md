# Segurança

* Senhas com hash do Django (PBKDF2); nunca em log (filtro `RedactFilter`). Login com limite de tentativas; sessão única por conta.
* Servidor autoritativo: o cliente pede ações; o servidor valida tudo e define o jogador do comando. Estado oculto não é enviado ao adversário.
* CSRF em todas as mutações HTTP; cookies HttpOnly/SameSite (Secure com `SECURE_COOKIES`). WebSocket: sessão + validação de Origin, limite de tamanho e taxa.
* XSS: o frontend usa `textContent` e não tem scripts/estilos inline; CSP restritiva (`apps/core/middleware.py`).
* SQL: apenas ORM parametrizado. Permissões por `acc_code`: painel só ADMIN/DEV; contas privilegiadas só DEV altera; RED não loga.
* Chat: 126 caracteres, controle removido, 5 msgs/5 s, persistência com campo `moderado` para moderação futura.
* Sorteios com `secrets.SystemRandom`. Segredos só no `.env` (fora do Git).
