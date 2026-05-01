import requests

# Test the new POST endpoint
url = "http://127.0.0.1:5000/api/admin/reset-student-password"
try:
    # Still no session, so should return 401
    res = requests.post(url, json={"user_id": 1, "password": "newpassword123"})
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text}")
except Exception as e:
    print(f"Error: {e}")
