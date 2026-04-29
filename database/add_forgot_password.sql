USE library_management;

ALTER TABLE users
  ADD COLUMN email VARCHAR(160) NULL UNIQUE AFTER username;

UPDATE users SET email = 'chanduv4321@gmail.com' WHERE username = 'Chandu';
UPDATE users SET email = 'jatlaratnakumari2@gmail.com' WHERE username = 'Ratna';
UPDATE users SET email = 'pannu@gmail.com' WHERE username = 'Pannu';
UPDATE users SET email = 'karuna@gmail.com' WHERE username = 'Karuna';
UPDATE users SET email = 'satya@gmail.com' WHERE username = 'Satya';

ALTER TABLE users
  MODIFY email VARCHAR(160) NOT NULL;

CREATE TABLE IF NOT EXISTS password_resets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  code_hash VARCHAR(255) NOT NULL,
  expires_at DATETIME NOT NULL,
  used BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_password_resets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
