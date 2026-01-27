import sqlite3
from db import DB_FILE

def inspect():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("Columns in users table:")
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    inspect()