"""
Утилиты для бота
"""

import aiosqlite
from aiogram import types

async def check_blocked_user(callback: types.CallbackQuery) -> bool:
    """Проверка заблокирован ли пользователь"""
    try:
        user_id = callback.from_user.id
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("SELECT account_status FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            
            if row and row[0] == 'О':
                await callback.answer("Ваш аккаунт заблокирован администратором.", show_alert=True)
                return True
        return False
        return False
    except Exception as e:
        print(f"Ошибка при проверке блокировки пользователя: {e}")
        return False

async def has_active_process(user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя активные процессы:
    1. Заявки (order_requests) в статусе 'new', 'active', 'processing' (не 'approved', 'rejected')
    2. Заказы (orders) в статусе 'new', 'processing', 'confirmed' (не 'completed', 'cancelled')
    """
    try:
        from config import ADMIN_ID
        if user_id == ADMIN_ID:
            return False

        async with aiosqlite.connect("bot_database.db") as db:
            # Проверка заявок
            cursor = await db.execute("""
                SELECT 1 FROM order_requests 
                WHERE user_id = ? AND status NOT IN ('approved', 'rejected', 'completed')
                LIMIT 1
            """, (user_id,))
            if await cursor.fetchone():
                return True

            # Проверка заказов
            cursor = await db.execute("""
                SELECT 1 FROM orders 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
                LIMIT 1
            """, (user_id,))
            if await cursor.fetchone():
                return True
                
        return False
    except Exception as e:
        print(f"Ошибка при проверке активных процессов: {e}")
        return False

async def get_active_process_details(user_id: int) -> str:
    """
    Возвращает детали активного процесса
    """
    try:
        from config import ADMIN_ID
        if user_id == ADMIN_ID:
            return "Администратор (тест)"

        async with aiosqlite.connect("bot_database.db") as db:
            # Проверка заявок
            cursor = await db.execute("""
                SELECT id, title, status, item_type FROM order_requests 
                WHERE user_id = ? AND status NOT IN ('approved', 'rejected', 'completed')
                LIMIT 1
            """, (user_id,))
            req = await cursor.fetchone()
            if req:
                return f"Активная заявка №{req[0]} '{req[1]}' (Тип: {req[3]}, Статус: {req[2]})"

            # Проверка заказов
            cursor = await db.execute("""
                SELECT id, item_type, status FROM orders 
                WHERE user_id = ? AND status NOT IN ('completed', 'cancelled', 'rejected')
                LIMIT 1
            """, (user_id,))
            order = await cursor.fetchone()
            if order:
                return f"Активный заказ №{order[0]} (Тип: {order[1]}, Статус: {order[2]})"
                
        return "Неизвестный процесс"
    except Exception as e:
        return f"Ошибка получения данных: {e}"