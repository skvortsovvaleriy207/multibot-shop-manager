import gspread
import aiosqlite
from datetime import datetime
from config import CREDENTIALS_FILE, MAIN_SURVEY_SHEET_URL
import asyncio
import logging
from utils import retry_google_api

def get_google_sheets_client():
    return gspread.service_account(filename=CREDENTIALS_FILE)

@retry_google_api(retries=5, delay=5)
def _update_partner_sheet_sync(sheet_name, data, create_cols=34):
    """Синхронная функция для обновления листа партнеров с повторными попытками"""
    if not MAIN_SURVEY_SHEET_URL:
        logging.error("MAIN_SURVEY_SHEET_URL не указан")
        return False
        
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(MAIN_SURVEY_SHEET_URL)
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            logging.info(f"Лист '{sheet_name}' не найден, создаем новый")
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=create_cols)
        
        sheet.clear()
        if data:
            sheet.update('A1', data)
        return True
    except Exception as e:
        logging.error(f"Ошибка в _update_partner_sheet_sync для {sheet_name}: {e}")
        raise e

async def sync_partners_tech_to_sheet():
    """Синхронизация партнеров по автотехнике с Google Sheets"""
    try:
        headers = [
            "Дата опроса", "Telegram ID", "Username партнера", "Компания-партнер",
            "Год основания", "Местонахождение", "Email партнера", "Телефон партнера",
            "Товары партнера", "Экономическая проблема", "Социальная проблема",
            "Экологическая проблема", "Иная проблема", "Активный партнер",
            "Инвестор в экосистеме", "Бизнес-предложение", "ИТОГО бонусов",
            "Корректировка админом", "ТЕКУЩИЙ БАЛАНС", "Стоимость проблем",
            "Информация для админа", "Дата создания программы", "Руководитель/менеджер",
            "Описание программы", "Условия партнерства", "Заявки/заказы",
            "Статус заказов", "Партнерская ссылка", "Отзывы подписчиков",
            "Счет/карта партнера", "ID в магазине", "Контакты партнера",
            "Текущая активность", "Состояние аккаунта"
        ]
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT u.user_id, u.username, u.full_name, u.email, u.phone,
                       u.business, u.products_services, u.account_status, u.created_at,
                       u.location, u.financial_problem, u.social_problem, u.ecological_problem,
                       u.business_proposal, COALESCE(ub.bonus_total, 0), COALESCE(ub.current_balance, 0)
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                WHERE u.active_partner = 'Да' OR u.account_status = 'ПАРТНЕР'
                   OR EXISTS (SELECT 1 FROM auto_products ap WHERE ap.user_id = u.user_id)
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
            """)
            partners = await cursor.fetchall()
        
        data = [headers]
        for partner in partners:
            row = [
                datetime.now().strftime("%d/%m/%Y"),  # Дата опроса
                partner[0],  # Telegram ID
                partner[1] or "",  # Username партнера
                partner[5] or "",  # Компания-партнер
                "",  # Год основания
                partner[9] or "",  # Местонахождение
                partner[3] or "",  # Email партнера
                partner[4] or "",  # Телефон партнера
                partner[6] or "",  # Товары партнера
                partner[10] or "",  # Экономическая проблема
                partner[11] or "",  # Социальная проблема
                partner[12] or "",  # Экологическая проблема
                "",  # Иная проблема
                "Да",  # Активный партнер
                "",  # Инвестор в экосистеме
                partner[13] or "",  # Бизнес-предложение
                partner[14] or 0,  # ИТОГО бонусов
                0,  # Корректировка админом
                partner[15] or 0,  # ТЕКУЩИЙ БАЛАНС
                0,  # Стоимость проблем
                "",  # Информация для админа
                partner[8][:10] if partner[8] else "",  # Дата создания программы
                "",  # Руководитель/менеджер
                "",  # Описание программы
                "",  # Условия партнерства
                "",  # Заявки/заказы
                "",  # Статус заказов
                "",  # Партнерская ссылка
                "",  # Отзывы подписчиков
                "",  # Счет/карта партнера
                partner[0],  # ID в магазине
                f"@{partner[1]}" if partner[1] else "",  # Контакты партнера
                "",  # Текущая активность
                partner[7] or "Р"  # Состояние аккаунта
            ]
            data.append(row)
        
        await _update_partner_sheet_sync("Партнеры", data)
        
        print(f"Синхронизировано {len(partners)} партнеров по автотехнике")
        return True
        
    except Exception as e:
        print(f"Ошибка синхронизации партнеров по автотехнике: {e}")
        return False

async def sync_partners_services_to_sheet():
    """Синхронизация партнеров по автоуслугам с Google Sheets"""
    try:
        headers = [
            "Дата опроса", "Telegram ID", "Username партнера", "Компания-партнер",
            "Год основания", "Местонахождение", "Email партнера", "Телефон партнера",
            "Услуги партнера", "Экономическая проблема", "Социальная проблема",
            "Экологическая проблема", "Иная проблема", "Активный партнер",
            "Инвестор в экосистеме", "Бизнес-предложение", "ИТОГО бонусов",
            "Корректировка админом", "ТЕКУЩИЙ БАЛАНС", "Стоимость проблем",
            "Информация для админа", "Дата создания программы", "Руководитель/менеджер",
            "Описание программы", "Условия партнерства", "Заявки/заказы",
            "Статус заказов", "Партнерская ссылка", "Отзывы", "Счет/карта",
            "ID в магазине", "Контакты", "Активность", "Состояние"
        ]
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT DISTINCT u.user_id, u.username, u.full_name, u.email, u.phone,
                       u.business, u.products_services, u.account_status,
                       u.created_at, ub.bonus_total, ub.current_balance
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                LEFT JOIN auto_services as_ ON u.user_id = as_.user_id
                WHERE (u.active_partner = 'Да' OR u.account_status = 'ПАРТНЕР') 
                   AND as_.id IS NOT NULL
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
            """)
            partners = await cursor.fetchall()
        
        data = [headers]
        for partner in partners:
            row = [
                datetime.now().strftime("%d/%m/%Y"),
                partner[0], partner[1] or "", partner[5] or "", "", "",
                partner[3] or "", partner[4] or "", partner[6] or "",
                "", "", "", "", "Да", "", "", partner[9] or 0, 0,
                partner[10] or 0, 0, "", partner[8][:10] if partner[8] else "",
                "", "", "", "", "", "", "", "", partner[0],
                f"@{partner[1]}" if partner[1] else "", "", partner[7] or "Р"
            ]
            data.append(row)
        
        await _update_partner_sheet_sync("Партнеры (Услуги)", data)
        
        print(f"Синхронизировано {len(partners)} партнеров по автоуслугам")
        return True
        
    except Exception as e:
        print(f"Ошибка синхронизации партнеров по автоуслугам: {e}")
        return False

async def sync_investors_to_sheet():
    """Синхронизация инвесторов с Google Sheets"""
    try:
        headers = [
            "Дата опроса", "Telegram ID инвестора", "Username инвестора",
            "Компания-инвестор", "Год основания", "Местонахождение",
            "Email инвестора", "Телефон инвестора", "Инвестиционная программа",
            "Экономическая проблема", "Социальная проблема", "Экологическая проблема",
            "Иная проблема", "Активный партнер", "Инвестор в экосистеме",
            "Бизнес-предложение", "ИТОГО бонусов", "Корректировка админом",
            "ТЕКУЩИЙ БАЛАНС", "Стоимость проблем", "Информация для админа",
            "Дата создания программы", "Руководитель/менеджер", "Описание инвестиций",
            "Условия программы", "Заявки/заказы", "Статус заказов",
            "Инвестиционная ссылка", "Отзывы", "Счет/карта", "ID в магазине",
            "Контакты", "Состояние аккаунта"
        ]
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT u.user_id, u.username, u.full_name, u.email, u.phone,
                       u.business, u.products_services, u.account_status,
                       u.created_at, ub.bonus_total, ub.current_balance
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                WHERE u.investor_trader = 'Да' OR u.account_status = 'ИНВЕСТОР'
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
            """)
            investors = await cursor.fetchall()
        
        data = [headers]
        for investor in investors:
            row = [
                datetime.now().strftime("%d/%m/%Y"),
                investor[0], investor[1] or "", investor[5] or "",
                "", "", investor[3] or "", investor[4] or "",
                investor[6] or "", "", "", "", "", "", "Да", "",
                investor[9] or 0, 0, investor[10] or 0, 0, "",
                investor[8][:10] if investor[8] else "", "", "", "", "", "",
                "", "", "", investor[0], f"@{investor[1]}" if investor[1] else "",
                investor[7] or "Р"
            ]
            data.append(row)
        
        await _update_partner_sheet_sync("Инвесторы", data)
        
        print(f"Синхронизировано {len(investors)} инвесторов")
        return True
        
    except Exception as e:
        print(f"Ошибка синхронизации инвесторов: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_users_from_sheets():
    """Синхронизация данных пользователей из Google Sheets"""
    try:
        gc = get_google_sheets_client()
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).sheet1
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                user_id = row.get('Telegram ID')
                if not user_id:
                    continue
                
                await db.execute("""
                    UPDATE users SET
                        account_status = ?, bonus_total = ?, current_balance = ?,
                        active_partner = ?, investor_trader = ?, passive_subscriber = ?
                    WHERE user_id = ?
                """, (
                    row.get('Состояние аккаунта', 'Р'),
                    row.get('ИТОГО бонусов', 0),
                    row.get('ТЕКУЩИЙ БАЛАНС', 0),
                    row.get('Активный партнер', 'Нет'),
                    row.get('Инвестор в экосистеме', 'Нет'),
                    row.get('Пассивный подписчик', 'Нет'),
                    user_id
                ))
            await db.commit()
        
        print("Данные пользователей обновлены из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации пользователей: {e}")
        return False

async def sync_partners_from_sheets():
    """Синхронизация партнерских данных из Google Sheets"""
    try:
        results = await asyncio.gather(
            sync_partners_tech_from_sheet(),
            sync_partners_services_from_sheet(),
            sync_investors_from_sheet(),
            return_exceptions=True
        )
        success_count = sum(1 for result in results if result is True)
        print(f"Партнерские данные синхронизированы: {success_count}/3")
        return success_count >= 2
    except Exception as e:
        print(f"Ошибка синхронизации партнеров: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_partners_tech_from_sheet():
    """Синхронизация партнеров по автотехнике из Google Sheets"""
    try:
        gc = get_google_sheets_client()
        if not MAIN_SURVEY_SHEET_URL:
            return False
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).worksheet("Партнеры")
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                user_id = row.get('Telegram ID')
                if not user_id:
                    continue
                    
                await db.execute("""
                    UPDATE users SET
                        active_partner = ?, account_status = ?, bonus_total = ?, current_balance = ?
                    WHERE user_id = ?
                """, (
                    'Да' if row.get('Активный партнер') == 'Да' else 'Нет',
                    row.get('Состояние аккаунта', 'Р'),
                    row.get('ИТОГО бонусов', 0),
                    row.get('ТЕКУЩИЙ БАЛАНС', 0),
                    user_id
                ))
            await db.commit()
        return True
    except Exception as e:
        print(f"Ошибка синхронизации партнеров по автотехнике: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_partners_services_from_sheet():
    """Синхронизация партнеров по автоуслугам из Google Sheets"""
    try:
        gc = get_google_sheets_client()
        if not MAIN_SURVEY_SHEET_URL:
            return False
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).worksheet("Партнеры")
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                user_id = row.get('Telegram ID')
                if not user_id:
                    continue
                    
                await db.execute("""
                    UPDATE users SET
                        active_partner = ?, account_status = ?, bonus_total = ?, current_balance = ?
                    WHERE user_id = ?
                """, (
                    'Да' if row.get('Активный партнер') == 'Да' else 'Нет',
                    row.get('Состояние', 'Р'),
                    row.get('ИТОГО бонусов', 0),
                    row.get('ТЕКУЩИЙ БАЛАНС', 0),
                    user_id
                ))
            await db.commit()
        return True
    except Exception as e:
        print(f"Ошибка синхронизации партнеров по автоуслугам: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_investors_from_sheet():
    """Синхронизация инвесторов из Google Sheets"""
    try:
        gc = get_google_sheets_client()
        if not MAIN_SURVEY_SHEET_URL:
            return False
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).worksheet("Партнеры")
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                user_id = row.get('Telegram ID инвестора')
                if not user_id:
                    continue
                    
                await db.execute("""
                    UPDATE users SET
                        investor_trader = ?, account_status = ?, bonus_total = ?, current_balance = ?
                    WHERE user_id = ?
                """, (
                    'Да' if row.get('Инвестор в экосистеме') == 'Да' else 'Нет',
                    row.get('Состояние аккаунта', 'Р'),
                    row.get('ИТОГО бонусов', 0),
                    row.get('ТЕКУЩИЙ БАЛАНС', 0),
                    user_id
                ))
            await db.commit()
        return True
    except Exception as e:
        print(f"Ошибка синхронизации инвесторов: {e}")
        return False

# Мгновенная выгрузка партнерских данных
async def export_all_partner_data():
    """Мгновенная выгрузка партнерских данных"""
    print("Начинаем выгрузку партнерских данных...")
    
    results = await asyncio.gather(
        sync_partners_tech_to_sheet(),
        sync_partners_services_to_sheet(),
        sync_investors_to_sheet(),
        return_exceptions=True
    )
    
    success_count = sum(1 for result in results if result is True)
    print(f"Выгрузка партнерских данных завершена: {success_count}/3 операций выполнено")
    
    return success_count >= 2

# Мгновенная выгрузка при создании/изменении партнера
async def instant_export_partner(user_id: int, partner_type: str):
    """Мгновенная выгрузка партнера в Google Sheets"""
    try:
        if partner_type == 'tech':
            await sync_partners_tech_to_sheet()
        elif partner_type == 'service':
            await sync_partners_services_to_sheet()
        elif partner_type == 'investor':
            await sync_investors_to_sheet()
        print(f"✅ Партнер {user_id} ({partner_type}) мгновенно выгружен в Google Sheets")
    except Exception as e:
        print(f"❌ Ошибка мгновенной выгрузки партнера: {e}")

async def sync_partner_data_to_cards():
    """Выгрузка партнерских данных в карточки товаров/услуг согласно ТЗ п.3-5"""
    try:
        # Синхронизируем данные партнеров по автотехнике в карточки товаров
        await sync_tech_partners_to_product_cards()
        
        # Синхронизируем данные партнеров по автоуслугам в карточки услуг  
        await sync_service_partners_to_service_cards()
        
        # Синхронизируем данные инвесторов в профили
        await sync_investor_data_to_profiles()
        
        print("✅ Партнерские данные выгружены в карточки товаров/услуг")
        return True
    except Exception as e:
        logging.error(f"Ошибка выгрузки партнерских данных: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_tech_partners_to_product_cards():
    """Выгрузка данных партнеров по автотехнике в карточки товаров"""
    try:
        gc = get_google_sheets_client()
        if not MAIN_SURVEY_SHEET_URL:
            return False
            
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).worksheet("Партнеры")
        partner_data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for partner in partner_data:
                user_id = partner.get('Telegram ID')
                if not user_id:
                    continue
                    
                # Обновляем карточки товаров партнера
                await db.execute("""
                    UPDATE auto_products 
                    SET partner_info = ?, partner_conditions = ?, partner_status = ?
                    WHERE user_id = ?
                """, (
                    partner.get('Описание программы', ''),
                    partner.get('Условия партнерства', ''),
                    partner.get('Активный партнер', 'Нет'),
                    user_id
                ))
            await db.commit()
        
        print("Данные партнеров по автотехнике выгружены в карточки товаров")
        return True
    except Exception as e:
        print(f"Ошибка выгрузки партнеров автотехники: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_service_partners_to_service_cards():
    """Выгрузка данных партнеров по автоуслугам в карточки услуг"""
    try:
        gc = get_google_sheets_client()
        if not MAIN_SURVEY_SHEET_URL:
            return False
            
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).worksheet("Партнеры")
        partner_data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for partner in partner_data:
                user_id = partner.get('Telegram ID')
                if not user_id:
                    continue
                    
                # Обновляем карточки услуг партнера
                await db.execute("""
                    UPDATE auto_services 
                    SET partner_info = ?, partner_conditions = ?, partner_status = ?
                    WHERE user_id = ?
                """, (
                    partner.get('Описание программы', ''),
                    partner.get('Условия программы', ''),
                    partner.get('Активный партнер', 'Нет'),
                    user_id
                ))
            await db.commit()
        
        print("Данные партнеров по автоуслугам выгружены в карточки услуг")
        return True
    except Exception as e:
        print(f"Ошибка выгрузки партнеров автоуслуг: {e}")
        return False

@retry_google_api(retries=3, delay=5)
async def sync_investor_data_to_profiles():
    """Выгрузка данных инвесторов в профили согласно ТЗ п.5"""
    try:
        gc = get_google_sheets_client()
        if not MAIN_SURVEY_SHEET_URL:
            return False
            
        sheet = gc.open_by_url(MAIN_SURVEY_SHEET_URL).worksheet("Партнеры")
        investor_data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for investor in investor_data:
                user_id = investor.get('Telegram ID инвестора')
                if not user_id:
                    continue
                    
                # Обновляем профиль инвестора
                await db.execute("""
                    UPDATE users 
                    SET investor_trader = ?, investment_program = ?, investor_conditions = ?
                    WHERE user_id = ?
                """, (
                    'Да' if investor.get('Инвестор в экосистеме') == 'Да' else 'Нет',
                    investor.get('Описание инвестиций', ''),
                    investor.get('Условия программы', ''),
                    user_id
                ))
            await db.commit()
        
        print("Данные инвесторов выгружены в профили")
        return True
    except Exception as e:
        print(f"Ошибка выгрузки данных инвесторов: {e}")
        return False

# Функция для периодической синхронизации (каждый день в 17:00)
async def scheduled_partner_sync():
    """Запланированная выгрузка партнерских данных в 17:00 МСК согласно ТЗ"""
    while True:
        try:
            # Ждем до 17:00 МСК
            now = datetime.now()
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            
            if now > target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Выгружаем партнерские данные в карточки (ТЗ п.3-5)
            await sync_partner_data_to_cards()
            
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Ошибка в scheduled_partner_sync: {e}")
            await asyncio.sleep(3600)  # Ждем час при ошибке