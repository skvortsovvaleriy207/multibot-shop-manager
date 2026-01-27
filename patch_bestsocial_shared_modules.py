import os

TARGET_FILES = [
    "bestsocialbot/survey.py",
    "bestsocialbot/referral_system.py",
    "bestsocialbot/payment_info.py",
    "bestsocialbot/user_interface.py"
]

IMPORT_ADD = "from db import SHARED_DB_FILE"

def patch_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} (not found)")
        return

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        if "from db import SHARED_DB_FILE" not in content:
             content = content.replace("from db import DB_FILE", "from db import DB_FILE, SHARED_DB_FILE")

        content = content.replace("aiosqlite.connect(DB_FILE)", "aiosqlite.connect(SHARED_DB_FILE)")
        content = content.replace("aiosqlite.connect(DB_FILE,", "aiosqlite.connect(SHARED_DB_FILE,")

        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Switched {filepath} to SHARED_DB_FILE")
    except Exception as e:
        print(f"Error patching {filepath}: {e}")

if __name__ == "__main__":
    for f in TARGET_FILES:
        patch_file(f)
