import sqlite3
from db import DB_FILE

def delete_order():
    db_path = DB_FILE
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            # Check if it exists first
            cursor.execute("SELECT * FROM order_requests WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                print("Order #1 not found.")
                return

            print(f"Found order: {row}")
            # Delete it
            cursor.execute("DELETE FROM order_requests WHERE id = 1")
            db.commit()
            print("✅ Order #1 deleted successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_order()