
import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from db import SHARED_DB_FILE, DB_FILE
from config import BOT_NAME

print(f"--- DB PATH CHECK FOR {BOT_NAME} ---")
print(f"CWD: {os.getcwd()}")
print(f"DB_FILE (Local): {DB_FILE} -> Absolute: {os.path.abspath(DB_FILE)}")
print(f"SHARED_DB_FILE: {SHARED_DB_FILE}")

import aiosqlite
import asyncio

async def inspect():
    db_path = SHARED_DB_FILE
    if not os.path.exists(db_path):
        print(f"ERROR: SHARED_DB_FILE does not exist at {db_path}")
    else:
        print(f"SHARED_DB_FILE exists. Size: {os.path.getsize(db_path)} bytes")
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            count = await cursor.fetchone()
            print(f"Users in SHARED DB: {count[0]}")

    local_path = os.path.abspath(DB_FILE)
    if os.path.exists(local_path):
        print(f"Local DB exists at {local_path}. Size: {os.path.getsize(local_path)} bytes")
        async with aiosqlite.connect(local_path) as db:
             try:
                 cursor = await db.execute("SELECT COUNT(*) FROM users")
                 count = await cursor.fetchone()
                 print(f"Users in LOCAL DB: {count[0]}")
             except Exception as e:
                 print(f"Error checking users in local DB: {e} (Maybe table doesn't exist?)")
    else:
        print(f"Local DB not found at {local_path}")

if __name__ == "__main__":
    asyncio.run(inspect())
