import aiosqlite
import asyncio

async def fix_database():
    print("Connecting to database...")
    async with aiosqlite.connect("bot_database.db") as db:
        print("Creating offer_purposes...")
        await db.execute("CREATE TABLE IF NOT EXISTS offer_purposes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        print("Creating offer_classes...")
        await db.execute("CREATE TABLE IF NOT EXISTS offer_classes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        print("Creating offer_types...")
        await db.execute("CREATE TABLE IF NOT EXISTS offer_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        print("Creating offer_views...")
        await db.execute("CREATE TABLE IF NOT EXISTS offer_views (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        print("Creating offer_other_chars...")
        await db.execute("CREATE TABLE IF NOT EXISTS offer_other_chars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        await db.commit()
    print("Database fix completed.")

if __name__ == "__main__":
    asyncio.run(fix_database())
