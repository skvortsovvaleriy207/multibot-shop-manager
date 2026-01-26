
import aiosqlite
import asyncio

from db import DB_FILE

async def clean_database():
    async with aiosqlite.connect(DB_FILE) as db:
        print("Starting database cleanup...")
        
        tables = [
            # Main User Data
            "users", "survey_answers", "user_bonuses", "referrals", "search_history",
            "user_activity", "user_activity_reports",
            
            # Content & Interactions
            "messages", "reviews", "showcase_messages",
            
            # Orders & Commerce
            "orders", "cart", "cart_order", "order_requests", "service_orders",
            
            # Application Settings
            "settings", "shop_sections",
            
            # Partners & Investors
            "auto_tech_partners", "auto_service_partners", "investors",
            
            # Catalog Items
            "auto_products", "auto_services",
            
            # Categories & Metadata (Product)
            "product_purposes", "product_types", "product_classes", 
            "product_views", "product_other_chars",
            
            # Categories & Metadata (Service)
            "service_purposes", "service_types", "service_classes", 
            "service_views", "service_other_chars",
            
            # Categories & Metadata (Offer)
            "offer_purposes", "offer_classes", "offer_types", 
            "offer_views", "offer_other_chars",
            
            # Core Categories
            "auto_categories", "categories"
            
        ]
        
        for table in tables:
            try:
                # Check if table exists first to avoid errors
                cursor = await db.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                result = await cursor.fetchone()
                
                if result:
                    await db.execute(f"DELETE FROM {table}")
                    # Reset auto-increment counters
                    await db.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    print(f"cleaned: {table}")
                else:
                    print(f"skip (not found): {table}")
                    
            except Exception as e:
                print(f"error clearing {table}: {e}")

        await db.commit()
        await db.execute("VACUUM")
        print("\nDatabase cleanup complete. VACUUM finished.")

if __name__ == "__main__":
    asyncio.run(clean_database())
