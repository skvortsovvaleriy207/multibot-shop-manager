
import sqlite3

def inspect():
    with sqlite3.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        print("--- ORDERS Table ---")
        cursor = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
        for row in cursor:
            print(row)

        print("\n--- ORDER_REQUESTS Table (ID 3) ---")
        cursor = db.execute("SELECT * FROM order_requests WHERE id = 3")
        row = cursor.fetchone()
        print(row)
        if row:
            print(f"Columns: {[d[0] for d in cursor.description]}")

        print("\n--- SERVICE_ORDERS Table (ID 3) ---")
        try:
            cursor = db.execute("SELECT * FROM service_orders WHERE id = 3")
            row = cursor.fetchone()
            print(row)
        except Exception as e:
            print(f"Error accessing service_orders: {e}")

if __name__ == "__main__":
    inspect()
