import aiosqlite
import asyncio

async def check_categories():
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT category FROM order_requests 
            WHERE item_type = 'offer' AND category IS NOT NULL AND category != '' 
            AND status IN ('active', 'approved')
        """)
        categories = await cursor.fetchall()
        
        print(f"Found {len(categories)} categories.")
        for cat in categories:
            cat_name = cat[0]
            callback_data = f"property_cat_{cat_name}"
            byte_len = len(callback_data.encode('utf-8'))
            print(f"Category: '{cat_name}' | Callback Data: '{callback_data}' | Bytes: {byte_len}")
            if byte_len > 64:
                print(">>> EXCEEDS 64 BYTES!")

if __name__ == "__main__":
    asyncio.run(check_categories())
