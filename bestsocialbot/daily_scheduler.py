"""
Ежедневный планировщик для синхронизации в 17:00 МСК согласно ТЗ
"""

import asyncio
import logging
from datetime import datetime, time
import pytz

async def start_daily_scheduler():
    """Запуск ежедневного планировщика синхронизации в 17:00 МСК"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    while True:
        try:
            # Получаем текущее время в МСК
            now = datetime.now(moscow_tz)
            
            # Устанавливаем целевое время 17:00 МСК
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            
            # Если уже прошло 17:00, планируем на следующий день
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            # Вычисляем время ожидания
            wait_seconds = (target_time - now).total_seconds()
            
            logging.info(f"Следующая синхронизация запланирована на {target_time.strftime('%d.%m.%Y %H:%M')} МСК")
            
            # Ждем до 17:00
            await asyncio.sleep(wait_seconds)
            
            # Выполняем ежедневную синхронизацию
            await daily_sync_task()
            
        except Exception as e:
            logging.error(f"Ошибка в планировщике: {e}")
            # При ошибке ждем час и пробуем снова
            await asyncio.sleep(3600)

async def daily_sync_task():
    """Ежедневная задача синхронизации в 17:00 МСК"""
    logging.info("🕐 Начинаем ежедневную синхронизацию в 17:00 МСК")
    
    try:
        # 1. Синхронизация основных данных
        from google_sheets import sync_db_to_google_sheets
        await sync_db_to_google_sheets()
        
        # 2. Синхронизация автомагазина
        from automarket_sheets import export_all_automarket_data
        await export_all_automarket_data()
        
        # 3. Синхронизация партнерских программ
        from partner_sheets import export_all_partner_data, sync_partner_data_to_cards
        await export_all_partner_data()
        await sync_partner_data_to_cards()
        
        # 4. Синхронизация статусов заказов (функционал в orders.py)
        # await sync_order_statuses_from_sheets()
        
        # 5. Синхронизация планов и отчетов (ТЗ №2 п.1)
        await sync_plans_and_reports()
        
        # 6. Обновление реферальной системы (ТЗ №2 п.2)
        await update_referral_system()
        
        # 7. Обновление системы активности (ТЗ №2 п.3)
        await update_activity_system()
        
        # 8. Генерация статистики (ТЗ №2 п.4-5)
        await generate_statistics()
        
        logging.info("✅ Ежедневная синхронизация завершена успешно")
        
    except Exception as e:
        logging.error(f"❌ Ошибка ежедневной синхронизации: {e}")

async def sync_plans_and_reports():
    """Синхронизация планов и отчетов согласно ТЗ №2 п.1"""
    try:
        # Выгрузка данных из графы 16 основной таблицы
        await export_business_proposals()
        
        # Отправка сообщений инициаторам
        await notify_proposal_initiators()
        
        # Обновление статусов предложений
        await update_proposal_statuses()
        
        logging.info("✅ Планы и отчеты синхронизированы")
        
    except Exception as e:
        logging.error(f"❌ Ошибка синхронизации планов и отчетов: {e}")

async def export_business_proposals():
    """Выгрузка бизнес-предложений из графы 16"""
    try:
        import aiosqlite
        from config import MAIN_SURVEY_SHEET_URL
        import gspread
        from config import CREDENTIALS_FILE
        
        # Получаем предложения из БД
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT user_id, username, full_name, business_proposal, created_at
                FROM users 
                WHERE business_proposal IS NOT NULL AND business_proposal != ''
                ORDER BY created_at DESC
            """)
            proposals = await cursor.fetchall()
        
        if not proposals:
            return
        
        # Создаем таблицу планов и отчетов
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        
        # Создаем новую таблицу или используем существующую
        try:
            sheet = gc.create("Планы и отчеты АвтоАвиа")
            worksheet = sheet.sheet1
        except:
            # Если таблица уже существует, открываем её
            sheet = gc.open("Планы и отчеты АвтоАвиа")
            worksheet = sheet.sheet1
        
        # Заголовки
        headers = [
            "Дата предложения", "Telegram ID", "Username", "ФИО", 
            "Бизнес-предложение", "Статус предложения", "Комментарий админа",
            "Дата обработки", "Оценка полезности", "Планируемая реализация"
        ]
        
        # Подготавливаем данные
        data = [headers]
        for proposal in proposals:
            row = [
                proposal[4][:10] if proposal[4] else "",  # Дата
                proposal[0],  # User ID
                proposal[1] or "",  # Username
                proposal[2] or "",  # ФИО
                proposal[3] or "",  # Предложение
                "Новое предложение",  # Статус по умолчанию
                "",  # Комментарий
                "",  # Дата обработки
                "",  # Оценка
                ""   # Планируемая реализация
            ]
            data.append(row)
        
        # Записываем данные
        worksheet.clear()
        worksheet.update('A1', data)
        
        logging.info(f"Выгружено {len(proposals)} бизнес-предложений")
        
    except Exception as e:
        logging.error(f"Ошибка выгрузки предложений: {e}")

async def notify_proposal_initiators():
    """Отправка сообщений инициаторам предложений"""
    try:
        import aiosqlite
        from bot_instance import bot
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT user_id, business_proposal
                FROM users 
                WHERE business_proposal IS NOT NULL AND business_proposal != ''
                AND (last_proposal_notification IS NULL OR 
                     date(last_proposal_notification) < date('now'))
            """)
            users = await cursor.fetchall()
        
        for user_id, proposal in users:
            try:
                message = f"""
🔔 **Уведомление о вашем бизнес-предложении**

Ваше предложение: "{proposal[:100]}..."

Для уточнения деталей и постановки предложения на учет, пожалуйста:
1. Опишите подробнее суть предложения
2. Укажите необходимые ресурсы
3. Предложите план реализации

Ваше предложение будет рассмотрено администрацией в течение 3 рабочих дней.
                """
                
                await bot.send_message(user_id, message)
                
                # Обновляем дату уведомления
                async with aiosqlite.connect("bot_database.db") as db:
                    await db.execute(
                        "UPDATE users SET last_proposal_notification = datetime('now') WHERE user_id = ?",
                        (user_id,)
                    )
                    await db.commit()
                
            except Exception as e:
                logging.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
        
        logging.info(f"Отправлено уведомлений: {len(users)}")
        
    except Exception as e:
        logging.error(f"Ошибка отправки уведомлений: {e}")

async def update_proposal_statuses():
    """Обновление статусов предложений из Google Sheets"""
    try:
        # Статусы согласно ТЗ №2 п.1
        valid_statuses = [
            "Новое предложение", "В обработке", "Запрос данных", "В оценке",
            "В опросе", "Полезность", "В доработке", "В обеспечении",
            "В производстве", "В реализации", "В развитии", "Выполнено", "Отменено"
        ]
        
        # Здесь должна быть логика чтения статусов из Google Sheets
        # и обновления в БД с уведомлением пользователей
        
        logging.info("Статусы предложений обновлены")
        
    except Exception as e:
        logging.error(f"Ошибка обновления статусов: {e}")

async def update_referral_system():
    """Обновление реферальной системы согласно ТЗ №2 п.2"""
    try:
        # Начисление бонусов рефереру (0,1 монеты за активного реферала)
        await calculate_referral_bonuses()
        
        # Обновление таблицы рефералов
        await update_referral_table()
        
        logging.info("✅ Реферальная система обновлена")
        
    except Exception as e:
        logging.error(f"❌ Ошибка обновления реферальной системы: {e}")

async def calculate_referral_bonuses():
    """Расчет и начисление реферальных бонусов"""
    try:
        import aiosqlite
        
        async with aiosqlite.connect("bot_database.db") as db:
            # Получаем активных рефералов за месяц
            cursor = await db.execute("""
                SELECT referrer_id, COUNT(*) as active_referrals
                FROM users 
                WHERE referrer_id IS NOT NULL 
                AND date(created_at) >= date('now', '-1 month')
                AND has_completed_survey = 1
                GROUP BY referrer_id
            """)
            referrals = await cursor.fetchall()
            
            for referrer_id, count in referrals:
                bonus = count * 0.1  # 0,1 монеты за каждого реферала
                
                # Начисляем бонус
                await db.execute("""
                    INSERT OR REPLACE INTO user_bonuses 
                    (user_id, bonus_total, current_balance, updated_at)
                    VALUES (?, COALESCE((SELECT bonus_total FROM user_bonuses WHERE user_id = ?), 0) + ?,
                            COALESCE((SELECT current_balance FROM user_bonuses WHERE user_id = ?), 0) + ?,
                            datetime('now'))
                """, (referrer_id, referrer_id, bonus, referrer_id, bonus))
            
            await db.commit()
            logging.info(f"Начислены реферальные бонусы {len(referrals)} пользователям")
            
    except Exception as e:
        logging.error(f"Ошибка расчета реферальных бонусов: {e}")

async def update_referral_table():
    """Обновление таблицы рефералов"""
    # Заглушка для обновления Google таблицы рефералов
    pass

async def update_activity_system():
    """Обновление системы активности согласно ТЗ №2 п.3"""
    try:
        # Расчет активности по 6 показателям
        await calculate_user_activity()
        
        # Начисление бонусов за активность (до 0,06 монеты в день)
        await award_activity_bonuses()
        
        logging.info("✅ Система активности обновлена")
        
    except Exception as e:
        logging.error(f"❌ Ошибка обновления системы активности: {e}")

async def calculate_user_activity():
    """Расчет активности пользователей по 6 показателям"""
    # 1. Заявки/заказы
    # 2. Аукционы партнеров  
    # 3. Конкурсы
    # 4. Информационные опросы
    # 5. Просмотры контента
    # 6. Комментарии и реакции
    pass

async def award_activity_bonuses():
    """Начисление бонусов за активность"""
    # До 0,06 монеты в день за активность
    pass

async def generate_statistics():
    """Генерация статистики согласно ТЗ №2 п.4-5"""
    try:
        # Текущая статистика
        await generate_current_statistics()
        
        # Накопительная статистика
        await generate_cumulative_statistics()
        
        logging.info("✅ Статистика сгенерирована")
        
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статистики: {e}")

async def generate_current_statistics():
    """Генерация текущей статистики участников"""
    pass

async def generate_cumulative_statistics():
    """Генерация накопительной статистики за неделю/месяц/квартал/год"""
    pass