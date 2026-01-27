
import sqlite3
import os

PROJECT_ROOT = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager"
BOT_DIRS = [
    os.path.join(PROJECT_ROOT, "bestsocialbot"),
    os.path.join(PROJECT_ROOT, "investmentsbot")
]

TABLES_TO_RENAME = ["users", "user_bonuses", "survey_answers"]

def cleanup_bot(bot_path):
    print(f"Cleaning up {os.path.basename(bot_path)}...")
    db_file = os.path.join(bot_path, "bot_database.db")
    
    if not os.path.exists(db_file):
        print("  - No database found.")
        return

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        for table in TABLES_TO_RENAME:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                backup_name = f"{table}_old_backup"
                print(f"  - Renaming {table} -> {backup_name}")
                # Drop backup if exists (retry)
                cursor.execute(f"DROP TABLE IF EXISTS {backup_name}")
                cursor.execute(f"ALTER TABLE {table} RENAME TO {backup_name}")
            else:
                print(f"  - Table {table} not found (already cleaned?)")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  - Error: {e}")

if __name__ == "__main__":
    for bot_dir in BOT_DIRS:
        cleanup_bot(bot_dir)
