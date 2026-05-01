from backend.app import get_connection

def check():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT SUM(total_quantity) as total FROM books")
        res = cursor.fetchone()
        print(f"SUM(total_quantity): {res['total']}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
