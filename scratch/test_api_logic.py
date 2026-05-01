import json
from backend.app import app, get_connection

def test_stats():
    # Mock a student session
    # We'll just call the logic manually
    with app.test_request_context():
        # Let's mock current_user for Ratna (ID 2)
        # In app.py, current_user() usually gets from session['user_id']
        # But we can just use the DB connection to test the query directly
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user_id = 2 # Ratna
        
        # Issued books count for this student
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE user_id = %s AND status = 'issued'", (user_id,))
        issued_count = cursor.fetchone()["count"]
        
        # Total books count in library
        cursor.execute("SELECT COUNT(*) as count FROM books")
        total_books = cursor.fetchone()["count"]
        
        # Total fine for this student
        cursor.execute("SELECT SUM(fine_amount) as fine FROM transactions WHERE user_id = %s", (user_id,))
        total_fine = cursor.fetchone()["fine"] or 0.0
        
        print(json.dumps({
            "issued_books_count": issued_count,
            "total_books": total_books,
            "total_fine": float(total_fine)
        }))
        conn.close()

if __name__ == "__main__":
    test_stats()
