import re

FILE_PATH = "investmentsbot/main.py"

def patch_main():
    with open(FILE_PATH, 'r') as f:
        content = f.read()

    # Function names that should use SHARED_DB_FILE
    # verify logic: 
    # check_blocked_user -> users table -> Shared
    # get_showcase_keyboard -> users table -> Shared
    # start_cmd -> users table -> Shared
    # send_user_notification -> users + messages table -> Shared
    # send_showcase -> showcase_messages -> Shared
    
    # Only export_to_google_sheets (line ~421) checks products/services. That should stay DB_FILE.
    
    # Strategy: Replace ALL, then revert export_to_google_sheets.
    content = content.replace("async with aiosqlite.connect(DB_FILE", "async with aiosqlite.connect(SHARED_DB_FILE")

    # Revert export function
    # Find the export function block and switch it back
    pattern = r"(async def export_to_google_sheets.*?async with aiosqlite.connect\()SHARED_DB_FILE(\).*?FROM auto_products)"
    # Regex is hard across lines. Use simple string replacement context.
    
    # We know export_to_google_sheets has "SELECT COUNT(*) FROM auto_products"
    # We can just iterate lines and switch back if inside that function.
    
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
    print("Patched main.py")

if __name__ == "__main__":
    patch_main()
