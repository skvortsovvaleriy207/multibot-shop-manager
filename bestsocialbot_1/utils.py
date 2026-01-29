import asyncio
import logging
import random
import gspread
from functools import wraps

def retry_google_api(retries: int = 3, delay: float = 5.0, backoff: float = 2.0):
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
                        sleep_time = current_delay + random.uniform(0, 1) # Add jitter
                        logging.warning(f"Google API Error {e.response.status_code} in {func.__name__}. Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{retries})")
                        await asyncio.sleep(sleep_time)
                        current_delay *= backoff
                    else:
                        logging.error(f"Google API Error in {func.__name__} after {attempt} retries: {e}")
                        raise e
                except Exception as e:
                     # For sync functions wrapped in to_thread, implementation might differ slightly if func is sync.
                     # But here we assume wrapper is async.
                     logging.error(f"Unexpected error in {func.__name__}: {e}")
                     raise e
        return wrapper
    return decorator