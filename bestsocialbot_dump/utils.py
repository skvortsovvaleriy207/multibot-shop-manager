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
    except Exception as e:
        print(f"Ошибка при проверке блокировки пользователя: {e}")
        return False