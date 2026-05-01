import requests

# Test the new PATCH endpoint
url = "http://127.0.0.1:5000/students/1/password"
try:
    # We don't have a session, so it should return 401, NOT 404
    res = requests.patch(url, json={"password": "newpassword123"})
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text}")
except Exception as e:
    print(f"Error: {e}")
