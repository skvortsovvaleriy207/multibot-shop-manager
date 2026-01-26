import sqlite3

def check_cart():
    try:
        conn = sqlite3.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db")
        cursor = conn.cursor()
        
        print("--- Cart Contents ---")
        try:
            cursor.execute("""
                SELECT user_id, count(*) 
                FROM cart_order 
                GROUP BY user_id
            """)
            rows = cursor.fetchall()
            if not rows:
                print("Cart is empty.")
            for row in rows:
                print(f"User ID: {row[0]}, Items: {row[1]}")
                
            print("\n--- Detailed Items for all users ---")
            cursor.execute("""
                SELECT user_id, item_type, item_id, quantity, price 
                FROM cart_order
            """)
            items = cursor.fetchall()
            for item in items:
                print(item)
                
        except Exception as e:
            print(f"Error querying cart_order: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    check_cart()
