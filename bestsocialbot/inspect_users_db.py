
import asyncio
import aiosqlite
import os

# Path to shared DB might be in shared_storage/shared_database.db or just shared_database.db depending on config
# Checking config or just trying common paths.
# Based on file list, shared_storage exists.
DB_PATH = "bestsocialbot/bot_database.db"
if not os.path.exists(DB_PATH):
    DB_PATH = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/bestsocialbot/bot_database.db"

async def inspect():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        print(f"Connected to {DB_PATH}")
        
        # Check users table schema (columns)
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        print("Columns in 'users' table:")
        for col in columns:
            print(f" - {col[1]} ({col[2]})")

        print("\n--- Tables Row Counts ---")
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = await cursor.fetchall()
        for table in tables:
            t_name = table[0]
            try:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {t_name}")
                count = await cursor.fetchone()
                print(f"Table '{t_name}': {count[0]} rows")
            except Exception as e:
                print(f"Table '{t_name}': Error {e}")
                
        print("\n--- Users Data ---")
        cursor = await db.execute("SELECT user_id, username, has_completed_survey FROM users")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, User: {row[1]}, SurveyDone: {row[2]}")

if __name__ == "__main__":
    asyncio.run(inspect())
