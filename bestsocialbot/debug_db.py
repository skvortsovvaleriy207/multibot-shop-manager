import aiosqlite
import asyncio

async def main():
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        print("--- CART ---")
        async with db.execute("SELECT * FROM cart WHERE user_id = 1138646732") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                print("Cart is empty")
            for row in rows:
                print(row)
        
        print("\n--- CART_ORDER ---")
        async with db.execute("SELECT * FROM cart_order WHERE user_id = 1138646732") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                print("Cart order is empty")
            for row in rows:
                print(row)
                
        print("\n--- PRODUCTS ---")
        async with db.execute("SELECT * FROM auto_products") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                print("No products found")
            for row in rows:
                print(row)

        print("\n--- USERS with PRODUCTS ---")
        async with db.execute("SELECT u.user_id, u.username FROM users u JOIN auto_products ap ON u.user_id = ap.user_id") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                print("No users joined with products")
            for row in rows:
                print(row)

if __name__ == "__main__":
    asyncio.run(main())
