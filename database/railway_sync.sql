-- RUN THIS ON RAILWAY DATABASE TO SYNC SCHEMA
USE library_management;

-- 1. Ensure book_requests table exists with 'cancelled' status
CREATE TABLE IF NOT EXISTS book_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  book_id INT NOT NULL,
  student_id INT NOT NULL,
  request_time DATETIME NOT NULL,
  status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
  rejection_reason VARCHAR(255),
  FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. Update status column to include 'cancelled' if it already exists
ALTER TABLE book_requests MODIFY COLUMN status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending';

-- 3. Ensure books table has the correct quantity columns
ALTER TABLE books MODIFY COLUMN total_quantity INT NOT NULL DEFAULT 1;
ALTER TABLE books MODIFY COLUMN available_quantity INT NOT NULL DEFAULT 1;
