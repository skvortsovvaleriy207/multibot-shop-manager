
import sqlite3
from db import DB_FILE

def fix_cart_types():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        print("Checking for 'товар' entries in cart_order...")
        cursor.execute("SELECT COUNT(*) FROM cart_order WHERE item_type = 'товар'")
        count = cursor.fetchone()[0]
        print(f"Found {count} entries.")
        
        if count > 0:
            print("Updating 'товар' to 'order_request'...")
            cursor.execute("UPDATE cart_order SET item_type = 'order_request' WHERE item_type = 'товар'")
            conn.commit()
            print("Done.")
        else:
            print("No entries to fix.")
            
        print("Checking for 'product' entries in cart_order...")
        cursor.execute("SELECT COUNT(*) FROM cart_order WHERE item_type = 'product'")
        count = cursor.fetchone()[0]
        print(f"Found {count} entries.")

        if count > 0:
            print("Updating 'product' to 'order_request'...")
            cursor.execute("UPDATE cart_order SET item_type = 'order_request' WHERE item_type = 'product'")
            conn.commit()
            print("Done.")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_cart_types()