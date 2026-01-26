
import sqlite3

def check_schema():
    conn = sqlite3.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    print("Users Schema:", cursor.fetchone()[0])
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_bonuses'")
    print("User Bonuses Schema:", cursor.fetchone()[0])

    conn.close()

if __name__ == "__main__":
    check_schema()
