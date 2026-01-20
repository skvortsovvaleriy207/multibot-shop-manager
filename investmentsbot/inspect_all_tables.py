
import aiosqlite
import asyncio

DB_FILE = "bot_database.db"

async def inspect():
    async with aiosqlite.connect(DB_FILE) as db:
        print("--- All Table Counts ---")
        
        # Get all table names
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        
        for (table_name,) in tables:
            if table_name == "sqlite_sequence":
                continue
            try:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = (await cursor.fetchone())[0]
                print(f"{table_name}: {count}")
            except Exception as e:
                print(f"{table_name}: Error {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
