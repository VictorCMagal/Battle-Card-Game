-- REFERÊNCIA do esquema (documentação). A fonte oficial são as migrations do Django
-- (python manage.py makemigrations/migrate). Este arquivo espelha os modelos para consulta
-- e para DBAs. Não execute sobre um banco já migrado.
SET NAMES utf8mb4;

CREATE TABLE Servidor (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(32) NOT NULL UNIQUE, active TINYINT(1) NOT NULL);
CREATE TABLE Config_Servidor (id BIGINT AUTO_INCREMENT PRIMARY KEY, `key` VARCHAR(64) NOT NULL UNIQUE, `value` VARCHAR(255) NOT NULL);

CREATE TABLE Conta (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  codigo_id INT NOT NULL UNIQUE,
  acc_status SMALLINT NOT NULL DEFAULT 0,
  name VARCHAR(16) NOT NULL UNIQUE,
  email VARCHAR(64) NOT NULL UNIQUE,
  birth_datatime DATETIME(6) NULL,
  acc_password VARCHAR(128) NOT NULL,          -- HASH do Django (D-01)
  login_datatime DATETIME(6) NULL,
  acc_pin VARCHAR(128) NULL,                   -- sem fluxo de PIN no MVP
  acc_score INT NOT NULL DEFAULT 0,
  acc_code VARCHAR(5) NOT NULL DEFAULT 'GREEN', -- DEV, ADMIN, GRAY, GREEN, RED
  victory_counts INT NOT NULL DEFAULT 0,
  premium_check TINYINT(1) NOT NULL DEFAULT 0,
  premium_score INT NULL,
  premium_datetime DATETIME(6) NULL,
  Selected_Deck SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  deck_1_id BIGINT NULL, deck_2_id BIGINT NULL, deck_3_id BIGINT NULL,
  deck_4_id BIGINT NULL, deck_5_id BIGINT NULL, deck_6_id BIGINT NULL,
  grimorium_id BIGINT NULL,
  cur_battlepoints INT NOT NULL DEFAULT 0,
  cur_magicdust INT NOT NULL DEFAULT 0,
  cur_cash INT NOT NULL DEFAULT 0,
  last_session_key VARCHAR(40) NULL,
  created_at DATETIME(6) NOT NULL
);

CREATE TABLE Carta (
  card_id INT UNSIGNED PRIMARY KEY, type VARCHAR(10) NOT NULL, name VARCHAR(64) NOT NULL,
  rarity VARCHAR(16) NOT NULL, power SMALLINT NOT NULL, power_bonus SMALLINT NOT NULL,
  attack_bonus SMALLINT NOT NULL, damage SMALLINT NOT NULL, shield SMALLINT NOT NULL, mana_cost SMALLINT NOT NULL,
  CONSTRAINT carta_card_id_gte_1 CHECK (card_id >= 1)         -- Card_ID 0 é inválido
);
CREATE TABLE Carta_Elemento (id BIGINT AUTO_INCREMENT PRIMARY KEY, carta_id INT UNSIGNED NOT NULL, slot SMALLINT UNSIGNED NOT NULL, element CHAR(1) NOT NULL,
  UNIQUE (carta_id, slot), FOREIGN KEY (carta_id) REFERENCES Carta(card_id) ON DELETE CASCADE);
CREATE TABLE Carta_ManaGain (id BIGINT AUTO_INCREMENT PRIMARY KEY, carta_id INT UNSIGNED NOT NULL, slot SMALLINT UNSIGNED NOT NULL, element CHAR(1) NOT NULL, `value` SMALLINT NOT NULL,
  UNIQUE (carta_id, slot), FOREIGN KEY (carta_id) REFERENCES Carta(card_id) ON DELETE CASCADE);
CREATE TABLE Carta_Skill (id BIGINT AUTO_INCREMENT PRIMARY KEY, carta_id INT UNSIGNED NOT NULL, slot SMALLINT UNSIGNED NOT NULL, name VARCHAR(32) NOT NULL,
  number VARCHAR(16) NOT NULL, manacost SMALLINT NOT NULL, txt_key VARCHAR(64) NOT NULL,
  UNIQUE (carta_id, slot), FOREIGN KEY (carta_id) REFERENCES Carta(card_id) ON DELETE CASCADE);
CREATE TABLE Combinacao (id BIGINT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(64) NOT NULL, ativo TINYINT(1) NOT NULL,
  block_card_id INT UNSIGNED NULL, block_element VARCHAR(1) NOT NULL, incoming_card_id INT UNSIGNED NULL, incoming_element VARCHAR(1) NOT NULL,
  effect_type VARCHAR(16) NOT NULL, effect_value INT NOT NULL);

CREATE TABLE Deck (id BIGINT AUTO_INCREMENT PRIMARY KEY, owner_id BIGINT NOT NULL, slot SMALLINT UNSIGNED NOT NULL, name VARCHAR(32) NOT NULL,
  created_at DATETIME(6) NOT NULL, UNIQUE (owner_id, slot), FOREIGN KEY (owner_id) REFERENCES Conta(id) ON DELETE CASCADE);
CREATE TABLE Deck_Carta (id BIGINT AUTO_INCREMENT PRIMARY KEY, card_uid CHAR(32) NOT NULL UNIQUE, deck_id BIGINT NOT NULL, carta_id INT UNSIGNED NOT NULL,
  is_foil TINYINT(1) NOT NULL, is_shiny TINYINT(1) NOT NULL, INDEX (deck_id, carta_id),
  FOREIGN KEY (deck_id) REFERENCES Deck(id) ON DELETE CASCADE, FOREIGN KEY (carta_id) REFERENCES Carta(card_id));
CREATE TABLE Grimorium (id BIGINT AUTO_INCREMENT PRIMARY KEY, owner_id BIGINT NOT NULL, FOREIGN KEY (owner_id) REFERENCES Conta(id) ON DELETE CASCADE);
CREATE TABLE Grimorium_Carta (id BIGINT AUTO_INCREMENT PRIMARY KEY, card_uid CHAR(32) NOT NULL UNIQUE, grimorium_id BIGINT NOT NULL, carta_id INT UNSIGNED NOT NULL,
  is_foil TINYINT(1) NOT NULL, is_shiny TINYINT(1) NOT NULL,
  FOREIGN KEY (grimorium_id) REFERENCES Grimorium(id) ON DELETE CASCADE, FOREIGN KEY (carta_id) REFERENCES Carta(card_id));

ALTER TABLE Conta
  ADD FOREIGN KEY (deck_1_id) REFERENCES Deck(id) ON DELETE SET NULL, ADD FOREIGN KEY (deck_2_id) REFERENCES Deck(id) ON DELETE SET NULL,
  ADD FOREIGN KEY (deck_3_id) REFERENCES Deck(id) ON DELETE SET NULL, ADD FOREIGN KEY (deck_4_id) REFERENCES Deck(id) ON DELETE SET NULL,
  ADD FOREIGN KEY (deck_5_id) REFERENCES Deck(id) ON DELETE SET NULL, ADD FOREIGN KEY (deck_6_id) REFERENCES Deck(id) ON DELETE SET NULL,
  ADD FOREIGN KEY (grimorium_id) REFERENCES Grimorium(id) ON DELETE SET NULL;

CREATE TABLE Historico_Partida (id BIGINT AUTO_INCREMENT PRIMARY KEY, servidor_id BIGINT NULL, modo VARCHAR(8) NOT NULL,
  jogador_a_id BIGINT NULL, jogador_b_id BIGINT NULL, iniciada_em DATETIME(6) NOT NULL, finalizada_em DATETIME(6) NULL,
  resultado VARCHAR(8) NOT NULL, vencedor VARCHAR(1) NOT NULL, motivo VARCHAR(16) NOT NULL, turnos INT UNSIGNED NOT NULL);
CREATE TABLE Historico_Evento (id BIGINT AUTO_INCREMENT PRIMARY KEY, partida_id BIGINT NOT NULL, seq INT UNSIGNED NOT NULL, turno INT UNSIGNED NOT NULL,
  jogador VARCHAR(1) NOT NULL, tipo VARCHAR(32) NOT NULL, payload JSON NOT NULL, criado_em DATETIME(6) NOT NULL,
  UNIQUE (partida_id, seq), FOREIGN KEY (partida_id) REFERENCES Historico_Partida(id) ON DELETE CASCADE);

CREATE TABLE Chat_Mensagem (id BIGINT AUTO_INCREMENT PRIMARY KEY, canal VARCHAR(40) NOT NULL, sender_id BIGINT NULL, sender_name VARCHAR(16) NOT NULL,
  texto VARCHAR(126) NOT NULL, criado_em DATETIME(6) NOT NULL, moderado TINYINT(1) NOT NULL, INDEX (canal));
