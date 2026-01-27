import sqlite3
import os
from db import DB_FILE

DB_FILE = DB_FILE
USER_ID = 1138646732

def delete_user_data(user_id):
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        tables = [
            "users",
            "survey_answers",
            "user_bonuses",
            "auto_products",
            "auto_services",
            "orders",
            "cart",
            "reviews",
            "messages",
            "order_requests",
            "service_orders",
            "cart_order"
        ]
        
        print(f"Beginning deletion for User ID: {user_id}")
        
        total_deleted = 0
        for table in tables:
            try:
                # Check if table has user_id column first (optional safety, but we checked schema)
                # But for safety let's just run DELETE and catch error if no column
                # Actually, messages has sender_id and recipient_id, orders has seller_id too.
                
                if table == "messages":
                    cursor.execute(f"DELETE FROM {table} WHERE sender_id = ? OR recipient_id = ?", (user_id, user_id))
                elif table == "orders":
                    cursor.execute(f"DELETE FROM {table} WHERE user_id = ? OR seller_id = ?", (user_id, user_id))
                else:
                    cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                
                count = cursor.rowcount
                if count > 0:
                    print(f"Deleted {count} rows from {table}")
                    total_deleted += count
            except sqlite3.OperationalError as e:
                # Table might not exist or column might be different
                print(f"Skipping {table}: {e}")
                
        conn.commit()
        print(f"Deletion complete. Total rows deleted: {total_deleted}")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_user_data(USER_ID)