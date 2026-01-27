import os

TARGET_FILES = [
    "investmentsbot/survey.py",
    "investmentsbot/referral_system.py",
    "investmentsbot/payment_info.py",
    "investmentsbot/marketing.py", # If exists, often user related
    "investmentsbot/user_interface.py" # Profile often here? No, main.py/shop.py usually.
]

IMPORT_ADD = "from db import SHARED_DB_FILE"

def patch_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} (not found)")
        return

    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Add import
        if "from db import SHARED_DB_FILE" not in content:
             content = content.replace("from db import DB_FILE", "from db import DB_FILE, SHARED_DB_FILE")

        # Replace connection
        # We replace (DB_FILE) with (SHARED_DB_FILE)
        # Note: We must be careful not to replace Shop logic if it's in the same file.
        # But these files (survey, referral) are almost exclusively User/Shared domains.
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
