
import sqlite3

def check_schema():
    with sqlite3.connect("bot_database.db") as db:
        print("--- product_purposes ---")
        cursor = db.execute("PRAGMA table_info(product_purposes)")
        for col in cursor:
            print(col)
        
        print("\n--- service_purposes ---")
        cursor = db.execute("PRAGMA table_info(service_purposes)")
        for col in cursor:
            print(col)

        print("\n--- Rows sample ---")
        cursor = db.execute("SELECT rowid, * FROM product_purposes LIMIT 3")
        for row in cursor:
             print(f"Product: {row}")
             
        cursor = db.execute("SELECT rowid, * FROM service_purposes LIMIT 3")
        for row in cursor:
             print(f"Service: {row}")

if __name__ == "__main__":
    check_schema()
