# Pendências, limitações e suposições (leia antes de usar)

## O que foi (e não foi) executado no ambiente de desenvolvimento
* **Executado e aprovado:** 56 testes do motor (`engine/`) e das regras puras (validação de cadastro, esquema/CSV/JSON de cartas, deck inicial,
  recompensas, balanceamento das 100 cartas); compilação de todos os `.py`; verificação estática de nomes indefinidos/imports; `node --check` em todos os `.js`.
* **Escrito, mas NÃO executado** (sem Django, Channels, MySQL e internet): models, views, serviços, consumers, runtime, painel, templates, comandos de seed, scripts de setup,
  migrations, SQL de referência, testes `tests/django_tests/` e todo o frontend no navegador. Espere ajustes na primeira execução.
* **Migrations não foram geradas** (exigem Django). `scripts/setup.*` roda `makemigrations` e `migrate`; **versione os arquivos gerados** em `apps/*/migrations/`.
* **Versões de dependências** não foram verificadas: `requirements.txt` usa faixas (Django 5.2 LTS etc.).

## Suposições onde o original era omisso (confirmadas na Fase 1, exceto onde indicado)
* Carta invocada da mão que **não destrói** o alvo é descartada (texto de §3.3). *(Não confirmado explicitamente.)*
* Power de ataque = Power efetivo + Attack_Bonus; contra-ataque usa o Power bruto do alvo (configurável em `engine/constants.py`).
* Auto-encerramento do turno usa uma heurística conservadora (`Game._exhausted`).
* `acc_status` fica 1 após a criação do deck inicial; valores 2 e 3, PIN e verificação de e-mail não têm fluxo (P§11).
* Premium (slots 4–6): apenas bloqueio/liberação por `premium_check`; sem compra.

## Diferenças em relação ao plano da Fase 1
* Salas existem só em memória (sem tabela espelho `Sala`); o histórico da partida é gravado **ao final** (uma queda do servidor perde o histórico da partida em curso).
* Chat privado e convites usam a mesma conexão do lobby (`/ws/lobby/`), sem rota própria.
* Apps agrupados: presença, i18n e páginas ficam em `apps/core`; monitoramento dentro de `apps/painel` + `game.runtime`.
* Importação de cartas e painel funcionam por formulários simples; sem testes de interface.
* Acessibilidade e responsividade são básicas (foco, `aria-live`, grid adaptável), sem auditoria.
* Argon2 não é instalado (PBKDF2 padrão do Django).

## Limitações de projeto (documentadas)
* Estado de partidas em memória e por processo; reiniciar encerra partidas. Para vários processos seria preciso estado compartilhado.
* Não há aquisição de cartas, loja, ranking público nem NPC (apenas a arquitetura para NPC/IA).
