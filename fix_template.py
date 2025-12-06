
import os

path = r"c:\Users\Tn22\Downloads\PenoraWriter\templates\start_writing.html"
try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old = "        const userCredits = {{ credits }\n    };"
    new = "        const userCredits = {{ credits }};"

    if old in content:
        content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed successfully.")
    else:
        print("Pattern not found. Debugging:")
        search_term = "const userCredits"
        idx = content.find(search_term)
        if idx != -1:
            print("Found nearby content:")
            print(repr(content[idx:idx+50]))
        else:
            print("Could not find 'const userCredits' at all.")
            
except Exception as e:
    print(f"Error: {e}")
