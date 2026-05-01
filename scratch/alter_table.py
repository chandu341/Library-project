import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Udnahc@0210',
    database='library_management'
)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE book_requests MODIFY COLUMN status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending'")
    conn.commit()
    print("Table altered successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()
