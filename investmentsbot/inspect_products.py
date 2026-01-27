import sqlite3
import os
from datetime import datetime
from db import DB_FILE

DB_FILE = DB_FILE

def inspect_products():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("--- TABLE: auto_products ---")
        try:
            cursor.execute("SELECT * FROM auto_products")
            products = cursor.fetchall()
            if not products:
                print("No products found in auto_products.")
            else:
                for p in products:
                    print(dict(p))
        except Exception as e:
            print(f"Error reading auto_products: {e}")

        print("\n--- TABLE: order_requests (Products only) ---")
        try:
            # Assuming there's a type or category column to distinguish products
            # Let's check all requests first to see what columns exist
            cursor.execute("PRAGMA table_info(order_requests)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'type' in columns:
                 cursor.execute("SELECT * FROM order_requests WHERE type='product'")
            else:
                 cursor.execute("SELECT * FROM order_requests") # Show all if no type column, or filter by logic later
            
            requests = cursor.fetchall()
            if not requests:
                print("No product requests found in order_requests.")
            else:
                for r in requests:
                    # Filter for 'product' type if we simply grabbed everything
                    if 'type' not in dict(r) or r['type'] == 'product' or r['request_type'] == 'product': 
                        print(dict(r))
        except Exception as e:
             print(f"Error reading order_requests: {e}")

        conn.close()

    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    inspect_products()