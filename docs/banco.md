# Banco de dados

Fonte oficial: migrations do Django (geradas por `makemigrations`; ver `docs/pendencias.md`). Referência: `sql/10_schema_reference.sql`.
Diagrama: `docs/diagrams/banco_er.mmd`. Charset `utf8mb4`.

| Tabela | Observações |
|---|---|
| `Conta` | colunas do original (`acc_password`=hash, `login_datatime`, `Selected_Deck`, `deck_1..6_id`, `grimorium_id`, `cur_*`). Desvios autorizados: senha VARCHAR(128) (hash), e-mail VARCHAR(64), `acc_pin` anulável, `codigo_id` gerado |
| `Deck`, `Deck_Carta` | uma linha por **cópia** (`card_uid` único). Limites 40 e 3 cópias/deck validados em serviço, em transação |
| `Grimorium`, `Grimorium_Carta` | máx. 500, sem cartas nulas/inexistentes (FK) |
| `Carta`, `Carta_Elemento`, `Carta_ManaGain`, `Carta_Skill`, `Combinacao` | catálogo (Card_ID ≥ 1 por CHECK) |
| `Historico_Partida`, `Historico_Evento` | cabeçalho + eventos com `seq` único por partida |
| `Chat_Mensagem`, `Servidor`, `Config_Servidor` | chat (retenção configurável), servidores, configurações |

Regras: inventário da conta = cartas em Decks + Grimorium; cada cópia está em um único lugar. Foil/Shiny são por cópia e
nunca aparecem nas cartas iniciais. Dados de cartas **não** ficam no código: vêm de `seeds/cards.json` (gerado por `seeds/generate_cards.py`).
