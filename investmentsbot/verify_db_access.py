
import aiosqlite
import asyncio
import os
import sys

# Define path manually as assumed
DB_FILE = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db"

async def verify():
    print(f"Verifying DB at: {DB_FILE}")
    if not os.path.exists(DB_FILE):
        print("❌ DB FILE DOES NOT EXIST!")
        return

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            print("✅ Connected to DB")
            
            # Check users table
            try:
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                count = (await cursor.fetchone())[0]
                print(f"✅ Table 'users' exists. Count: {count}")
            except Exception as e:
                print(f"❌ Failed to query 'users' table: {e}")

            # Check orders table
            try:
                cursor = await db.execute("SELECT COUNT(*) FROM orders")
                count = (await cursor.fetchone())[0]
                print(f"✅ Table 'orders' exists. Count: {count}")
            except Exception as e:
                print(f"❌ Failed to query 'orders' table: {e}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
