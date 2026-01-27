"""
Модуль для полного управления всеми таблицами через Google Sheets
Позволяет администраторам управлять всеми данными бота через Google таблицы
"""

import gspread
import aiosqlite
import asyncio
import logging
from datetime import datetime
from config import CREDENTIALS_FILE
from db import DB_FILE

def get_google_sheets_client():
    return gspread.service_account(filename=CREDENTIALS_FILE)

async def sync_categories_from_sheet():
    """Синхронизация категорий из Google Sheets"""
    try:
        from config import AUTO_CATEGORIES_SHEET_URL
        if not AUTO_CATEGORIES_SHEET_URL:
            return False
            
        gc = get_google_sheets_client()
        sheet = gc.open_by_url(AUTO_CATEGORIES_SHEET_URL).sheet1
        data = sheet.get_all_records()
        
        async with aiosqlite.connect(DB_FILE) as db:
            for row in data:
                category_id = row.get('ID категории')
                if not category_id:
                    continue
                    
                await db.execute("""
                    UPDATE auto_categories 
                    SET name = ?, description = ?, is_active = ?
                    WHERE id = ?
                """, (
                    row.get('Название категории', ''),
                    row.get('Описание', ''),
                    1 if row.get('Активна', 'Да') == 'Да' else 0,
                    category_id
                ))
            await db.commit()
        
        print("Категории синхронизированы из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации категорий: {e}")
        return False

async def sync_categories_to_sheet():
    """Экспорт категорий в Google Sheets"""
    try:
        from config import AUTO_CATEGORIES_SHEET_URL
        gc = get_google_sheets_client()
        
        if not AUTO_CATEGORIES_SHEET_URL:
            print("⚠️ AUTO_CATEGORIES_SHEET_URL не указан в config.py")
            return False
        sheet = gc.open_by_url(AUTO_CATEGORIES_SHEET_URL).sheet1
        
        headers = ["ID категории", "Название категории", "Описание", "Активна", "Дата создания"]
        
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("SELECT id, name, description, is_active, created_at FROM auto_categories ORDER BY id")
            categories = await cursor.fetchall()
        
        data = [headers]
        for category in categories:
            row = [
                category[0],  # ID
                category[1] or "",  # Название
                category[2] or "",  # Описание
                "Да" if category[3] else "Нет",  # Активна
                category[4][:10] if category[4] else ""  # Дата
            ]
            data.append(row)
        
        sheet.clear()
        if data:
            sheet.update('A1', data)
        
        print(f"Экспортировано {len(categories)} категорий в Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка экспорта категорий: {e}")
        return False

async def sync_user_bonuses_from_sheet():
    """Синхронизация бонусов пользователей из Google Sheets"""
    try:
        from config import USER_BONUSES_SHEET_URL
        if not USER_BONUSES_SHEET_URL:
            return False
            
        gc = get_google_sheets_client()
        sheet = gc.open_by_url(USER_BONUSES_SHEET_URL).sheet1
        data = sheet.get_all_records()
        
        async with aiosqlite.connect(DB_FILE) as db:
            for row in data:
                user_id = row.get('Telegram ID')
                if not user_id:
                    continue
                    
                await db.execute("""
                    INSERT OR REPLACE INTO user_bonuses 
                    (user_id, bonus_total, current_balance, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    row.get('ИТОГО бонусов', 0),
                    row.get('ТЕКУЩИЙ БАЛАНС', 0),
                    datetime.now().isoformat()
                ))
            await db.commit()
        
        print("Бонусы пользователей синхронизированы из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации бонусов: {e}")
        return False

async def sync_user_bonuses_to_sheet():
    """Экспорт бонусов пользователей в Google Sheets"""
    try:
        from config import USER_BONUSES_SHEET_URL
        gc = get_google_sheets_client()
        
        if not USER_BONUSES_SHEET_URL:
            print("⚠️ USER_BONUSES_SHEET_URL не указан в config.py")
            return False
        sheet = gc.open_by_url(USER_BONUSES_SHEET_URL).sheet1
        
        headers = ["Telegram ID", "Username", "ФИО", "ИТОГО бонусов", "ТЕКУЩИЙ БАЛАНС", "Последнее обновление"]
        
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("""
                SELECT u.user_id, u.username, u.full_name, 
                       COALESCE(ub.bonus_total, 0), COALESCE(ub.current_balance, 0), ub.last_updated
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                ORDER BY u.user_id
            """)
            bonuses = await cursor.fetchall()
        
        data = [headers]
        for bonus in bonuses:
            row = [
                bonus[0],  # User ID
                bonus[1] or "",  # Username
                bonus[2] or "",  # ФИО
                bonus[3] or 0,  # Бонусы
                bonus[4] or 0,  # Баланс
                bonus[5][:19] if bonus[5] else ""  # Дата
            ]
            data.append(row)
        
        sheet.clear()
        if data:
            sheet.update('A1', data)
        
        print(f"Экспортировано {len(bonuses)} записей бонусов в Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка экспорта бонусов: {e}")
        return False

async def sync_reviews_from_sheet():
    """Синхронизация отзывов из Google Sheets"""
    try:
        from config import REVIEWS_SHEET_URL
        if not REVIEWS_SHEET_URL:
            return False
            
        gc = get_google_sheets_client()
        sheet = gc.open_by_url(REVIEWS_SHEET_URL).sheet1
        data = sheet.get_all_records()
        
        async with aiosqlite.connect(DB_FILE) as db:
            for row in data:
                review_id = row.get('ID отзыва')
                if not review_id:
                    continue
                    
                await db.execute("""
                    UPDATE reviews 
                    SET rating = ?, comment = ?, is_approved = ?
                    WHERE id = ?
                """, (
                    row.get('Рейтинг', 5),
                    row.get('Комментарий', ''),
                    1 if row.get('Одобрен', 'Да') == 'Да' else 0,
                    review_id
                ))
            await db.commit()
        
        print("Отзывы синхронизированы из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации отзывов: {e}")
        return False

async def sync_reviews_to_sheet():
    """Экспорт отзывов в Google Sheets"""
    try:
        from config import REVIEWS_SHEET_URL
        gc = get_google_sheets_client()
        
        if not REVIEWS_SHEET_URL:
            print("⚠️ REVIEWS_SHEET_URL не указан в config.py")
            return False
        sheet = gc.open_by_url(REVIEWS_SHEET_URL).sheet1
        
        headers = ["ID отзыва", "Telegram ID", "Username", "Тип заказа", "ID товара/услуги", 
                  "Рейтинг", "Комментарий", "Одобрен", "Дата создания"]
        
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("""
                SELECT r.id, r.user_id, u.username, r.order_type, r.item_id,
                       r.rating, r.comment, r.is_approved, r.created_at
                FROM reviews r
                LEFT JOIN users u ON r.user_id = u.user_id
                ORDER BY r.created_at DESC
            """)
            reviews = await cursor.fetchall()
        
        data = [headers]
        for review in reviews:
            row = [
                review[0],  # ID
                review[1],  # User ID
                review[2] or "",  # Username
                "Автотехника" if review[3] == 'tech' else "Автоуслуги",  # Тип
                review[4],  # Item ID
                review[5],  # Рейтинг
                review[6] or "",  # Комментарий
                "Да" if review[7] else "Нет",  # Одобрен
                review[8][:19] if review[8] else ""  # Дата
            ]
            data.append(row)
        
        sheet.clear()
        if data:
            sheet.update('A1', data)
        
        print(f"Экспортировано {len(reviews)} отзывов в Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка экспорта отзывов: {e}")
        return False

# Периодическая загрузка из Google Sheets
async def load_admin_data_from_sheets():
    """Периодическая загрузка административных данных из Google Sheets"""
    print("Начинаем загрузку административных данных...")
    
    results = await asyncio.gather(
        sync_categories_from_sheet(),
        sync_user_bonuses_from_sheet(),
        sync_reviews_from_sheet(),
        return_exceptions=True
    )
    
    success_count = sum(1 for result in results if result is True)
    print(f"Загрузка завершена: {success_count}/3 таблиц")
    
    return success_count >= 2

# Мгновенная выгрузка административных данных
async def export_admin_data_to_sheets():
    """Мгновенная выгрузка административных данных"""
    print("Начинаем выгрузку административных данных...")
    
    results = await asyncio.gather(
        sync_categories_to_sheet(),
        sync_user_bonuses_to_sheet(),
        sync_reviews_to_sheet(),
        return_exceptions=True
    )
    
    success_count = sum(1 for result in results if result is True)
    print(f"Выгрузка завершена: {success_count}/3 таблиц")
    
    return success_count >= 2

# Мгновенная выгрузка при создании/изменении
async def instant_export_category(category_id: int):
    """Мгновенная выгрузка категории"""
    try:
        await sync_categories_to_sheet()
        print(f"✅ Категория {category_id} мгновенно выгружена")
    except Exception as e:
        print(f"❌ Ошибка выгрузки категории: {e}")

async def instant_export_user_bonus(user_id: int):
    """Мгновенная выгрузка бонусов пользователя"""
    try:
        await sync_user_bonuses_to_sheet()
        print(f"✅ Бонусы пользователя {user_id} мгновенно выгружены")
    except Exception as e:
        print(f"❌ Ошибка выгрузки бонусов: {e}")

async def instant_export_review(review_id: int):
    """Мгновенная выгрузка отзыва"""
    try:
        await sync_reviews_to_sheet()
        print(f"✅ Отзыв {review_id} мгновенно выгружен")
    except Exception as e:
        print(f"❌ Ошибка выгрузки отзыва: {e}")

async def scheduled_admin_tables_sync():
    """Периодическая загрузка административных данных в 17:00 МСК"""
    from datetime import datetime
    while True:
        try:
            # Ждем до 17:00 МСК
            now = datetime.now()
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            
            if now > target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Загрузка административных данных в 17:00
            await load_admin_data_from_sheets()
            
        except Exception as e:
            logging.error(f"Ошибка в scheduled_admin_tables_sync: {e}")
            await asyncio.sleep(3600)  # При ошибке ждем час

# Функция для добавления в main.py
async def start_admin_sheets_sync():
    """Запуск синхронизации административных таблиц"""
    asyncio.create_task(scheduled_admin_tables_sync())
    print("Запущена синхронизация административных таблиц")