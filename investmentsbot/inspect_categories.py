import aiosqlite
import asyncio

async def inspect_db():
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        print("--- Product Purposes ---")
        async with db.execute("SELECT name FROM product_purposes") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(row[0])
        
        print("\n--- Service Purposes ---")
        async with db.execute("SELECT name FROM service_purposes") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(row[0])

        print("\n--- Property Purposes ---")
        async with db.execute("SELECT name FROM property_purposes") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(row[0])

if __name__ == "__main__":
    asyncio.run(inspect_db())
