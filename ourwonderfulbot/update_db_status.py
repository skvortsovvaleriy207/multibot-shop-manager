import sqlite3
import os

DB_NAME = "bot_database.db"

def update_schema():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if user_status column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "user_status" not in columns:
        print("Adding user_status column...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN user_status TEXT DEFAULT ''")
            conn.commit()
            print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("Column user_status already exists.")
        
    conn.close()

if __name__ == "__main__":
    update_schema()
