import re

FILE_PATH = "bestsocialbot/main.py"

def patch_main():
    with open(FILE_PATH, 'r') as f:
        content = f.read()

    # Import
    if "from db import init_db, DB_FILE" in content:
        content = content.replace("from db import init_db, DB_FILE", "from db import init_db, DB_FILE, SHARED_DB_FILE")

    content = content.replace("async with aiosqlite.connect(DB_FILE", "async with aiosqlite.connect(SHARED_DB_FILE")

    # Revert export function
    lines = content.splitlines()
    new_lines = []
    in_export = False
    
    for line in lines:
        if "async def export_to_google_sheets" in line:
            in_export = True
        if in_export and "async def " in line and "export_to_google_sheets" not in line:
            in_export = False
            
        if in_export and "async with aiosqlite.connect(SHARED_DB_FILE" in line:
            line = line.replace("SHARED_DB_FILE", "DB_FILE")
            
        new_lines.append(line)

    with open(FILE_PATH, 'w') as f:
        f.write("\n".join(new_lines))
    print("Patched bestsocialbot/main.py")

if __name__ == "__main__":
    patch_main()
