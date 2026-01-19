import sqlite3

def check_db():
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        
        print("--- Auto Categories ---")
        try:
            cursor.execute("SELECT * FROM auto_categories")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error querying auto_categories: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    check_db()
