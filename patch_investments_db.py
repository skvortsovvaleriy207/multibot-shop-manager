import os
import glob

TARGET_DIR = "investmentsbot"
NEW_DB_PATH = 'DB_FILE'
IMPORT_STMT = 'from db import DB_FILE'

def patch_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        if 'bot_database.db' not in content:
            return False

        # Don't patch db.py itself (it defines DB_FILE)
        if filepath.endswith("db.py"):
            return False

        # Add import if missing
        if IMPORT_STMT not in content:
            # Try to insert after imports
            lines = content.splitlines()
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    last_import_idx = i
            
            lines.insert(last_import_idx + 1, IMPORT_STMT)
            content = "\n".join(lines)

        # Replace connection string
        # Handle "bot_database.db" (double quotes) and 'bot_database.db' (single quotes)
        content = content.replace('"bot_database.db"', 'DB_FILE')
        content = content.replace("'bot_database.db'", 'DB_FILE')

        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Patched {filepath}")
        return True
    except Exception as e:
        print(f"Error patching {filepath}: {e}")
        return False

def main():
    files = glob.glob(os.path.join(TARGET_DIR, "*.py"))
    for file in files:
        patch_file(file)

if __name__ == "__main__":
    main()
