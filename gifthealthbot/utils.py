import asyncio
import logging
import random
import gspread
import aiosqlite
from functools import wraps

from aiogram.types import Message, CallbackQuery
from db import check_account_status

async def has_active_process(user_id: int) -> bool:
    """
    Checks if the user has any active order requests or orders.
    Active means status is not 'completed', 'cancelled', or 'rejected'.
    """
    async with aiosqlite.connect("bot_database.db") as db:
        # Check order_requests
        cursor = await db.execute("""
            SELECT 1 FROM order_requests 
            WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
        """, (user_id,))
        if await cursor.fetchone():
            return True
            
        # Check orders
        cursor = await db.execute("""
            SELECT 1 FROM orders 
            WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
        """, (user_id,))
        if await cursor.fetchone():
            return True
            
    return False

async def get_active_process_details(user_id: int) -> str:
    """
    Returns details about the active process for the user.
    """
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT item_type, created_at, status FROM order_requests 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
            """, (user_id,))
            row = await cursor.fetchone()
            if row:
                return f"Активная заявка: {row[0]} от {row[1]} (Статус: {row[2]})"
        except Exception:
            pass

        try:
            cursor = await db.execute("""
                SELECT order_type, order_date, status FROM orders 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
            """, (user_id,))
            row = await cursor.fetchone()
            if row:
                return f"Активный заказ: {row[0]} от {row[1]} (Статус: {row[2]})"
        except Exception:
            pass

    return "Неизвестный процесс"

async def check_blocked_user(event):
    """
    Checks if the user is blocked. 
    Returns True if blocked (and sends message), False otherwise.
    """
    user_id = event.from_user.id
    # check_account_status returns True if allowed ("Р"), False otherwise
    is_allowed = await check_account_status(user_id)
    
    if not is_allowed:
        if isinstance(event, CallbackQuery):
            await event.answer("Ваш аккаунт заблокирован или не найден.", show_alert=True)
        else:
            await event.answer("Ваш аккаунт заблокирован или не найден.")
        return True 
    return False

def retry_google_api(retries: int = 5, delay: float = 5.0, backoff: float = 2.0):
    """
    Decorator to retry function calls upon gspread.exceptions.APIError.
    
    Args:
        retries (int): Number of retries.
        delay (float): Initial delay in seconds.
        backoff (float): Multiplier for delay after each failure.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return await asyncio.to_thread(func, *args, **kwargs)
                except gspread.exceptions.APIError as e:
                    # Check for 429 Quota exceeded or 5xx Server Errors
                    if attempt < retries and (e.response.status_code == 429 or e.response.status_code >= 500):
                        # For 429 (Quota Exceeded), wait longer to let quota reset
                        if e.response.status_code == 429:
                             sleep_time = 60.0 + random.uniform(5, 15) # Wait at least 60s + significant jitter
                             logging.warning(f"Google API Quota Exceeded (429) in {func.__name__}. Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{retries})")
                        else:
                             sleep_time = current_delay + random.uniform(0, 2) # Add jitter
                             logging.warning(f"Google API Error {e.response.status_code} in {func.__name__}. Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{retries})")
                        
                        await asyncio.sleep(sleep_time)
                        if e.response.status_code != 429:
                            current_delay *= backoff
                    else:
                        logging.error(f"Google API Error in {func.__name__} after {attempt} retries: {e}")
                        raise e
                except Exception as e:
                     logging.error(f"Unexpected error in {func.__name__}: {e}")
                     raise e
        return wrapper
    return decorator