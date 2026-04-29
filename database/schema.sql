CREATE DATABASE IF NOT EXISTS library_management;
USE library_management;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin', 'student') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(120) NOT NULL,
  author VARCHAR(120) NOT NULL,
  category VARCHAR(80) NOT NULL,
  total_quantity INT NOT NULL DEFAULT 1,
  available_quantity INT NOT NULL DEFAULT 1,
  shelf VARCHAR(40) NOT NULL,
  cover_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_books_title (title),
  CHECK (total_quantity >= 0),
  CHECK (available_quantity >= 0)
);

CREATE TABLE IF NOT EXISTS transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  book_id INT NOT NULL,
  issue_date DATE NOT NULL,
  due_date DATE NOT NULL,
  return_date DATE,
  status ENUM('issued', 'returned') NOT NULL DEFAULT 'issued',
  fine_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_transactions_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS password_resets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  code_hash VARCHAR(255) NOT NULL,
  expires_at DATETIME NOT NULL,
  used BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_password_resets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO users (name, username, email, password_hash, role) VALUES
('Chandu', 'Chandu', 'chanduv4321@gmail.com', 'scrypt:32768:8:1$ksr96qp8r8CJPkJI$eb255cd9ee0032d9ed0421f86f63b43b30c5b9b1fef5cae16c9ff86d3ea5a03866c031b8a7ab34fdb435c9aae21184bb77ce8e3cd8b0b374a56c86622ae02198', 'admin'),
('Ratna', 'Ratna', 'jatlaratnakumari2@gmail.com', 'scrypt:32768:8:1$jk6Q3fUqoNk4zead$5d4c2fdac93da25b9171a2ac9c20fd2b87e4d4da2d38bcdb874a41c64f75f7bd535e0b3a1da5278ae2c082de6cd68c72de1e2f7269fc33ed40804e00deca72d4', 'student'),
('Pannu', 'Pannu', 'pannu@gmail.com', 'scrypt:32768:8:1$HFEiB3AYIT9Txf8l$5f75b4a2e2d7249024093b76f3c2efd08ab85ab80d3d2bfe355ec822b2982274215c9014a76fe065af588899dc0cf6327769f596e3942fdfac81f63ae80aeb0f', 'student'),
('Karuna', 'Karuna', 'karuna@gmail.com', 'scrypt:32768:8:1$lilWYYJqVRaNSU1c$29de224bf31d62e49389163f3787560f5a14db1a0413767b2f5f2391a90eb9714f78067d218098320f6e903563999564041af8d43fe90006c18b2692c62e28ab', 'student'),
('Satya', 'Satya', 'satya@gmail.com', 'scrypt:32768:8:1$d3DwSpQV3CpXNCsn$1378d68c5d8637f9a01e20cd85013bf4806a4e63d73b95acc0f4b753056f295f8c0e127f79447c9259d076128964c20b9d5b1f9a2a9d60891ef93875605d5fd4', 'student')
ON DUPLICATE KEY UPDATE name = VALUES(name), email = VALUES(email), password_hash = VALUES(password_hash), role = VALUES(role);

INSERT INTO books (title, author, category, total_quantity, available_quantity, shelf, cover_url) VALUES
('Book 1', 'Author 1', 'General', 5, 5, 'A1', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=900&q=80'),
('Book 2', 'Author 2', 'Science', 4, 4, 'A2', 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=900&q=80'),
('Book 3', 'Author 3', 'History', 3, 3, 'B1', 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=900&q=80'),
('Book 4', 'Author 4', 'Computer', 6, 6, 'B2', 'https://images.unsplash.com/photo-1519682337058-a94d519337bc?auto=format&fit=crop&w=900&q=80'),
('Book 5', 'Author 5', 'Language', 2, 2, 'C1', 'https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?auto=format&fit=crop&w=900&q=80')
ON DUPLICATE KEY UPDATE title = VALUES(title);
