import aiosqlite
import gspread
from datetime import datetime, timedelta
from config import CREDENTIALS_FILE, REFERRALS_SHEET_URL
import asyncio
import logging
from bot_instance import bot
from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dispatcher import dp
from utils import check_blocked_user

# Бонус за реферала согласно ТЗ
REFERRAL_BONUS = 0.1

async def init_referral_system():
    """Инициализация реферальной системы"""
    async with aiosqlite.connect("bot_database.db") as db:
        # Таблица рефералов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                created_at TEXT,
                bonus_paid BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        """)
        
        # Добавляем поля в users
        try:
            await db.execute("ALTER TABLE users ADD COLUMN referral_link TEXT")
            await db.execute("ALTER TABLE users ADD COLUMN referral_earnings REAL DEFAULT 0")
            await db.execute("ALTER TABLE users ADD COLUMN total_referrals INTEGER DEFAULT 0")
        except:
            pass
        
        await db.commit()

async def generate_referral_link(user_id: int) -> str:
    """Генерация реферальной ссылки"""
    from bot_instance import bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Сохраняем ссылку в БД
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute(
            "UPDATE users SET referral_link = ? WHERE user_id = ?",
            (link, user_id)
        )
        await db.commit()
    
    return link

async def process_referral(referred_id: int, referrer_id: int):
    """Обработка реферала"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # Проверяем, не является ли пользователь уже рефералом
            cursor = await db.execute(
                "SELECT 1 FROM referrals WHERE referred_id = ?", (referred_id,)
            )
            if await cursor.fetchone():
                return False
            
            # Добавляем реферала
            await db.execute("""
                INSERT INTO referrals (referrer_id, referred_id, created_at)
                VALUES (?, ?, datetime('now'))
            """, (referrer_id, referred_id))
            
            # Обновляем счетчик рефералов
            await db.execute("""
                UPDATE users SET total_referrals = total_referrals + 1
                WHERE user_id = ?
            """, (referrer_id,))
            
            await db.commit()
            
            # Уведомляем реферера
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 У вас новый реферал! Вы получите бонус {REFERRAL_BONUS} монеты."
                )
            except:
                pass
            
            return True
            
    except Exception as e:
        logging.error(f"Error processing referral: {e}")
        return False

async def calculate_monthly_referral_bonuses():
    """Расчет ежемесячных бонусов за рефералов"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # Получаем активных рефералов за месяц
            cursor = await db.execute("""
                SELECT r.referrer_id, COUNT(*) as active_referrals
                FROM referrals r
                JOIN users u ON r.referred_id = u.user_id
                WHERE r.created_at >= date('now', '-30 days')
                AND u.has_completed_survey = 1
                AND r.bonus_paid = FALSE
                GROUP BY r.referrer_id
            """)
            
            referral_data = await cursor.fetchall()
            
            for referrer_id, active_count in referral_data:
                bonus = active_count * REFERRAL_BONUS
                
                # Начисляем бонус
                await db.execute("""
                    UPDATE users SET 
                        referral_earnings = referral_earnings + ?,
                        current_balance = current_balance + ?
                    WHERE user_id = ?
                """, (bonus, bonus, referrer_id))
                
                # Отмечаем бонусы как выплаченные
                await db.execute("""
                    UPDATE referrals SET bonus_paid = TRUE
                    WHERE referrer_id = ? AND bonus_paid = FALSE
                """, (referrer_id,))
                
                # Уведомляем пользователя
                try:
                    await bot.send_message(
                        referrer_id,
                        f"💰 Начислен реферальный бонус: {bonus} монет за {active_count} активных рефералов!"
                    )
                except:
                    pass
            
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"Error calculating referral bonuses: {e}")
        return False

async def export_referral_data():
    """Выгрузка данных реферальной системы"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT u.user_id, u.username, u.full_name, u.total_referrals,
                       u.referral_earnings, u.referral_link, u.created_at
                FROM users u
                WHERE u.total_referrals > 0 OR u.referral_earnings > 0
                ORDER BY u.total_referrals DESC
            """)
            referrers = await cursor.fetchall()
        
        if not referrers:
            return True
        
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_url(REFERRALS_SHEET_URL).sheet1
        
        # Заголовки
        headers = [
            "ID пользователя", "Username", "ФИО", "Количество рефералов",
            "Заработано монет", "Реферальная ссылка", "Дата регистрации"
        ]
        
        # Данные
        data = [headers]
        for referrer in referrers:
            data.append([
                referrer[0], referrer[1] or "", referrer[2] or "",
                referrer[3], referrer[4], referrer[5] or "", referrer[6]
            ])
        
        sheet.clear()
        sheet.update('A1', data)
        
        logging.info("Referral data exported successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting referral data: {e}")
        return False

async def get_referral_stats(user_id: int):
    """Получение статистики рефералов пользователя"""
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT total_referrals, referral_earnings, referral_link
            FROM users WHERE user_id = ?
        """, (user_id,))
        return await cursor.fetchone()

async def start_referral_system():
    """Запуск реферальной системы"""
    await init_referral_system()
    asyncio.create_task(scheduled_referral_sync())

async def scheduled_referral_sync():
    """Планировщик реферальной системы"""
    import pytz
    
    while True:
        try:
            moscow_tz = pytz.timezone('Europe/Moscow')
            now = datetime.now(moscow_tz)
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            
            if now >= target_time:
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            logging.info("Starting scheduled referral sync at 17:00 MSK")
            
            # Рассчитываем бонусы
            await calculate_monthly_referral_bonuses()
            
            # Выгружаем данные
            await export_referral_data()
            
            logging.info("✅ Referral sync completed successfully")
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Error in scheduled referral sync: {e}")
        
        await asyncio.sleep(3600)

# Обработчик кнопки "Рефералы"
@dp.callback_query(F.data == "referral_system")
async def referral_system_handler(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    # Получаем статистику пользователя
    stats = await get_referral_stats(user_id)
    
    if not stats:
        # Создаем реферальную ссылку если её нет
        referral_link = await generate_referral_link(user_id)
        total_referrals = 0
        referral_earnings = 0.0
    else:
        total_referrals, referral_earnings, referral_link = stats
        if not referral_link:
            referral_link = await generate_referral_link(user_id)
    
    # Получаем список рефералов
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT u.username, u.full_name, r.created_at
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.created_at DESC
            LIMIT 10
        """, (user_id,))
        recent_referrals = await cursor.fetchall()
    
    text = f"🔗 **Реферальная программа**\n\n"
    text += f"👥 Всего рефералов: {total_referrals or 0}\n"
    text += f"💰 Заработано: {referral_earnings or 0:.1f} монет\n\n"
    text += f"🎯 **Ваша реферальная ссылка:**\n`{referral_link}`\n\n"
    text += f"💡 **Как это работает:**\n"
    text += f"• Поделитесь ссылкой с друзьями\n"
    text += f"• За каждого активного реферала получите {REFERRAL_BONUS} монеты\n"
    text += f"• Бонусы начисляются ежемесячно\n\n"
    
    if recent_referrals:
        text += f"👥 **Последние рефералы:**\n"
        for username, full_name, created_at in recent_referrals[:5]:
            name = full_name or username or "Пользователь"
            date = created_at[:10] if created_at else "Неизвестно"
            text += f"• {name} ({date})\n"
    else:
        text += f"👥 **У вас пока нет рефералов**\n"
        text += f"Поделитесь ссылкой, чтобы начать зарабатывать!"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="referral_system"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()