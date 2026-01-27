
import asyncio
import aiosqlite
from db import DB_FILE

async def check_db():
    async with aiosqlite.connect(DB_FILE) as db:
        print('--- Product Purposes Table ---')
        try:
            async with db.execute('SELECT * FROM product_purposes') as cursor:
                rows = await cursor.fetchall()
                if not rows:
                     print("Table is empty")
                for row in rows:
                    print(row)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())