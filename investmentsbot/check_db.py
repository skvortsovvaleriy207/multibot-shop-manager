import asyncio
import aiosqlite

async def run():
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        c1 = await db.execute('SELECT COUNT(*) FROM auto_products')
        print('auto_products:', (await c1.fetchone())[0])
        
        c2 = await db.execute('SELECT COUNT(*) FROM auto_services')
        print('auto_services:', (await c2.fetchone())[0])
        
        c3 = await db.execute("SELECT COUNT(*) FROM order_requests WHERE item_type='product'")
        print('requests_product:', (await c3.fetchone())[0])
        
        c4 = await db.execute("SELECT COUNT(*) FROM order_requests WHERE item_type='service'")
        print('requests_service:', (await c4.fetchone())[0])
        
        c5 = await db.execute("SELECT COUNT(*) FROM order_requests WHERE item_type='offer'")
        print('requests_offer:', (await c5.fetchone())[0])

asyncio.run(run())
