import sqlite3

USER_ID = 7254584539

def delete_all_active():
    db_path = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db"
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            
            # 1. Delete active Order Requests
            cursor.execute("""
                SELECT id, title, status FROM order_requests 
                WHERE user_id = ? AND status NOT IN ('approved', 'rejected', 'completed')
            """, (USER_ID,))
            requests = cursor.fetchall()
            
            if requests:
                print(f"Found {len(requests)} active requests: {requests}")
                cursor.execute("""
                    DELETE FROM order_requests 
                    WHERE user_id = ? AND status NOT IN ('approved', 'rejected', 'completed')
                """, (USER_ID,))
                print(f"✅ Deleted {cursor.rowcount} active requests.")
            else:
                print("No active requests found.")

            # 2. Delete active Orders (Buying)
            cursor.execute("""
                SELECT id, status FROM orders 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
            """, (USER_ID,))
            orders = cursor.fetchall()
            
            if orders:
                print(f"Found {len(orders)} active buying orders: {orders}")
                cursor.execute("""
                    DELETE FROM orders 
                    WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
                """, (USER_ID,))
                print(f"✅ Deleted {cursor.rowcount} active orders.")
            else:
                print("No active buying orders found.")

            db.commit()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_all_active()
