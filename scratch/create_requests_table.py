import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def update_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "library_management")
        )
        cursor = conn.cursor()
        
        print("Creating book_requests table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                book_id INT NOT NULL,
                student_id INT NOT NULL,
                request_time DATETIME NOT NULL,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Success! book_requests table created.")
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    update_db()
