import requests

def test_flow():
    s = requests.Session()
    # Login as Ratna (Student)
    res = s.post("http://127.0.0.1:5000/login", json={"username": "Ratna", "password": "password", "role": "student"})
    print("Login status:", res.status_code)
    
    # Try requesting a book
    res = s.post("http://127.0.0.1:5000/request-book", json={"book_id": 1})
    print("Request book status:", res.status_code)
    print("Request book body:", res.text)
    
    # Try getting transactions (student)
    res = s.get("http://127.0.0.1:5000/transactions")
    print("Transactions status:", res.status_code)
    print("Transactions body:", res.text[:100] + '...')

if __name__ == "__main__":
    test_flow()
