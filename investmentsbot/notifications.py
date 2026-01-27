import logging
import aiosqlite
from aiogram import Bot

from db import connect_db, SHARED_DB_FILE

async def send_user_notification(bot: Bot, user_id: int, changes: dict = None):
    """
    Отправляет уведомление пользователю о состоянии его профиля.
    changes: словарь изменений (не используется для формирования текста, но может быть полезен для логирования)
    """
    async with connect_db() as db:
        # 1. Получаем данные пользователя
        cursor = await db.execute("""
            SELECT 
                username, full_name, birth_date, location, email, phone, employment,
                financial_problem, social_problem, ecological_problem, passive_subscriber,
                active_partner, investor_trader, business_proposal
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        user_basic_data = await cursor.fetchone()
        
        # 2. Получаем ПОСЛЕДНЮЮ запись о бонусах
        cursor = await db.execute("""
            SELECT bonus_total, current_balance 
            FROM user_bonuses 
            WHERE user_id = ? 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (user_id,))
        bonus_data = await cursor.fetchone()

        if user_basic_data:
             # Merge tuples. bonus_data might be None if no bonuses yet.
             bonus_values = bonus_data if bonus_data else (0.0, 0.0)
             user_data = user_basic_data + bonus_values
        else:
             user_data = None
    
    if not user_data:
        logging.warning(f"Attempted to notify non-existent user {user_id}")
        return

    field_names = {
        'username': 'Никнейм',
        'full_name': 'ФИО',
        'birth_date': 'Дата рождения',
        'location': 'Место жительства',
        'email': 'Email',
        'phone': 'Телефон',
        'employment': 'Занятость',
        'financial_problem': 'Финансовая проблема',
        'social_problem': 'Социальная проблема',
        'ecological_problem': 'Экологическая проблема',
        'passive_subscriber': 'Статус пассивного подписчика',
        'active_partner': 'Статус активного партнера',
        'investor_trader': 'Статус инвестора/трейдера',
        'business_proposal': 'Бизнес-предложение',
        'bonus_total': 'Общая сумма бонусов',
        'current_balance': 'Текущий баланс'
    }

    message = "🔔 Ваш профиль был обновлен. Текущие данные:\n\n"
    for i, (field, name) in enumerate(field_names.items()):
        value = user_data[i] if user_data[i] is not None else 'Не указано'
        message += f"▪️ {name}: {value}\n"
    
    # 1. Сохраняем сообщение в БД (для внутреннего ящика)
    try:
        from datetime import datetime
        async with connect_db() as db:
            await db.execute("""
                INSERT INTO messages (sender_id, recipient_id, subject, message_text, sent_at, is_read)
                VALUES (NULL, ?, ?, ?, ?, 0)
            """, (user_id, "Обновление профиля", message, datetime.now().isoformat()))
            await db.commit()
    except Exception as db_e:
        logging.error(f"Failed to save notification to DB for user {user_id}: {db_e}")

    # 2. Отправляем в чат Telegram
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        logging.error(f"Failed to send notification to user {user_id}: {e}")
