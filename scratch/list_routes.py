from backend.app import app

def list_routes():
    print("Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.endpoint}")

if __name__ == "__main__":
    list_routes()
