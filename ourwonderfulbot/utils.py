import asyncio
import logging
import random
import gspread
from functools import wraps

import aiosqlite
from aiogram.types import Message, CallbackQuery
from db import check_account_status

async def has_active_process(user_id: int) -> bool:
    """
    Checks if the user has any active order requests or orders.
    Active means status is not 'completed', 'cancelled', or 'rejected'.
    """
    async with aiosqlite.connect("bot_database.db") as db:
        # Check order_requests
        try:
            cursor = await db.execute("""
                SELECT 1 FROM order_requests 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
            """, (user_id,))
            if await cursor.fetchone():
                return True
        except Exception:
            pass # Table might not exist or other error
            
        # Check orders
        try:
            cursor = await db.execute("""
                SELECT 1 FROM orders 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
            """, (user_id,))
            if await cursor.fetchone():
                return True
        except Exception:
            pass

    return False

async def get_active_process_details(user_id: int) -> str:
    """
    Returns details about the active process (order request or order).
    """
    async with aiosqlite.connect("bot_database.db") as db:
        # Check order_requests
        try:
            cursor = await db.execute("""
                SELECT id, status, item_type FROM order_requests 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
                LIMIT 1
            """, (user_id,))
            row = await cursor.fetchone()
            if row:
                return f"Активная заявка #{row[0]} (Статус: {row[1]})"
        except Exception:
            pass
            
        # Check orders
        try:
            cursor = await db.execute("""
                SELECT id, status FROM orders 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
                LIMIT 1
            """, (user_id,))
            row = await cursor.fetchone()
            if row:
                return f"Активный заказ #{row[0]} (Статус: {row[1]})"
        except Exception:
            pass

    return "Неизвестный активный процесс"

async def check_blocked_user(event):
    """
    Checks if the user is blocked. 
    Returns True if blocked (and sends message), False otherwise.
    """
    user_id = event.from_user.id
    # check_account_status returns True if allowed ("Р"), False otherwise
    # OLD LOGIC: if not allowed => blocked. 
    # NEW LOGIC: check explicitly if blocked ("О")
    
    from db import is_user_blocked
    is_blocked = await is_user_blocked(user_id)
    
    if is_blocked:
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
                        # If it's a sync function, we run it in a threadexecutor if it's called from async context,
                        # BUT the wrapper itself is async, so we must await.
                        # However, some functions might be sync and used in sync context.
                        # For simplicity in this codebase which uses asyncio, we assume async usage.
                        # BUT wait, the calls are often wrapped in asyncio.to_thread already in main.py?
                        # No, usually we call sync functions directly or via to_thread.
                        # If we wrap a sync function with this async wrapper, we must call it with await.
                        # Let's handle both just in case, or assume we decorate the implementation functions.
                        # Actually, gspread calls are blocking. We should run them in thread.
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