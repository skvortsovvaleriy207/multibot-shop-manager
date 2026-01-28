
import aiosqlite
import asyncio

DB_FILE = "bot_database.db"

async def inspect():
    async with aiosqlite.connect(DB_FILE) as db:
        print("--- Table Counts ---")
        tables = [
            "users", "survey_answers", "showcase_messages", "user_bonuses", "settings",
            "auto_categories", "categories", "auto_products", "auto_services", "orders",
            "cart", "reviews", "messages", "auto_tech_partners", "auto_service_partners",
            "investors", "order_requests", "service_orders", "shop_sections"
        ]
        
        for table in tables:
            try:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                print(f"{table}: {count}")
            except Exception as e:
                print(f"{table}: Error {e}")

        print("\n--- Settings Table Content ---")
        try:
            async with db.execute("SELECT key, value FROM settings") as cursor:
                async for row in cursor:
                    print(f"{row[0]}: {row[1]}")
        except Exception as e:
            print(f"Error reading settings: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
