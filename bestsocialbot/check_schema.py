
import sqlite3
from db import DB_FILE

def check_schema():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    print("Users Schema:", cursor.fetchone()[0])
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_bonuses'")
    print("User Bonuses Schema:", cursor.fetchone()[0])

    conn.close()

if __name__ == "__main__":
    check_schema()