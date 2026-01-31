import asyncio
import aiosqlite
import os

# Path to the global database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'shared_storage', 'global_users.db'))

async def clear_users():
    """
    Clears all user data from the global database but PRESERVES legal documents.
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    print(f"🧹 Clearing users from {DB_PATH}...")
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # list of tables to clear
            tables_to_clear = [
                "user_subscriptions",
                "user_surveys",
                "global_users"
            ]
            
            for table in tables_to_clear:
                await db.execute(f"DELETE FROM {table}")
                print(f"   - Cleared table: {table}")
            
            await db.commit()
            
            # Verify legal docs are still there
            async with db.execute("SELECT COUNT(*) FROM legal_documents") as cursor:
                 count = (await cursor.fetchone())[0]
                 print(f"✅ Users cleared. Legal documents count: {count}")
                 
    except Exception as e:
        print(f"❌ Error clearing users: {e}")

if __name__ == "__main__":
    confirm = input(f"⚠️  WARNING: This will delete ALL user data from {DB_PATH}.\nType 'yes' to continue: ")
    if confirm.strip().lower() in ['yes', 'y']:
        asyncio.run(clear_users())
    else:
        print("Cancelled.")
