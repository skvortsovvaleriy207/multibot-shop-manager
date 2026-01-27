import sqlite3
import os

DB_DIR = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/investmentsbot"
DB_FILE = os.path.join(DB_DIR, "bot_database.db")

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print(f"Checking database: {DB_FILE}")
    
    # Check users count
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"Total users count: {count}")
    
    if count > 0:
        cursor.execute("SELECT user_id, username, full_name, created_at FROM users LIMIT 5")
        users = cursor.fetchall()
        print("First 5 users:")
        for u in users:
            print(u)
    else:
        print("No users found.")
        
    conn.close()

except Exception as e:
    print(f"Error checking DB: {e}")
