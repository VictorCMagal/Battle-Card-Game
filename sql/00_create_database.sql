-- Cria o banco e o usuário do jogo (MySQL 8). EDITE a senha antes de executar.
-- Uso: mysql -u root -p < sql/00_create_database.sql
CREATE DATABASE IF NOT EXISTS battle_card_game CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'bcg_user'@'localhost' IDENTIFIED BY 'TROQUE_ESTA_SENHA';
GRANT ALL PRIVILEGES ON battle_card_game.* TO 'bcg_user'@'localhost';
-- Para a suíte de testes Django (cria banco "test_battle_card_game"):
GRANT ALL PRIVILEGES ON `test\_battle\_card\_game`.* TO 'bcg_user'@'localhost';
FLUSH PRIVILEGES;
