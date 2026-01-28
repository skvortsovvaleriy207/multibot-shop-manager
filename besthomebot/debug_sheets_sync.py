import sys
import os
import asyncio
import logging

# Add current directory to path
sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO)

async def run_debug():
    print("--- STARTING DEBUG SYNC ---")
    try:
        # Import here to avoid early errors
        from google_sheets import sync_from_sheets_to_db
        
        result = await sync_from_sheets_to_db()
        print(f"--- SYNC RESULT: {result} ---")
    except Exception as e:
        print(f"--- SYNC EXCEPTION: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
