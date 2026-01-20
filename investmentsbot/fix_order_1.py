
import sqlite3

def fix_db():
    try:
        with sqlite3.connect("bot_database.db") as db:
            print("Updating order 1 type to 'product'...")
            cursor = db.execute("UPDATE orders SET order_type = 'product' WHERE id = 1")
            print(f"Updated {cursor.rowcount} rows.")
            db.commit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_db()
