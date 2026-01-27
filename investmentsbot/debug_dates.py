import asyncio
import aiosqlite
from db import DB_FILE

async def check_dates():
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT user_id, survey_date, created_at FROM users LIMIT 10")
        rows = await cursor.fetchall()
        print(f"Found {len(rows)} users. Data:")
        for row in rows:
            print(f"User {row[0]}: survey_date='{row[1]}', created_at='{row[2]}'")

if __name__ == "__main__":
    asyncio.run(check_dates())