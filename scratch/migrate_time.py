import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def migrate_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "library_management")
        )
        cursor = conn.cursor()
        
        print("Migrating transactions table to DATETIME...")
        cursor.execute("ALTER TABLE transactions MODIFY issue_date DATETIME NOT NULL")
        cursor.execute("ALTER TABLE transactions MODIFY due_date DATETIME NOT NULL")
        cursor.execute("ALTER TABLE transactions MODIFY return_date DATETIME")
        
        conn.commit()
        print("Success! Database columns updated to DATETIME.")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    migrate_db()
