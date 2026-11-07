# Dependências

Faixas em `requirements.txt` (não foi possível instalar/verificar versões exatas no ambiente de desenvolvimento): Django 5.2.x (LTS),
channels 4.2+, daphne 4.1+, mysqlclient 2.2+, django-environ, whitenoise. Opcional: channels-redis.
Após o primeiro `setup` bem-sucedido rode `pip freeze > requirements.lock` e versione o resultado. Sem dependências de frontend (JS/CSS puros, sem CDN).
MySQL 8.x (testado em desenho com 8.4 LTS). `CheckConstraint(condition=...)` exige Django ≥ 5.1.
