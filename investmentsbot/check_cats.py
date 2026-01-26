import aiosqlite
import asyncio

async def check_categories():
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        async with db.execute("SELECT * FROM categories") as cursor:
            rows = await cursor.fetchall()
            print(f"Total categories: {len(rows)}")
            for row in rows:
                print(row)

if __name__ == "__main__":
    asyncio.run(check_categories())
