
import sqlite3
from db import DB_FILE

def inspect_users():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        print("--- USERS TABLE CONTENT ---")
        cursor.execute("SELECT user_id, username, full_name, user_status FROM users")
        rows = cursor.fetchall()
        
        if not rows:
            print("Table 'users' is empty.")
        else:
            for row in rows:
                print(f"Info: {row}")
                print(f"ID Type: {type(row[0])}")
                
        print("\n--- SCHEMA INFO ---")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_users()