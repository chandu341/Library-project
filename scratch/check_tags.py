import os

def check_tags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tags = {
        '{%': '%}',
        '{{': '}}',
        '{#': '#}'
    }
    
    for start, end in tags.items():
        start_count = content.count(start)
        end_count = content.count(end)
        if start_count != end_count:
            print(f"UNBALANCED JINJA TAGS in {filepath}: {start} ({start_count}) vs {end} ({end_count})")
        else:
            print(f"Jinja tags balanced in {filepath} for {start}")

check_tags(r"d:\Projects\Library-project\templates\login.html")
