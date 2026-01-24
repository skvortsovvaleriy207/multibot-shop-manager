import aiosqlite
import gspread
from datetime import datetime, timedelta
from config import CREDENTIALS_FILE, PLANS_REPORTS_SHEET_URL
import asyncio
import logging
from bot_instance import bot

# Статусы предложений согласно ТЗ
PROPOSAL_STATUSES = [
    "Новое предложение", "В обработке", "Запрос данных", "В оценке", 
    "В опросе", "Полезность", "В доработке", "В обеспечении", 
    "В производстве", "В реализации", "В развитии", "Выполнено", "Отменено"
]

def is_valid_proposal(text: str) -> bool:
    """Проверка валидности предложения"""
    if not text or len(text) < 2:
        return False
        
    invalid_patterns = [
        "нет", "no", "не имею", "отсутствует", "none", "n/a", 
        "минус", "-", "—", "не хочу", "не буду"
    ]
    
    cleaned_text = text.lower().strip()
    
    # Полное совпадение
    if cleaned_text in invalid_patterns:
        return False
        
    # Частичное совпадение для коротких фраз
    if len(cleaned_text) < 10:
        for pattern in invalid_patterns:
            if pattern == cleaned_text:
                return False
                
    return True

async def export_initiatives_to_sheets():
    """Выгрузка инициатив в таблицу планов и отчетов"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT user_id, username, full_name, business_proposal, 
                       created_at, phone, email
                FROM users 
                WHERE business_proposal IS NOT NULL AND business_proposal != ''
                ORDER BY created_at DESC
            """)
            initiatives = await cursor.fetchall()
        
        if not initiatives:
            return True
        
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_url(PLANS_REPORTS_SHEET_URL).sheet1
        
        # Заголовки
        headers = [
            "ID пользователя", "Username", "ФИО", "Инициативное предложение",
            "Дата подачи", "Телефон", "Email", "Статус предложения", 
            "Комментарий админа", "Дата обновления"
        ]
        
        # Данные
        data = [headers]
        for initiative in initiatives:
            proposal_text = initiative[3]
            if is_valid_proposal(proposal_text):
                data.append([
                    initiative[0], initiative[1] or "", initiative[2] or "",
                    proposal_text, initiative[4], initiative[5] or "", 
                    initiative[6] or "", "Новое предложение", "", ""
                ])
        
        sheet.clear()
        sheet.update('A1', data)
        
        logging.info("Initiatives exported to Google Sheets successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting initiatives: {e}")
        return False

async def notify_initiators():
    """Уведомление инициаторов для уточнения деталей"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT user_id, username, full_name, business_proposal
                FROM users 
                WHERE business_proposal IS NOT NULL AND business_proposal != ''
                AND (notified_at IS NULL OR notified_at < date('now', '-7 days'))
            """)
            initiators = await cursor.fetchall()
        
        for user_id, username, full_name, proposal in initiators:
            if not is_valid_proposal(proposal):
                continue

            try:
                message = f"""
🚀 **Ваша инициатива на рассмотрении**

Здравствуйте, {full_name or username or 'участник'}!

Ваше предложение: "{proposal[:100]}..." принято к рассмотрению.

Для дальнейшей работы с вашей инициативой просим уточнить:
• Детальное описание предложения
• Ожидаемые сроки реализации  
• Необходимые ресурсы
• Ваши контактные данные

Ответьте на это сообщение с дополнительной информацией.
                """
                
                await bot.send_message(user_id, message)
                
                # Отмечаем как уведомленного
                await db.execute(
                    "UPDATE users SET notified_at = datetime('now') WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                
                await asyncio.sleep(1)  # Задержка между сообщениями
                
            except Exception as e:
                logging.error(f"Failed to notify user {user_id}: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error notifying initiators: {e}")
        return False

async def sync_proposal_statuses():
    """Синхронизация статусов предложений из Google Sheets"""
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_url(PLANS_REPORTS_SHEET_URL).sheet1
        
        data = sheet.get_all_values()
        if len(data) < 2:
            return True
        
        headers = data[0]
        status_col = headers.index("Статус предложения") if "Статус предложения" in headers else -1
        user_id_col = headers.index("ID пользователя") if "ID пользователя" in headers else -1
        
        if status_col == -1 or user_id_col == -1:
            return False
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data[1:]:
                if len(row) > max(status_col, user_id_col):
                    user_id = row[user_id_col]
                    status = row[status_col]
                    
                    if user_id and status and status in PROPOSAL_STATUSES:
                        # Получаем текущий статус
                        cursor = await db.execute("SELECT proposal_status FROM users WHERE user_id = ?", (int(user_id),))
                        current_status_row = await cursor.fetchone()
                        current_status = current_status_row[0] if current_status_row else None
                        
                        # Если статус изменился, обновляем и уведомляем
                        if current_status != status:
                            await db.execute(
                                "UPDATE users SET proposal_status = ? WHERE user_id = ?",
                                (status, int(user_id))
                            )
                            
                            # Уведомляем пользователя об изменении статуса
                            try:
                                message = f"""
📋 **Обновление статуса вашей инициативы**

Статус изменен на: **{status}**

Следите за обновлениями в личном кабинете.
                                """
                                await bot.send_message(int(user_id), message)
                            except Exception:
                                pass
            
            await db.commit()
        
        return True
        
    except Exception as e:
        logging.error(f"Error syncing proposal statuses: {e}")
        return False

async def scheduled_initiatives_sync():
    """Планировщик синхронизации инициатив в 17:00 МСК"""
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
            
            logging.info("Starting scheduled initiatives sync at 17:00 MSK")
            
            # Выгружаем инициативы
            await export_initiatives_to_sheets()
            
            # Уведомляем инициаторов
            await notify_initiators()
            
            # Синхронизируем статусы
            await sync_proposal_statuses()
            
            logging.info("✅ Initiatives sync completed successfully")
                
        except Exception as e:
            logging.error(f"Error in scheduled initiatives sync: {e}")
        
        await asyncio.sleep(3600)  # Проверяем каждый час