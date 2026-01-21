import sqlite3
import os

USER_ID = 7254584539
DB_PATH = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/investmentsbot/bot_database.db"

def delete_user():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Deleting user {USER_ID} from {DB_PATH} using sqlite3...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Delete from users
        cursor.execute("DELETE FROM users WHERE user_id = ?", (USER_ID,))
        print(f"Deleted from users: {cursor.rowcount} rows")
        
        # Delete from survey_answers
        cursor.execute("DELETE FROM survey_answers WHERE user_id = ?", (USER_ID,))
        print(f"Deleted from survey_answers: {cursor.rowcount} rows")
        
        # Delete from user_bonuses
        cursor.execute("DELETE FROM user_bonuses WHERE user_id = ?", (USER_ID,))
        print(f"Deleted from user_bonuses: {cursor.rowcount} rows")
        
        conn.commit()
        print("Deletion complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    delete_user()
