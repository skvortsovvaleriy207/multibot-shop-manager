
import sqlite3

def debug_cart():
    try:
        conn = sqlite3.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db")
        cursor = conn.cursor()
        
        print("--- All rows in cart_order ---")
        cursor.execute("SELECT * FROM cart_order")
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        print(f"Columns: {columns}")
        for row in rows:
            print(row)
            
        print("\n--- Rows with item_id=19 ---")
        cursor.execute("SELECT * FROM cart_order WHERE item_id=19")
        rows_19 = cursor.fetchall()
        for row in rows_19:
            print(row)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_cart()
