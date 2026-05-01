import sys
import os
from jinja2 import Environment, FileSystemLoader

# Add the project root to sys.path
project_root = r"d:\Projects\Library-project"
sys.path.append(project_root)

# Mock stats
stats = {
    "total_books": 10,
    "total_students": 5,
    "books_issued": 3,
    "overdue_books": 1,
    "today_issued": 2,
    "today_returned": 1,
    "activities": [
        {"type": "issued", "title": "Test", "description": "Desc", "status": "On time"}
    ]
}

env = Environment(loader=FileSystemLoader(os.path.join(project_root, "templates")))

# Add url_for mock
def url_for(endpoint, **values):
    return f"/{endpoint}"

env.globals['url_for'] = url_for

try:
    template = env.get_template("login.html")
    print(template.render(stats=stats))
    print("SUCCESS: Template rendered correctly.")
except Exception as e:
    print(f"ERROR: {e}")
