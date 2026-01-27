import aiosqlite
import os
import json
from datetime import datetime
import logging

# Path to the global database file
GLOBAL_DB_PATH = os.path.join(os.path.dirname(__file__), 'global_users.db')

async def init_global_db():
    try:
        async with aiosqlite.connect(GLOBAL_DB_PATH) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS global_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Survey data table (JSON storage for flexibility)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_surveys (
                    user_id INTEGER PRIMARY KEY,
                    survey_data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES global_users(user_id)
                )
            """)
            # Subscriptions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id INTEGER,
                    bot_folder_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, bot_folder_name),
                    FOREIGN KEY (user_id) REFERENCES global_users(user_id)
                )
            """)
            await db.commit()
    except Exception as e:
        logging.error(f"Error initializing global DB: {e}")

async def get_user_subscription_count(user_id: int) -> int:
    """Returns the number of bots the user is subscribed to."""
    async with aiosqlite.connect(GLOBAL_DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM user_subscriptions WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def is_user_subscribed(user_id: int, bot_name: str) -> bool:
    """Checks if the user is already subscribed to the specific bot."""
    async with aiosqlite.connect(GLOBAL_DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM user_subscriptions WHERE user_id = ? AND bot_folder_name = ?", 
            (user_id, bot_name)
        )
        return await cursor.fetchone() is not None

async def register_user_subscription(user_id: int, bot_name: str):
    """Registers a user subscription to a bot."""
    async with aiosqlite.connect(GLOBAL_DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_subscriptions (user_id, bot_folder_name) VALUES (?, ?)", 
            (user_id, bot_name)
        )
        await db.commit()

async def get_global_user_survey(user_id: int) -> dict:
    """Retrieves the survey data for a user if it exists."""
    async with aiosqlite.connect(GLOBAL_DB_PATH) as db:
        cursor = await db.execute("SELECT survey_data FROM user_surveys WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                logging.error(f"Error decoding survey data for user {user_id}")
                return None
        return None

async def save_global_user(user_id: int, username: str, full_name: str, survey_data: dict):
    """Saves user info and survey data to the global database."""
    async with aiosqlite.connect(GLOBAL_DB_PATH) as db:
        # 1. Save Base User Info
        cursor = await db.execute("SELECT user_id FROM global_users WHERE user_id = ?", (user_id,))
        if not await cursor.fetchone():
             await db.execute(
                "INSERT INTO global_users (user_id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )
        else:
             await db.execute(
                "UPDATE global_users SET username = ?, full_name = ? WHERE user_id = ?",
                (username, full_name, user_id)
            )
        
        # 2. Save Survey Data
        survey_json = json.dumps(survey_data, ensure_ascii=False)
        await db.execute(
            "INSERT OR REPLACE INTO user_surveys (user_id, survey_data, updated_at) VALUES (?, ?, ?)",
            (user_id, survey_json, datetime.now().isoformat())
        )
        await db.commit()
