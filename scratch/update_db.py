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
        
        print("Dropping old constraint...")
        # We need to find the actual name or just try dropping the one from schema
        try:
            cursor.execute("ALTER TABLE transactions DROP FOREIGN KEY fk_transactions_book")
        except:
            print("Could not drop fk_transactions_book by name, trying to find it...")
            cursor.execute("""
                SELECT CONSTRAINT_NAME 
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_NAME = 'transactions' 
                AND COLUMN_NAME = 'book_id' 
                AND REFERENCED_TABLE_NAME = 'books'
            """)
            res = cursor.fetchone()
            if res:
                name = res[0]
                cursor.execute(f"ALTER TABLE transactions DROP FOREIGN KEY {name}")
        
        print("Adding new constraint with ON DELETE CASCADE...")
        cursor.execute("""
            ALTER TABLE transactions 
            ADD CONSTRAINT fk_transactions_book 
            FOREIGN KEY (book_id) REFERENCES books(id) 
            ON DELETE CASCADE
        """)
        
        conn.commit()
        print("Success! Database updated.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    update_db()
