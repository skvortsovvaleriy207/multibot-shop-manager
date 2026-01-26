import aiosqlite
from db import DB_FILE
import asyncio

async def check_categories():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT * FROM categories") as cursor:
            rows = await cursor.fetchall()
            print(f"Total categories: {len(rows)}")
            for row in rows:
                print(row)

if __name__ == "__main__":
    asyncio.run(check_categories())
