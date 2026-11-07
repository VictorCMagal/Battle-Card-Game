# Manutenção

* **Logs:** `logs/{django,ws,match,app}.log` (5 MB × 5). Erros recentes aparecem no painel/monitor.
* **Chat:** retenção `CHAT_RETENTION_DAYS`; botão "Apagar mensagens antigas" no painel (Configurações).
* **Cartas:** painel → Cartas (CRUD/importar/exportar). Alterações invalidam o cache; partidas em andamento mantêm o catálogo com que começaram.
* **Novo idioma:** copie `locale/pt_BR/messages.json` para `locale/<xx_XX>/` e defina `IDIOMA`.
* **Nova skill:** classe em `engine/skills.py` (`@register("chave")`) + `Carta_Skill` + texto `skill.<chave>.txt`.
* **Nova combinação:** painel/Django Admin → Combinacao (sem código).
* **Backup:** `mysqldump battle_card_game`. Reiniciar o servidor encerra as partidas em andamento.
* **Migrations:** após alterar modelos, `python manage.py makemigrations && migrate` e versione os arquivos.
