
import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from google_sheets import sync_with_google_sheets
from db import init_db
import aiosqlite

logging.basicConfig(level=logging.INFO)

async def check_user(user_id):
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            print(f"User {user_id}: Name={row[7]}, Email={row[10]}, Phone={row[11]}, SurveyCompleted={row[4]}")
        else:
            print(f"User {user_id} not found in DB")

async def main():
    print("Checking DB before sync...")
    # User ID from the conversation metadata/images: 1138646732
    user_id = 1138646732
    await check_user(user_id)

    print("\nRunning sync_with_google_sheets...")
    changes = await sync_with_google_sheets()
    
    print(f"\nSync finished. Changes detected: {changes}")
    
    print("\nChecking DB after sync...")
    await check_user(user_id)

if __name__ == "__main__":
    asyncio.run(main())
