import requests

def test():
    s = requests.Session()
    # 1. Login as a student (assuming student1 exists, or we just try to login)
    login_data = {"username": "student", "password": "password", "role": "student"}
    # Actually let's try just the endpoint first.
    # If we get a 401, it should be JSON!
    try:
        r = s.post('http://127.0.0.1:5000/request-book', json={'book_id': 1})
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
        print(f"Text: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test()
