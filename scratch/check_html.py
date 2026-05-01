import os
import re

def check_html_tags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find open and close tags
    # This is not perfect but can catch simple mismatches
    tags = re.findall(r'<(/?[a-z1-6]+)', content.lower())
    
    stack = []
    void_tags = {'img', 'br', 'hr', 'input', 'link', 'meta', '!doctype'}
    
    for tag in tags:
        if tag.startswith('!'):
            continue
        if tag in void_tags:
            continue
        
        if tag.startswith('/'):
            if not stack:
                print(f"Unexpected close tag: <{tag}>")
            else:
                top = stack.pop()
                if top != tag[1:]:
                    print(f"Tag mismatch: opened <{top}>, closed <{tag}>")
        else:
            stack.append(tag)
    
    if stack:
        print(f"Unclosed tags: {stack}")
    else:
        print("HTML tags seem balanced (ignoring void tags).")

check_html_tags(r"d:\Projects\Library-project\templates\login.html")
