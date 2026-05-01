import requests
import json

def test_api():
    try:
        # We need a session cookie to test login-required APIs
        # But we can test /request-book (unauthenticated should give 401)
        resp = requests.post("http://127.0.0.1:5000/request-book", json={"book_id": 1})
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
