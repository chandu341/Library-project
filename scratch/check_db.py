from backend.db import get_connection

def check():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        print("Checking book_requests table...")
        cursor.execute("DESCRIBE book_requests")
        for row in cursor.fetchall():
            print(row)
            
        print("\nChecking transactions table...")
        cursor.execute("DESCRIBE transactions")
        for row in cursor.fetchall():
            print(row)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    check()
