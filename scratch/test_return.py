import requests

def test_return():
    s = requests.Session()
    # Login as student
    s.post("http://127.0.0.1:5000/login", json={"username": "Ratna", "password": "password", "role": "student"})
    
    # Get transactions to find the one to return
    res = s.get("http://127.0.0.1:5000/transactions")
    data = res.json()
    trans = [t for t in data.get("transactions", []) if t["status"] == "issued"]
    
    print("Issued transactions:", len(trans))
    if trans:
        t_id = trans[0]["id"]
        print("Returning transaction ID:", t_id)
        res = s.post("http://127.0.0.1:5000/return", json={"transaction_id": t_id})
        print("Return status:", res.status_code)
        print("Return body:", res.text)

if __name__ == "__main__":
    test_return()
