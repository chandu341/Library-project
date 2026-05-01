import requests

def test_admin_flow():
    s = requests.Session()
    # Login as Admin
    res = s.post("http://127.0.0.1:5000/login", json={"username": "Chandu", "password": "password", "role": "admin"})
    print("Admin login status:", res.status_code)
    
    # Get requests
    res = s.get("http://127.0.0.1:5000/admin/requests")
    print("Admin requests status:", res.status_code)
    try:
        data = res.json()
        reqs = data.get("requests", [])
        print("Pending requests count:", len(reqs))
        if reqs:
            req_id = reqs[0]["id"]
            # Approve it
            res = s.post("http://127.0.0.1:5000/approve-request", json={"request_id": req_id})
            print("Approve status:", res.status_code)
            print("Approve body:", res.text)
    except Exception as e:
        print("Error parsing requests:", e)

if __name__ == "__main__":
    test_admin_flow()
