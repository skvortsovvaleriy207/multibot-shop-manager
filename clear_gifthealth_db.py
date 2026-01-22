import sqlite3
import os

DB_PATH = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/gifthealthbot/bot_database.db"

def clear_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Clearing ALL data from {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name != "sqlite_sequence": 
                print(f"Clearing table: {table_name}")
                cursor.execute(f"DELETE FROM {table_name}")
        
        conn.commit()
        print("All tables cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clear_db()
