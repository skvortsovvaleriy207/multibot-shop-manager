import aiosqlite
import asyncio
import os

DB_PATH = "../shared_storage/bot_database.db"

async def dump_db():
    if not os.path.exists(DB_PATH):
        print(f"File {DB_PATH} does not exist!")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        print(f"--- Users in {DB_PATH} ---")
        try:
            async with db.execute("SELECT user_id, username, survey_date, created_at, has_completed_survey FROM users") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    print(f"User: {row}")
        except Exception as e:
            print(f"Error reading users: {e}")

        print(f"\n--- Bonuses in {DB_PATH} ---")
        try:
            async with db.execute("SELECT * FROM user_bonuses") as cursor:
                 rows = await cursor.fetchall()
                 for row in rows:
                     print(f"Bonus: {row}")
        except Exception as e:
            print(f"Error reading bonuses: {e}")

if __name__ == "__main__":
    asyncio.run(dump_db())
