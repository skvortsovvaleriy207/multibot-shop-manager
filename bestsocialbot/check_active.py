import sqlite3
import sys

def check_active_processes(user_id):
    print(f"Checking for user {user_id}...")
    try:
        conn = sqlite3.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db")
        cursor = conn.cursor()
        
        print("\n--- Order Requests (NOT approved/rejected) ---")
        cursor.execute("""
            SELECT id, title, status, created_at 
            FROM order_requests 
            WHERE user_id = ? AND status NOT IN ('approved', 'rejected')
        """, (user_id,))
        requests = cursor.fetchall()
        for r in requests:
            print(f"Request ID: {r[0]}, Title: {r[1]}, Status: {r[2]}, Date: {r[3]}")

        print("\n--- Orders (NOT completed/cancelled/rejected) ---")
        cursor.execute("""
            SELECT id, item_id, status, order_date 
            FROM orders 
            WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
        """, (user_id,))
        orders = cursor.fetchall()
        for o in orders:
            print(f"Order ID: {o[0]}, Item ID: {o[1]}, Status: {o[2]}, Date: {o[3]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_active_processes(7254584539)
