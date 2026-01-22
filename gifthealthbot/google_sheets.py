import gspread
from datetime import datetime
import logging
import aiosqlite
from config import CREDENTIALS_FILE, MAIN_SURVEY_SHEET_URL
import asyncio
from collections import defaultdict

UNIFIED_SHEET_URL = MAIN_SURVEY_SHEET_URL
SHEET_MAIN = "Основная таблица"
SHEET_PARTNERS = "Партнеры"
SHEET_INVESTORS = "Инвесторы"
SHEET_PARSING = "Парсинги"
SHEET_INVITES = "Инвайты"

SHEET_PRODUCTS = "Товары"
SHEET_SERVICES = "Услуги"
SHEET_REQUESTS = "Заявки"  # Лист для заявки
SHEET_REAL_ORDERS = "Заказы"  # Лист для реальных заказов


def get_google_sheets_client():
    return gspread.service_account(filename=CREDENTIALS_FILE)


def get_main_survey_sheet_url():
    return MAIN_SURVEY_SHEET_URL


def init_unified_sheet():
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)

        sheets_config = [
            (SHEET_MAIN, 33,
             ["ДД/ММ/ГГ проведения опроса", "Телеграм ID", "Телеграм @username", "ФИО подписчика", "ДД/ММ/ГГ рождения",
              "Место жительства", "Email", "Мобильный телефон", "Текущая занятость", "Финансовая проблема",
              "Социальная проблема", "Экологическая проблема", "Пассивный подписчик (1.0)", "Активный партнер (2.0)",
              "Инвестор/трейдер (3.0)", "Бизнес-предложение", "ИТОГО бонусов", "Корректировка бонусов",
              "ТЕКУЩИЙ БАЛАНС", "Стоимость проблем", "Иная информация", "ДД/ММ/ГГ партнерства", "Количество рефералов",
              "Оплата за рефералов", "ДД/ММ/ГГ подписки", "Заявки всего/в работе", "Заказы-Покупки", "Заказы-Продажи",
              "Иная информация магазин", "Статус в магазине", "Бизнес подписчика", "Заказы/Товары/Услуги",
              "Статус аккаунта (Р/Б)"]),
            (SHEET_PARTNERS, 6,
             ["Тематика партнерства", "Команда партнера", "Активность партнера", "Каналы/чаты подписки",
              "Статус партнера", "Примечание"]),
            (SHEET_INVESTORS, 5,
             ["Команда инвестора", "Каналы/чаты подписки", "Активность инвестора", "Статус инвестора", "Примечание"]),
            (SHEET_PARSING, 13,
             ["ID", "Username", "Телефон", "Имя", "Иная информация", "Источник парсинга", "Тип ТГ чата",
              "Дата парсинга", "№ парсинга", "Исполнитель парсинга", "№ рассылки/инвайта", "№ в Основной таблице",
              "Примечание"]),
            (SHEET_INVITES, 12,
             ["ID", "Username", "Телефон", "Имя", "Иная информация", "Источник инвайта", "Дата инвайта",
              "№ рассылки/инвайта", "Исполнитель инвайта", "Канал/чат подписки", "№ в Основной таблице", "Примечание"]),

            (SHEET_PRODUCTS, 13,
             ["Дата и статус заказа", "ID заказчика", "№ в Основной таблице", "Категория товара", "Наименование товара",
              "Количество", "Данные поставщика", "№, дата соглашения", "Оплата заказчиком",
              "№, дата документа поставки", "Иная информация", "Статус товара/поставщика", "Примечание"]),
            (SHEET_SERVICES, 13,
             ["Дата и статус заказа", "ID заказчика", "№ в Основной таблице", "Категория услуги", "Наименование услуги",
              "Объем услуги", "Данные поставщика", "№, дата соглашения", "Оплата заказчиком",
              "№, дата документа выполнения", "Иная информация, отзывы", "Статус услуги/поставщика", "Примечание"]),
            (SHEET_REQUESTS, 29,
             ["ID заявки", "Дата создания", "ID пользователя", "Username", "Операция", "Тип заявки", "Категория",
              "Класс товара", "Тип товара", "Вид товара", "Название", "Назначение", "Имя", "Дата создания товара",
              "Состояние", "Спецификации", "Преимущества", "Доп. информация", "Изображения", "Цена", "Наличие",
              "Подробные характеристики", "Отзывы", "Рейтинг", "Информация о доставке", "Информация о поставщике",
              "Статистика", "Сроки", "Теги", "Контакты", "Статус"]),
            (SHEET_REAL_ORDERS, 10,
             ["ID заказа", "Дата заказа", "Тип заказа", "ID товара", "ID продавца", "ID покупателя",
              "Статус", "Дата изменения", "Заметки", "Сумма"])
        ]

        for sheet_name, cols, headers in sheets_config:
            try:
                sheet = spreadsheet.worksheet(sheet_name)
            except:
                sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=cols)
            sheet.update(f'A1:{chr(64 + cols)}1', [headers])

        return True
    except Exception as e:
        logging.error(f"Ошибка инициализации: {e}")
        return False


async def sync_with_google_sheets():
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)
        sheet = spreadsheet.worksheet(SHEET_MAIN)
        gsheet_data = sheet.get_all_records()
        logging.info(f"Fetched {len(gsheet_data)} rows from Google Sheets")

        # Повторные попытки при блокировке БД
        for attempt in range(3):
            try:
                async with aiosqlite.connect("bot_database.db", timeout=30) as db:
                    break
            except Exception as e:
                if "database is locked" in str(e) and attempt < 2:
                    await asyncio.sleep(2)
                    continue
                raise

        async with aiosqlite.connect("bot_database.db", timeout=30) as db:
            cursor = await db.execute("SELECT user_id, has_completed_survey FROM users WHERE user_id != 0")
            db_users = await cursor.fetchall()
            db_user_ids = {user[0] for user in db_users}
            db_user_survey_status = {user[0]: user[1] for user in db_users}
            changes = defaultdict(dict)
            # Дедупликация данных из Google Sheets
            unique_rows = {}
            for row in gsheet_data:
                user_id_raw = row.get('Telegram ID') or row.get('User ID')
                if not user_id_raw or str(user_id_raw).strip() == '':
                    continue
                try:
                    user_id = int(str(user_id_raw).strip())
                    unique_rows[user_id] = row
                except ValueError:
                    continue
            
            for user_id, row in unique_rows.items():
                # Check for recent local update to prevent overwrite
                # If local data was updated less than 10 minutes ago, skip this sync cycle
                try:
                    cursor = await db.execute("SELECT updated_at FROM users WHERE user_id = ?", (user_id,))
                    time_row = await cursor.fetchone()
                    if time_row and time_row[0]:
                        try:
                            last_update = datetime.fromisoformat(time_row[0])
                            if (datetime.now() - last_update).total_seconds() < 600: # 10 minutes
                                logging.info(f"Skipping sync for user {user_id} due to recent local update ({time_row[0]})")
                                continue
                        except ValueError:
                            pass # Invalid date format, proceed with sync
                except Exception as e:
                    logging.error(f"Error checking updated_at for user {user_id}: {e}")

                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                db_user = await cursor.fetchone()
                
                if db_user:
                    db_fields = {
                        'username': str(db_user[1] or '').strip(),
                        'full_name': str(db_user[7] or '').strip(),
                        'birth_date': str(db_user[8] or '').strip(),
                        'location': str(db_user[9] or '').strip(),
                        'email': str(db_user[10] or '').strip(),
                        'phone': str(db_user[11] or '').strip(),
                        'employment': str(db_user[12] or '').strip(),
                        'financial_problem': str(db_user[13] or '').strip(),
                        'social_problem': str(db_user[14] or '').strip(),
                        'ecological_problem': str(db_user[15] or '').strip(),
                        'passive_subscriber': str(db_user[16] or '').strip(),
                        'active_partner': str(db_user[17] or '').strip(),
                        'investor_trader': str(db_user[18] or '').strip(),
                        'business_proposal': str(db_user[19] or '').strip(),
                        'bonus_total': float(db_user[20] or 0),
                        'current_balance': float(db_user[22] or 0)
                    }
                    
                    gsheet_fields = {
                        'username': str(row.get('Username', '')).strip(),
                        'full_name': str(row.get('ФИО', '')).strip(),
                        'birth_date': str(row.get('Дата рождения', '')).strip(),
                        'location': str(row.get('Место жительства', '')).strip(),
                        'email': str(row.get('Email', '')).strip(),
                        'phone': str(row.get('Телефон', '')).strip(),
                        'employment': str(row.get('Занятость', '')).strip(),
                        'financial_problem': str(row.get('Финансовая проблема', '')).strip(),
                        'social_problem': str(row.get('Социальная проблема', '')).strip(),
                        'ecological_problem': str(row.get('Экологическая проблема', '')).strip(),
                        'passive_subscriber': str(row.get('Пассивный подписчик', '')).strip(),
                        'active_partner': str(row.get('Активный партнер', '')).strip(),
                        'investor_trader': str(row.get('Инвестор/трейдер', '')).strip(),
                        'business_proposal': str(row.get('Бизнес-предложение', '')).strip(),
                        'bonus_total': _safe_float(row.get('Сумма бонусов', 0)),
                        'current_balance': _safe_float(row.get('Текущий баланс', 0))
                    }

                    for field in gsheet_fields:
                        val_db = db_fields[field]
                        val_sheet = gsheet_fields[field]
                        
                        # Сравнение с учетом типов
                        is_diff = False
                        if isinstance(val_db, float) or isinstance(val_sheet, float):
                             try:
                                 if abs(float(val_db) - float(val_sheet)) > 0.01:
                                     is_diff = True
                             except:
                                 if str(val_db) != str(val_sheet):
                                     is_diff = True
                        else:
                            if str(val_db) != str(val_sheet):
                                is_diff = True
                                
                        if is_diff:
                            changes[user_id][field] = {
                                'old': val_db,
                                'new': val_sheet
                            }
                try:
                    has_completed_survey = db_user_survey_status.get(user_id, 0)
                    
                    # Если статус 0 (новый или не прошел), проверяем наличие данных опроса в таблице
                    if has_completed_survey == 0:
                        has_survey_data = any([
                            row.get('Финансовая проблема'),
                            row.get('Социальная проблема'),
                            row.get('Экологическая проблема')
                        ])
                        if has_survey_data:
                            has_completed_survey = 1
                    user_data = {
                        "user_id": user_id,
                        "username": row.get('Username', ''),
                        "full_name": row.get('ФИО', ''),
                        "birth_date": row.get('Дата рождения', ''),
                        "location": row.get('Место жительства', ''),
                        "email": row.get('Email', ''),
                        "phone": row.get('Телефон', ''),
                        "employment": row.get('Занятость', ''),
                        "financial_problem": row.get('Финансовая проблема', ''),
                        "social_problem": row.get('Социальная проблема', ''),
                        "ecological_problem": row.get('Экологическая проблема', ''),
                        "passive_subscriber": row.get('Пассивный подписчик', ''),
                        "active_partner": row.get('Активный партнер', ''),
                        "investor_trader": row.get('Инвестор/трейдер', ''),
                        "business_proposal": row.get('Бизнес-предложение', ''),
                        "bonus_total": float(row.get('Сумма бонусов') or 0),
                        "current_balance": float(row.get('Текущий баланс') or 0),
                        "updated_at": datetime.now().isoformat(),
                        "has_completed_survey": has_completed_survey,
                        "account_status": row.get("Статус аккаунта", "Р")
                    }
                    full_name = user_data.get("full_name", "").split()
                    if len(full_name) > 0:
                        user_data["first_name"] = full_name[0]
                    if len(full_name) > 1:
                        user_data["last_name"] = " ".join(full_name[1:])
                    columns = ", ".join(user_data.keys())
                    placeholders = ", ".join([f":{key}" for key in user_data.keys()])
                    await db.execute(f"INSERT OR REPLACE INTO users ({columns}) VALUES ({placeholders})", user_data)
                    cursor = await db.execute("SELECT id FROM user_bonuses WHERE user_id = ?", (user_id,))
                    bonus_record = await cursor.fetchone()
                    if bonus_record:
                        await db.execute(
                            """
                            UPDATE user_bonuses 
                            SET bonus_total = ?, current_balance = ?, updated_at = ?
                            WHERE user_id = ?
                            """,
                            (user_data["bonus_total"], user_data["current_balance"], user_data["updated_at"], user_id))
                    else:
                        await db.execute(
                            """
                            INSERT INTO user_bonuses 
                            (user_id, bonus_total, current_balance, updated_at)
                            VALUES (?, ?, ?, ?)
                            """,
                            (user_id, user_data["bonus_total"], user_data["current_balance"], user_data["updated_at"]))
                    print(f"[SYNC] Добавлен/обновлён user_id: {user_id}, username: {user_data.get('username', '')}")
                except Exception as e:
                    logging.error(f"Error processing row {row}: {e}")
                    continue
            await db.commit()
            await db.commit()
            # Фильтруем изменения, исключая служебного пользователя с ID=0
            filtered_changes = {uid: chg for uid, chg in changes.items() if uid != 0}
            return filtered_changes
    except Exception as e:
        logging.error(f"Error syncing with Google Sheets: {e}")
        return None


async def sync_db_to_google_sheets():
    try:
        # Сначала агрегируем статистику
        from data_aggregator import aggregate_user_statistics
        await aggregate_user_statistics()

        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)
        sheet = spreadsheet.worksheet(SHEET_MAIN)

        # Получаем данные из базы данных
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT DISTINCT
                    sa1.answer_text as survey_date,
                    u.user_id,
                    sa3.answer_text as username,
                    sa4.answer_text as full_name,
                    sa5.answer_text as birth_date,
                    sa6.answer_text as location,
                    sa7.answer_text as email,
                    sa8.answer_text as phone,
                    sa9.answer_text as employment,
                    sa10.answer_text as financial_problem,
                    sa11.answer_text as social_problem,
                    sa12.answer_text as ecological_problem,
                    sa13.answer_text as passive_subscriber,
                    sa14.answer_text as active_partner,
                    sa15.answer_text as investor_trader,
                    sa16.answer_text as business_proposal,
                    ub.bonus_total,
                    ub.bonus_adjustment,
                    ub.current_balance,
                    u.problem_cost,
                    u.notes,
                    u.partnership_date,
                    COALESCE(u.total_referrals, u.referral_count, 0) as referral_count,
                    COALESCE(u.referral_earnings, u.referral_payment, 0) as referral_payment,
                    u.subscription_date,
                    u.subscription_date,
                    u.requests_text,
                    u.purchases,
                    u.sales,
                    u.requisites,
                    u.shop_id,
                    u.business,
                    u.products_services,
                    u.account_status
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                LEFT JOIN survey_answers sa1 ON u.user_id = sa1.user_id AND sa1.question_id = 1
                LEFT JOIN survey_answers sa3 ON u.user_id = sa3.user_id AND sa3.question_id = 3
                LEFT JOIN survey_answers sa4 ON u.user_id = sa4.user_id AND sa4.question_id = 4
                LEFT JOIN survey_answers sa5 ON u.user_id = sa5.user_id AND sa5.question_id = 5
                LEFT JOIN survey_answers sa6 ON u.user_id = sa6.user_id AND sa6.question_id = 6
                LEFT JOIN survey_answers sa7 ON u.user_id = sa7.user_id AND sa7.question_id = 7
                LEFT JOIN survey_answers sa8 ON u.user_id = sa8.user_id AND sa8.question_id = 8
                LEFT JOIN survey_answers sa9 ON u.user_id = sa9.user_id AND sa9.question_id = 9
                LEFT JOIN survey_answers sa10 ON u.user_id = sa10.user_id AND sa10.question_id = 10
                LEFT JOIN survey_answers sa11 ON u.user_id = sa11.user_id AND sa11.question_id = 11
                LEFT JOIN survey_answers sa12 ON u.user_id = sa12.user_id AND sa12.question_id = 12
                LEFT JOIN survey_answers sa13 ON u.user_id = sa13.user_id AND sa13.question_id = 13
                LEFT JOIN survey_answers sa14 ON u.user_id = sa14.user_id AND sa14.question_id = 14
                LEFT JOIN survey_answers sa15 ON u.user_id = sa15.user_id AND sa15.question_id = 15
                LEFT JOIN survey_answers sa16 ON u.user_id = sa16.user_id AND sa16.question_id = 16
                WHERE u.user_id != 0
                GROUP BY u.user_id
                ORDER BY MAX(ub.updated_at) DESC
            """)
            users = await cursor.fetchall()

        headers = [
            "Дата опроса", "Telegram ID", "Username", "ФИО", "Дата рождения",
            "Место жительства", "Email", "Телефон", "Занятость",
            "Финансовая проблема", "Социальная проблема", "Экологическая проблема",
            "Пассивный подписчик", "Активный партнер", "Инвестор/трейдер",
            "Бизнес-предложение", "Сумма бонусов", "Корректировка бонусов",
            "Текущий баланс", "Стоимость проблем", "Примечания",
            "Дата партнерства", "Количество рефералов", "Оплата за рефералов",
            "Дата подписки", "Заявки всего/в работе", "Заказы-Покупки", "Заказы-Продажи",
            "Реквизиты", "ID в магазине", "Бизнес", "Товары/услуги", "Статус аккаунта"
        ]

        data = [headers]
        for user in users:
            data.append(list(user))

        sheet.clear()
        sheet.update('A1', data)

        return True
    except Exception as e:
        logging.error(f"Error syncing DB to Google Sheets: {e}")
        return False


# google_sheets_sync.py
import gspread
from datetime import datetime
import logging
from typing import Dict, Any, Optional
import aiosqlite
from config import BESTHOME_SURVEY_SHEET_URL, CREDENTIALS_FILE


async def sync_from_sheets_to_db() -> Dict[str, Any]:
    """
    Загружает данные из Google Sheets в базу данных текущего бота
    Только для Основной таблицы

    Returns:
        dict: Результат синхронизации
    """
    try:
        # Авторизация в Google Sheets
        client = gspread.service_account(filename=CREDENTIALS_FILE)

        # Открываем таблицу besthome
        spreadsheet = client.open_by_url(BESTHOME_SURVEY_SHEET_URL)
        worksheet = spreadsheet.worksheet("Основная таблица")

        # Получаем все данные из таблицы
        all_data = worksheet.get_all_records()

        if not all_data:
            return {
                "success": False,
                "message": "В таблице нет данных",
                "synced_count": 0
            }

        # Подключаемся к базе данных
        async with aiosqlite.connect("bot_database.db") as db:
            synced_count = 0

            for row in all_data:
                try:
                    # Получаем ID пользователя (пробуем разные названия столбцов)
                    telegram_id = None

                    if 'Telegram ID' in row:
                        telegram_id = row['Telegram ID']
                    elif 'User ID' in row:
                        telegram_id = row['User ID']
                    elif 'ID' in row:
                        telegram_id = row['ID']

                    # Пропускаем строки без ID
                    if not telegram_id or str(telegram_id).strip() == '':
                        continue

                    user_id = int(str(telegram_id).strip())

                    # Пропускаем нулевой ID (служебная запись)
                    if user_id == 0:
                        continue

                    # Формируем данные пользователя для вставки/обновления
                    user_data = {
                        "user_id": user_id,
                        "username": row.get('Username', ''),
                        "full_name": row.get('ФИО', ''),
                        "birth_date": row.get('Дата рождения', ''),
                        "location": row.get('Место жительства', ''),
                        "email": row.get('Email', ''),
                        "phone": row.get('Телефон', ''),
                        "employment": row.get('Занятость', ''),
                        "financial_problem": row.get('Финансовая проблема', ''),
                        "social_problem": row.get('Социальная проблема', ''),
                        "ecological_problem": row.get('Экологическая проблема', ''),
                        "passive_subscriber": row.get('Пассивный подписчик', ''),
                        "active_partner": row.get('Активный партнер', ''),
                        "investor_trader": row.get('Инвестор/трейдер', ''),
                        "business_proposal": row.get('Бизнес-предложение', ''),
                        "bonus_total": _safe_float(row.get('Сумма бонусов', 0)),
                        "current_balance": _safe_float(row.get('Текущий баланс', 0)),
                        "problem_cost": row.get('Стоимость проблем', ''),
                        "notes": row.get('Примечания', ''),
                        "account_status": row.get('Статус аккаунта', 'Р'),
                        "updated_at": datetime.now().isoformat()
                    }

                    # Извлекаем имя и фамилию из полного имени
                    full_name = user_data.get("full_name", "").split()
                    if len(full_name) > 0:
                        user_data["first_name"] = full_name[0]
                    if len(full_name) > 1:
                        user_data["last_name"] = " ".join(full_name[1:])

                    # Определяем, заполнил ли пользователь опрос
                    # Если есть какие-то данные в анкете, считаем опрос заполненным
                    has_survey_data = any([
                        user_data["financial_problem"],
                        user_data["social_problem"],
                        user_data["ecological_problem"]
                    ])
                    user_data["has_completed_survey"] = 1 if has_survey_data else 0

                    # Проверяем существование пользователя
                    cursor = await db.execute(
                        "SELECT user_id FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    user_exists = await cursor.fetchone() is not None

                    if user_exists:
                        # Обновляем существующего пользователя
                        update_fields = []
                        update_values = []

                        for key, value in user_data.items():
                            if key != "user_id":  # user_id не обновляем
                                update_fields.append(f"{key} = ?")
                                update_values.append(value)

                        update_values.append(user_id)  # для WHERE условия

                        update_query = f"""
                            UPDATE users 
                            SET {', '.join(update_fields)}
                            WHERE user_id = ?
                        """

                        await db.execute(update_query, update_values)
                        logging.info(f"Обновлён пользователь {user_id}")

                    else:
                        # Вставляем нового пользователя
                        columns = list(user_data.keys())
                        placeholders = ", ".join(["?" for _ in columns])
                        column_names = ", ".join(columns)

                        insert_query = f"""
                            INSERT INTO users ({column_names}) 
                            VALUES ({placeholders})
                        """

                        await db.execute(insert_query, list(user_data.values()))
                        logging.info(f"Добавлен пользователь {user_id}")

                    synced_count += 1

                except Exception as e:
                    logging.error(f"Ошибка обработки строки: {e}")
                    continue

            await db.commit()

            return {
                "success": True,
                "message": f"Синхронизация завершена. Обработано {synced_count} пользователей",
                "synced_count": synced_count,
                "total_rows": len(all_data)
            }

    except Exception as e:
        logging.error(f"Ошибка синхронизации из Google Sheets: {e}")
        return {
            "success": False,
            "message": f"Ошибка синхронизации: {str(e)}",
            "synced_count": 0
        }


def _safe_float(value) -> float:
    """Безопасное преобразование в float"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

async def sync_db_to_main_survey_sheet():
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)
        sheet = spreadsheet.worksheet(SHEET_MAIN)

        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT DISTINCT
                    sa1.answer_text,
                    CAST(u.user_id AS TEXT),
                    sa3.answer_text,
                    sa4.answer_text,
                    sa5.answer_text,
                    sa6.answer_text,
                    sa7.answer_text,
                    sa8.answer_text,
                    sa9.answer_text,
                    sa10.answer_text,
                    sa11.answer_text,
                    sa12.answer_text,
                    sa13.answer_text,
                    sa14.answer_text,
                    sa15.answer_text,
                    sa16.answer_text,
                    ub.bonus_total,
                    ub.bonus_adjustment,
                    ub.current_balance,
                    u.problem_cost,
                    u.notes,
                    u.partnership_date,
                    u.referral_count,
                    u.referral_payment,
                    u.subscription_date,
                    u.subscription_payment_date,
                    u.purchases,
                    u.sales,
                    u.requisites,
                    u.shop_id,
                    u.business,
                    u.products_services,
                    u.account_status
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                LEFT JOIN survey_answers sa1 ON u.user_id = sa1.user_id AND sa1.question_id = 1
                LEFT JOIN survey_answers sa3 ON u.user_id = sa3.user_id AND sa3.question_id = 3
                LEFT JOIN survey_answers sa4 ON u.user_id = sa4.user_id AND sa4.question_id = 4
                LEFT JOIN survey_answers sa5 ON u.user_id = sa5.user_id AND sa5.question_id = 5
                LEFT JOIN survey_answers sa6 ON u.user_id = sa6.user_id AND sa6.question_id = 6
                LEFT JOIN survey_answers sa7 ON u.user_id = sa7.user_id AND sa7.question_id = 7
                LEFT JOIN survey_answers sa8 ON u.user_id = sa8.user_id AND sa8.question_id = 8
                LEFT JOIN survey_answers sa9 ON u.user_id = sa9.user_id AND sa9.question_id = 9
                LEFT JOIN survey_answers sa10 ON u.user_id = sa10.user_id AND sa10.question_id = 10
                LEFT JOIN survey_answers sa11 ON u.user_id = sa11.user_id AND sa11.question_id = 11
                LEFT JOIN survey_answers sa12 ON u.user_id = sa12.user_id AND sa12.question_id = 12
                LEFT JOIN survey_answers sa13 ON u.user_id = sa13.user_id AND sa13.question_id = 13
                LEFT JOIN survey_answers sa14 ON u.user_id = sa14.user_id AND sa14.question_id = 14
                LEFT JOIN survey_answers sa15 ON u.user_id = sa15.user_id AND sa15.question_id = 15
                LEFT JOIN survey_answers sa16 ON u.user_id = sa16.user_id AND sa16.question_id = 16
                WHERE u.user_id != 0
                GROUP BY u.user_id
                ORDER BY MAX(ub.updated_at) DESC
            """)
            users = await cursor.fetchall()

        headers = [
            "Дата опроса", "Telegram ID", "Username", "ФИО", "Дата рождения",
            "Место жительства", "Email", "Телефон", "Занятость",
            "Финансовая проблема", "Социальная проблема", "Экологическая проблема",
            "Пассивный подписчик", "Активный партнер", "Инвестор/трейдер",
            "Бизнес-предложение", "Сумма бонусов", "Корректировка бонусов",
            "Текущий баланс", "Стоимость проблем", "Примечания",
            "Дата партнерства", "Количество рефералов", "Оплата за рефералов",
            "Дата подписки", "Дата оплаты подписки", "Покупки", "Продажи",
            "Реквизиты", "ID в магазине", "Бизнес", "Товары/услуги", "Статус аккаунта"
        ]

        data = [headers]
        for user in users:
            data.append(list(user))

        sheet.clear()
        sheet.update('A1', data)

        return True
    except Exception as e:
        logging.error(f"Error syncing DB to Main Survey Google Sheets: {e}")
        return False


async def sync_sheets_to_db():
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)

        async with aiosqlite.connect("bot_database.db") as db:
            products_sheet = spreadsheet.worksheet(SHEET_PRODUCTS)
            products_data = products_sheet.get_all_records()

            for row in products_data:
                if row.get('ID заказчика'):
                    await db.execute("""
                        UPDATE auto_products SET
                            title = ?, description = ?, price = ?, status = ?,
                            specifications = ?, delivery_info = ?, warranty_info = ?
                        WHERE user_id = ? AND title = ?
                    """, (
                        row.get('Наименование товара'),
                        row.get('Иная информация'),
                        row.get('Оплата заказчиком'),
                        row.get('Статус товара/поставщика'),
                        row.get('Количество'),
                        row.get('№, дата документа поставки'),
                        row.get('Примечание'),
                        row.get('ID заказчика'),
                        row.get('Наименование товара')
                    ))

            services_sheet = spreadsheet.worksheet(SHEET_SERVICES)
            services_data = services_sheet.get_all_records()

            for row in services_data:
                if row.get('ID заказчика'):
                    await db.execute("""
                        UPDATE auto_services SET
                            title = ?, description = ?, price = ?, status = ?,
                            duration = ?, location = ?
                        WHERE user_id = ? AND title = ?
                    """, (
                        row.get('Наименование услуги'),
                        row.get('Иная информация, отзывы'),
                        row.get('Оплата заказчиком'),
                        row.get('Статус услуги/поставщика'),
                        row.get('Объем услуги'),
                        row.get('Примечание'),
                        row.get('ID заказчика'),
                        row.get('Наименование услуги')
                    ))

            await db.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка синхронизации из таблицы в БД: {e}")
        return False


async def sync_order_requests_to_sheets():
    """Синхронизация заявок с Google Sheets с учетом разных типов заявок"""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)

        # Создаем или получаем лист для заявок
        try:
            orders_sheet = spreadsheet.worksheet("Заявки")
            print(f"✅ Лист 'Заявки' найден")

            # Получаем заголовки и проверяем их
            orders_sheet.update('A1', [[
                "ID заказа", "Дата заказа", "Тип заказа", "ID товара/услуги", "Название",
                "Telegram ID покупателя", "Username покупателя", "Telegram ID продавца", "Username продавца",
                "Статус заказа", "Цена", "Примечания"
            ]])
            print("✅ Заголовки таблицы обновлены")
        except Exception as e:
            orders_sheet = spreadsheet.add_worksheet(title="Заявки", rows=1000, cols=12)
            headers = [
                "ID заказа", "Дата заказа", "Тип заказа", "ID товара/услуги", "Название",
                "Telegram ID покупателя", "Username покупателя", "Telegram ID продавца", "Username продавца",
                "Статус заказа", "Цена", "Примечания"
            ]
            orders_sheet.update('A1', [headers])
            print(f"✅ Создан новый лист 'Заявки' с заголовками")
            existing_headers = headers

        # Получаем все данные из базы данных для товаров и предложений
        all_requests = []

        async with aiosqlite.connect("bot_database.db") as db:
            # 1. Получаем заявки на товары и предложения
            cursor = await db.execute("""
                SELECT 
                    'P' || r.id as order_id,
                    r.created_at as order_date,
                    CASE 
                        WHEN r.item_type = 'product' THEN 'Товар'
                        WHEN r.item_type = 'offer' THEN 'Предложение'
                        WHEN r.item_type = 'cart_order' THEN 'Заказ из корзины'
                        ELSE r.item_type
                    END as order_type,
                    COALESCE(r.id, '') as item_id,
                    COALESCE(r.title, 'Без названия') as title,
                    r.user_id as buyer_id,
                    COALESCE(u.username, 'Не указан') as buyer_username,
                    '' as seller_id, -- Пока нет данных о продавце в order_requests
                    '' as seller_username, -- Пока нет данных
                    CASE 
                        WHEN r.status = 'new' THEN 'Новый'
                        WHEN r.status = 'active' THEN 'Активен'
                        WHEN r.status = 'completed' THEN 'Завершен'
                        WHEN r.status = 'processing' THEN 'В обработке'
                        ELSE r.status
                    END as status,
                    COALESCE(r.price, '0') as price,
                    COALESCE(r.additional_info, '') as notes
                FROM order_requests r
                LEFT JOIN users u ON r.user_id = u.user_id
                WHERE r.item_type IN ('product', 'offer', 'cart_order')
                ORDER BY r.id ASC
            """)
            product_requests = await cursor.fetchall()
            print(f"[DEBUG] Найдено {len(product_requests)} заявок для выгрузки (включая корзину)")
            all_requests.extend(product_requests)

            # 2. Получаем заявки на услуги
            cursor = await db.execute("""
                SELECT 
                    'S' || s.id as order_id,
                    s.created_at as order_date,
                    'Услуга' as order_type,
                    COALESCE(s.id, '') as item_id,
                    COALESCE(s.title, 'Без названия') as title,
                    s.user_id as buyer_id,
                    COALESCE(u.username, 'Не указан') as buyer_username,
                    '' as seller_id,
                    '' as seller_username,
                    CASE 
                        WHEN s.status = 'new' THEN 'Новый'
                        WHEN s.status = 'active' THEN 'Активен'
                        WHEN s.status = 'completed' THEN 'Завершен'
                        ELSE s.status
                    END as status,
                    COALESCE(s.price, '0') as price,
                    COALESCE(s.additional_info, '') as notes
                FROM service_orders s
                LEFT JOIN users u ON s.user_id = u.user_id
                ORDER BY s.id ASC
            """)
            service_requests = await cursor.fetchall()
            all_requests.extend(service_requests)

        print(f"📊 В базе данных найдено всего {len(all_requests)} записей")
        print(f"   • Товары и предложения: {len(product_requests)}")
        print(f"   • Услуги: {len(service_requests)}")

        # Получаем текущие данные из Google Sheets
        # Переписываем таблицу полностью для гарантии соответствия схеме (12 колонок)
        
        if all_requests:
            # Преобразуем данные в правильный формат для записи
            all_data_formatted = [list(req) for req in all_requests]
            
            # Очищаем таблицу, но оставляем заголовки (первая строка)
            orders_sheet.clear()
            
            # Восстанавливаем заголовки
            headers = [
                "ID заказа", "Дата заказа", "Тип заказа", "ID товара/услуги", "Название",
                "Telegram ID покупателя", "Username покупателя", "Telegram ID продавца", "Username продавца",
                "Статус заказа", "Цена", "Примечания"
            ]
            orders_sheet.update('A1', [headers])
            
            # Записываем все данные начиная со 2-й строки
            orders_sheet.update('A2', all_data_formatted)
            
            print(f"✅ Таблица полностью обновлена с {len(all_requests)} записями")
        else:
            # Если данных нет, просто чистим всё кроме заголовков (или восстанавливаем их)
            orders_sheet.clear()
            headers = [
                "ID заказа", "Дата заказа", "Тип заказа", "ID товара/услуги", "Название",
                "Telegram ID покупателя", "Username покупателя", "Telegram ID продавца", "Username продавца",
                "Статус заказа", "Цена", "Примечания"
            ]
            orders_sheet.update('A1', [headers])
            print("ℹ️ В базе данных нет записей, таблица очищена")

        return True

    except Exception as e:
        print(f"❌ Ошибка при синхронизации с Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False




async def auto_fill_cart_from_orders(user_id: int):
    """Автоматическое заполнение корзины из активных заявок пользователя"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # Проверяем, не заполнена ли уже корзина
            cursor = await db.execute("""
                SELECT COUNT(*) FROM cart_order WHERE user_id = ?
            """, (user_id,))
            cart_count = (await cursor.fetchone())[0]

            # Всегда проверяем и добавляем новые активные заявки
            print(f"🛒 Проверяем активные заявки для пользователя {user_id}")

            added_count = 0

            # 1. Получаем активные заявки на товары и предложения пользователя
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, item_type 
                FROM order_requests 
                WHERE user_id = ? AND status IN ('active', 'new')
                ORDER BY created_at DESC
            """, (user_id,))
            product_orders = await cursor.fetchall()

            # 2. Получаем активные заявки на услуги пользователя
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, 'service' as item_type 
                FROM service_orders 
                WHERE user_id = ? AND status IN ('active', 'new')
                ORDER BY created_at DESC
            """, (user_id,))
            service_orders = await cursor.fetchall()

            # Объединяем все заявки
            all_orders = product_orders + service_orders

            if not all_orders:
                print(f"ℹ️ Нет активных заявок для пользователя {user_id}")
                return False

            # Добавляем каждую заявку в корзину
            for order in all_orders:
                order_id, title, price, category, operation, item_type = order

                # Проверяем, нет ли уже этой заявки в корзине
                cursor = await db.execute("""
                    SELECT id FROM cart_order 
                    WHERE user_id = ? AND item_type = ? AND item_id = ?
                """, (user_id, "order_request", order_id))
                existing = await cursor.fetchone()

                if not existing:
                    # Определяем источник для корректного удаления
                    source_table = "service_orders" if item_type == "service" else "order_requests"

                    # Добавляем заявку в корзину
                    await db.execute("""
                        INSERT INTO cart_order (
                            user_id, item_type, item_id, quantity, selected_options, price, added_at, source_table
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        "order_request",
                        order_id,
                        1,  # Количество по умолчанию
                        "",  # Без опций по умолчанию
                        price or "0",
                        datetime.now().isoformat(),
                        source_table  # Сохраняем источник для корректного удаления
                    ))
                    added_count += 1
                    print(f"✅ Заявка {order_id} ({item_type}) добавлена в корзину пользователя {user_id}")

            if added_count > 0:
                await db.commit()
                print(f"✅ В корзину добавлено {added_count} новых заявок для пользователя {user_id}")
                return True
            else:
                print(f"ℹ️ Нет новых заявок для добавления в корзину пользователя {user_id}")
                return False

    except Exception as e:
        print(f"❌ Ошибка при заполнении корзины: {e}")
        import traceback
        traceback.print_exc()
        return False


async def auto_add_to_cart_from_requests():
    """Автоматическое добавление новых активных заявок в корзину для всех пользователей"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # Получаем новые активные заявки всех пользователей
            all_new_requests = []

            # 1. Заявки на товары и предложения
            cursor = await db.execute("""
                SELECT id, user_id, title, price, 'product/offer' as source 
                FROM order_requests 
                WHERE status IN ('active', 'new')
                ORDER BY created_at DESC
            """)
            product_requests = await cursor.fetchall()
            all_new_requests.extend(product_requests)

            # 2. Заявки на услуги
            cursor = await db.execute("""
                SELECT id, user_id, title, price, 'service' as source 
                FROM service_orders 
                WHERE status IN ('active', 'new')
                ORDER BY created_at DESC
            """)
            service_requests = await cursor.fetchall()
            all_new_requests.extend(service_requests)

            if not all_new_requests:
                print("ℹ️ Нет новых активных заявок для добавления в корзины")
                return 0

            added_to_cart = 0
            users_processed = set()

            for req in all_new_requests:
                request_id, user_id, title, price, source = req
                item_type = "service" if source == "service" else "product/offer"

                # Проверяем, нет ли уже этой заявки в корзине пользователя
                cursor = await db.execute("""
                    SELECT id FROM cart_order 
                    WHERE user_id = ? AND item_type = 'order_request' AND item_id = ?
                """, (user_id, request_id))
                existing_in_cart = await cursor.fetchone()

                if not existing_in_cart:
                    # Определяем источник для корректного удаления
                    source_table = "service_orders" if source == "service" else "order_requests"

                    # Добавляем в корзину
                    await db.execute("""
                        INSERT INTO cart_order (
                            user_id, item_type, item_id, quantity, selected_options, price, added_at, source_table
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        "order_request",
                        request_id,
                        1,  # Количество по умолчанию
                        "",  # Без опций
                        price or "0",
                        datetime.now().isoformat(),
                        source_table
                    ))
                    added_to_cart += 1
                    users_processed.add(user_id)
                    print(f"✅ Заявка {request_id} ({item_type}) добавлена в корзину пользователя {user_id}")

            if added_to_cart > 0:
                await db.commit()
                print(f"✅ В корзины добавлено {added_to_cart} заявок для {len(users_processed)} пользователей")
            else:
                print("ℹ️ Все активные заявки уже находятся в корзинах")

            return added_to_cart

    except Exception as e:
        print(f"❌ Ошибка автоматического добавления в корзину: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def sync_requests_from_sheets_to_db():
    """Загрузка заявок из Google Sheets в БД"""

    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)

        # Пробуем найти лист с заявками
        try:
            requests_sheet = spreadsheet.worksheet(SHEET_REQUESTS)
        except:
            print(f"ℹ️ Лист '{SHEET_REQUESTS}' не найден в Google Sheets")
            return False

        # Получаем данные из листа
        requests_data = requests_sheet.get_all_records()
        print(f"📊 Найдено {len(requests_data)} записей в Google Sheets")

        if not requests_data:
            print("ℹ️ В Google Sheets нет данных для импорта")
            return False

        async with aiosqlite.connect("bot_database.db") as db:
            added_count = 0
            updated_count = 0
            skipped_count = 0

            # Получаем существующие ID из базы данных
            cursor = await db.execute("SELECT id FROM order_requests")
            existing_order_ids = {row[0] for row in await cursor.fetchall()}

            cursor = await db.execute("SELECT id FROM service_orders")
            existing_service_ids = {row[0] for row in await cursor.fetchall()}

            # Объединяем все ID для проверки уникальности
            all_existing_ids = existing_order_ids.union(existing_service_ids)
            print(
                f"📊 В базе данных найдено {len(all_existing_ids)} записей (товары: {len(existing_order_ids)}, услуги: {len(existing_service_ids)})")

            for row_idx, row in enumerate(requests_data, 1):

                try:
                    # Пропускаем строки без ID заявки
                    if not row.get('ID заказа'):

                        print(f"⚠️ Строка {row_idx}: пропущена, нет ID заявки")
                        skipped_count += 1
                        continue

                    # Парсим ID заявки
                    try:
                        # request_id = int(row['ID заявки'])  <- ОШИБКА ЗДЕСЬ, убираем
                        request_id_str = str(row['ID заказа']).strip()
                        if request_id_str.startswith('P'):
                            # Это товар/предложение из order_requests
                            request_id = int(request_id_str[1:])  # Убираем префикс 'P'
                            source_table = 'order_requests'
                        elif request_id_str.startswith('S'):
                            # Это услуга из service_orders
                            request_id = int(request_id_str[1:])  # Убираем префикс 'S'
                            source_table = 'service_orders'
                        else:
                            # Старый формат без префикса (для обратной совместимости)
                            request_id = int(request_id_str)
                            source_table = 'order_requests'  # По умолчанию

                    # Обработка ошибки
                    except (ValueError, TypeError):
                        print(f"⚠️ Строка {row_idx}: неверный формат ID заявки: {row.get('ID заявки')}")
                        skipped_count += 1
                        continue

                    item_type_raw = str(row.get('Тип заявки', '')).lower()
                    if 'корзин' in item_type_raw or 'cart_order' in item_type_raw:
                        # Пропускаем заказы из корзины (они только для отчетности)
                        continue

                    # Проверяем обязательные поля
                    if not row.get('ID пользователя'):
                        print(f"⚠️ Строка {row_idx}: пропущена, нет ID пользователя")
                        skipped_count += 1
                        continue

                    # Парсим ID пользователя
                    try:
                        user_id = int(row['ID пользователя'])
                    except (ValueError, TypeError):
                        print(f"⚠️ Строка {row_idx}: неверный формат ID пользователя: {row.get('ID пользователя')}")
                        skipped_count += 1
                        continue

                    # Проверяем существование пользователя
                    cursor = await db.execute(
                        "SELECT user_id FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    user_exists = await cursor.fetchone()

                    if not user_exists:
                        print(f"⚠️ Строка {row_idx}: пользователь {user_id} не найден, пропускаем заявку")
                        skipped_count += 1
                        continue

                    # Форматируем дату
                    created_at = row.get('Дата создания', '')
                    if not created_at:
                        created_at = datetime.now().isoformat()

                    # Определяем статус
                    status = row.get('Статус', 'new')
                    status_lower = str(status).lower()
                    if any(word in status_lower for word in ['активен', 'active', 'активная', 'новая', 'new']):
                        status = 'active'
                    elif any(word in status_lower for word in ['выполнено', 'completed', 'завершено', 'завершена']):
                        status = 'completed'
                    else:
                        status = 'active'  # По умолчанию active для загрузки в корзину

                    # Определяем операцию
                    operation = row.get('Операция', 'buy')
                    operation_lower = str(operation).lower()

                    # Определяем тип заявки
                    item_type = row.get('Тип заявки', 'product')
                    item_type_lower = str(item_type).lower()

                    # Для услуг
                    if any(word in item_type_lower for word in ['услуга', 'service', 'сервис']):
                        item_type = 'service'
                        # Определяем операцию для услуг
                        if any(word in operation_lower for word in ['заказать', 'order', 'купить']):
                            operation = 'buy'
                        elif any(word in operation_lower for word in ['предложить', 'offer', 'продать', 'sell']):
                            operation = 'sell'
                        else:
                            operation = 'sell'  # По умолчанию для услуг

                        # Проверяем, существует ли уже услуга с таким ID
                        if request_id in existing_service_ids:
                            # Обновляем существующую услугу
                            await db.execute("""
                                UPDATE service_orders SET
                                    user_id = ?,
                                    operation = ?,
                                    category = ?,
                                    item_class = ?,
                                    item_type = ?,
                                    item_kind = ?,
                                    title = ?,
                                    works = ?, -- Назначение
                                    materials = ?, -- Имя
                                    service_date = ?, -- Дата создания товара
                                    conditions = ?, -- Состояние
                                    pricing = ?, -- Спецификации
                                    guarantees = ?, -- Преимущества
                                    additional_info = ?, -- Доп. информация
                                    images = ?,
                                    price = ?,
                                    deadline = ?, -- Наличие
                                    reviews = ?,
                                    rating = ?,
                                    supplier_info = ?,
                                    statistics = ?,
                                    tags = ?,
                                    contact = ?,
                                    status = ?,
                                    created_at = ?
                                WHERE id = ?
                            """, (
                                user_id,
                                operation,
                                row.get('Категория', ''),
                                row.get('Класс', ''),
                                row.get('Тип', ''),
                                row.get('Вид', ''),
                                row.get('Название', 'Без названия'),
                                row.get('Назначение', ''),
                                row.get('Имя', ''),
                                row.get('Дата создания товара', ''),
                                row.get('Состояние', ''),
                                row.get('Спецификации', ''),
                                row.get('Преимущества', ''),
                                row.get('Доп. информация', ''),
                                row.get('Изображения', ''),
                                str(row.get('Цена', '0')) if row.get('Цена') else '0',
                                row.get('Наличие', ''),
                                row.get('Отзывы', ''),
                                row.get('Рейтинг', ''),
                                row.get('Информация о поставщике', ''),
                                row.get('Статистика', ''),
                                row.get('Теги', ''),
                                row.get('Контакты', f'ID: {user_id}'),
                                status,
                                created_at,
                                request_id
                                ))
                            updated_count += 1
                            print(f"🔄 Строка {row_idx}: обновлена услуга ID: {request_id}")
                        else:
                            # Создаем новую услугу
                            cursor = await db.execute("""
                                INSERT INTO service_orders (
                                    id, user_id, operation, category, item_class,
                                    item_type, item_kind, title, works, materials,
                                    service_date, conditions, pricing, guarantees,
                                    additional_info, images, price, deadline,
                                    reviews, rating, supplier_info, statistics,
                                    tags, contact, status, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                request_id,
                                user_id,
                                operation,
                                row.get('Категория', ''),
                                row.get('Класс', ''),
                                row.get('Тип', ''),
                                row.get('Вид', ''),
                                row.get('Название', 'Без названия'),
                                row.get('Назначение', ''),
                                row.get('Имя', ''),
                                row.get('Дата создания товара', ''),
                                row.get('Состояние', ''),
                                row.get('Спецификации', ''),
                                row.get('Преимущества', ''),
                                row.get('Доп. информация', ''),
                                row.get('Изображения', ''),
                                str(row.get('Цена', '0')) if row.get('Цена') else '0',
                                row.get('Наличие', ''),
                                row.get('Отзывы', ''),
                                row.get('Рейтинг', ''),
                                row.get('Информация о поставщике', ''),
                                row.get('Статистика', ''),
                                row.get('Теги', ''),
                                row.get('Контакты', f'ID: {user_id}'),
                                status,
                                created_at
                                ))

                            added_count += 1
                            print(f"✅ Строка {row_idx}: добавлена услуга ID: {request_id}")

                            # Автоматически добавляем в корзину если статус активный
                            if status == 'active':
                                await db.execute("""
                                    INSERT OR IGNORE INTO cart_order 
                                    (user_id, item_type, item_id, quantity, price, added_at, source_table)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    user_id,
                                    'order_request',
                                    request_id,
                                    1,  # Количество по умолчанию
                                    str(row.get('Цена', '0')) if row.get('Цена') else '0',
                                    datetime.now().isoformat(),
                                    'service_orders'
                                ))
                                print(f"🛒 Услуга {request_id} добавлена в корзину пользователя {user_id}")

                    # Для товаров и предложений
                    else:
                        if any(word in item_type_lower for word in ['предложение', 'offer', 'актив']):
                            item_type = 'offer'
                        else:
                            item_type = 'product'

                        # Определяем операцию для товаров/предложений
                        if any(word in operation_lower for word in ['продать', 'sell', 'продажа']):
                            operation = 'sell'
                        else:
                            operation = 'buy'

                        # Проверяем, существует ли уже заявка с таким ID
                        if request_id in existing_order_ids:
                            # Обновляем существующую заявку
                            await db.execute("""
                                UPDATE order_requests SET
                                    user_id = ?,
                                    operation = ?,
                                    item_type = ?,
                                    category = ?,
                                    item_class = ?,
                                    item_type_detail = ?,
                                    item_kind = ?,
                                    title = ?,
                                    purpose = ?,
                                    name = ?,
                                    creation_date = ?,
                                    condition = ?,
                                    specifications = ?,
                                    advantages = ?,
                                    additional_info = ?,
                                    images = ?,
                                    price = ?,
                                    availability = ?,
                                    detailed_specs = ?,
                                    reviews = ?,
                                    rating = ?,
                                    delivery_info = ?,
                                    supplier_info = ?,
                                    statistics = ?,
                                    deadline = ?,
                                    tags = ?,
                                    contact = ?,
                                    status = ?,
                                    created_at = ?
                                WHERE id = ?
                            """, (
                                user_id,
                                operation,
                                item_type,
                                row.get('Категория', ''),
                                row.get('Класс', ''),
                                row.get('Тип', ''),
                                row.get('Вид', ''),
                                row.get('Название', 'Без названия'),
                                row.get('Назначение', ''),
                                row.get('Имя', ''),
                                row.get('Дата создания товара', ''),
                                row.get('Состояние', ''),
                                row.get('Спецификации', ''),
                                row.get('Преимущества', ''),
                                row.get('Доп. информация', ''),
                                row.get('Изображения', ''),
                                str(row.get('Цена', '0')) if row.get('Цена') else '0',
                                row.get('Наличие', ''),
                                row.get('Подробные характеристики', ''),
                                row.get('Отзывы', ''),
                                row.get('Рейтинг', ''),
                                row.get('Информация о доставке', ''),
                                row.get('Информация о поставщике', ''),
                                row.get('Статистика', ''),
                                row.get('Сроки', ''),
                                row.get('Теги', ''),
                                row.get('Контакты', f'ID: {user_id}'),
                                status,
                                created_at,
                                request_id
                            ))
                            updated_count += 1
                            print(f"🔄 Строка {row_idx}: обновлена заявка ID: {request_id} (тип: {item_type})")
                        else:
                            # Создаем новую заявку
                            cursor = await db.execute("""
                                INSERT INTO order_requests (
                                    id, user_id, operation, item_type, category, item_class,
                                    item_type_detail, item_kind, title, purpose, name,
                                    creation_date, condition, specifications, advantages,
                                    additional_info, images, price, availability,
                                    detailed_specs, reviews, rating, delivery_info,
                                    supplier_info, statistics, deadline, tags, contact,
                                    status, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                request_id,
                                user_id,
                                operation,
                                item_type,
                                row.get('Категория', ''),
                                row.get('Класс', ''),
                                row.get('Тип', ''),
                                row.get('Вид', ''),
                                row.get('Название', 'Без названия'),
                                row.get('Назначение', ''),
                                row.get('Имя', ''),
                                row.get('Дата создания товара', ''),
                                row.get('Состояние', ''),
                                row.get('Спецификации', ''),
                                row.get('Преимущества', ''),
                                row.get('Доп. информация', ''),
                                row.get('Изображения', ''),
                                str(row.get('Цена', '0')) if row.get('Цена') else '0',
                                row.get('Наличие', ''),
                                row.get('Подробные характеристики', ''),
                                row.get('Отзывы', ''),
                                row.get('Рейтинг', ''),
                                row.get('Информация о доставке', ''),
                                row.get('Информация о поставщике', ''),
                                row.get('Статистика', ''),
                                row.get('Сроки', ''),
                                row.get('Теги', ''),
                                row.get('Контакты', f'ID: {user_id}'),
                                status,
                                created_at
                            ))

                            added_count += 1
                            print(f"✅ Строка {row_idx}: добавлена заявка ID: {request_id} (тип: {item_type})")

                            # Автоматически добавляем в корзину если статус активный
                            if status == 'active':
                                await db.execute("""
                                    INSERT OR IGNORE INTO cart_order 
                                    (user_id, item_type, item_id, quantity, price, added_at, source_table)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    user_id,
                                    'order_request',
                                    request_id,
                                    1,  # Количество по умолчанию
                                    str(row.get('Цена', '0')) if row.get('Цена') else '0',
                                    datetime.now().isoformat(),
                                    'order_requests'
                                ))
                                print(f"🛒 Заявка {request_id} добавлена в корзину пользователя {user_id}")

                except Exception as e:
                    print(f"❌ Строка {row_idx}: ошибка обработки: {e}")
                    import traceback
                    traceback.print_exc()
                    skipped_count += 1
                    continue

            await db.commit()

            print(f"\n📊 Импорт завершен:")
            print(f"   ✅ Добавлено: {added_count}")
            print(f"   🔄 Обновлено: {updated_count}")
            print(f"   ⏭️ Пропущено: {skipped_count}")
            print(f"   📈 Всего обработано: {added_count + updated_count}")

            return added_count > 0 or updated_count > 0

    except Exception as e:
        print(f"❌ Критическая ошибка импорта заявок: {e}")
        import traceback
        traceback.print_exc()
        return False

async def sync_all_sheets(bidirectional=False):
    try:
        if bidirectional:
            await sync_sheets_to_db()
        await sync_db_to_google_sheets()
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)

        async with aiosqlite.connect("bot_database.db") as db:
            partners_sheet = spreadsheet.worksheet(SHEET_PARTNERS)
            cursor = await db.execute(
                "SELECT specialization, partner_name, 'Активен', contact_info, status, '' FROM auto_tech_partners UNION ALL SELECT services, partner_name, 'Активен', contact_info, status, '' FROM auto_service_partners")
            partners = await cursor.fetchall()
            if partners:
                partners_sheet.clear()
                partners_sheet.update('A1', [list(partners_sheet.row_values(1))] + [list(p) for p in partners])

            investors_sheet = spreadsheet.worksheet(SHEET_INVESTORS)
            cursor = await db.execute("SELECT investor_name, contact_info, 'Активен', status, '' FROM investors")
            investors = await cursor.fetchall()
            if investors:
                investors_sheet.clear()
                investors_sheet.update('A1', [list(investors_sheet.row_values(1))] + [list(i) for i in investors])



            products_sheet = spreadsheet.worksheet(SHEET_PRODUCTS)
            cursor = await db.execute("""
                SELECT 
                    o.order_date || ' - ' || o.status,
                    o.user_id,
                    (SELECT COUNT(*)+1 FROM users WHERE user_id < o.user_id),
                    c.name,
                    p.title,
                    COALESCE(p.specifications, '1'),
                    u.full_name || ' (' || COALESCE(u.phone, '') || ')',
                    COALESCE(p.partner_info, ''),
                    COALESCE(p.price, ''),
                    COALESCE(p.delivery_info, ''),
                    COALESCE(p.description, ''),
                    p.status,
                    COALESCE(p.images, '')
                FROM orders o
                JOIN auto_products p ON o.item_id = p.id
                JOIN auto_categories c ON p.category_id = c.id
                JOIN users u ON o.seller_id = u.user_id
                WHERE o.order_type = 'product'
            """)
            products = await cursor.fetchall()
            if products:
                products_sheet.clear()
                products_sheet.update('A1', [list(products_sheet.row_values(1))] + [list(p) for p in products])

            services_sheet = spreadsheet.worksheet(SHEET_SERVICES)
            cursor = await db.execute("""
                SELECT 
                    o.order_date || ' - ' || o.status,
                    o.user_id,
                    (SELECT COUNT(*)+1 FROM users WHERE user_id < o.user_id),
                    c.name,
                    s.title,
                    COALESCE(s.duration, ''),
                    u.full_name || ' (' || COALESCE(u.phone, '') || ')',
                    COALESCE(s.partner_info, ''),
                    COALESCE(s.price, ''),
                    o.order_date,
                    COALESCE(s.description, ''),
                    s.status,
                    COALESCE(s.images, '')
                FROM orders o
                JOIN auto_services s ON o.item_id = s.id
                JOIN auto_categories c ON s.category_id = c.id
                JOIN users u ON o.seller_id = u.user_id
                WHERE o.order_type = 'service'
            """)
            services = await cursor.fetchall()
            if services:
                services_sheet.clear()
                services_sheet.update('A1', [list(services_sheet.row_values(1))] + [list(s) for s in services])

        return True
    except Exception as e:
        logging.error(f"Ошибка синхронизации всех листов: {e}")
        return False


async def sync_orders_to_sheets():
    """Синхронизация заказов (таблица orders) с Google Sheet 'Заказы'"""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)
        
        try:
            sheet = spreadsheet.worksheet(SHEET_REAL_ORDERS)
            print(f"✅ Лист '{SHEET_REAL_ORDERS}' найден")
        except:
            sheet = spreadsheet.add_worksheet(title=SHEET_REAL_ORDERS, rows=1000, cols=15)
            headers = [
                "ID заказа", "Дата заказа", "Тип", "Статус", "ID покупателя", "Username покупателя", 
                "ID товара", "Название товара", "Цена", "ID продавца", "Username продавца", 
                "Количество", "Сумма", "Примечания", "Дата обновления"
            ]
            sheet.update('A1', [headers])
            print(f"✅ Лист '{SHEET_REAL_ORDERS}' создан с заголовками")

        # Получаем данные из orders
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT 
                    o.id,
                    o.order_date,
                    o.order_type,
                    o.status,
                    o.user_id,
                    ub.username,
                    o.item_id,
                    COALESCE(p.title, s.title, 'Неизвестно') as item_title,
                    COALESCE(p.price, s.price, '0') as item_price,
                    o.seller_id,
                    us.username as seller_username,
                    '1' as quantity, -- В orders пока поштучно или надо парсить notes
                    o.notes,
                    datetime('now')
                FROM orders o
                LEFT JOIN users ub ON o.user_id = ub.user_id
                LEFT JOIN users us ON o.seller_id = us.user_id
                LEFT JOIN order_requests p ON (o.item_id = p.id AND o.order_type IN ('product', 'offer', 'order_request'))
                LEFT JOIN service_orders s ON (o.item_id = s.id AND o.order_type = 'service')
                ORDER BY o.order_date DESC
            """)
            orders = await cursor.fetchall()
            
        print(f"[DEBUG] Найдено {len(orders)} заказов для выгрузки в '{SHEET_REAL_ORDERS}'")
        
        if orders:
            # Формируем данные
            data_rows = []
            for order in orders:
                (id, date, type_, status, buyer_id, buyer_name, item_id, title, price, 
                 seller_id, seller_name, qty, notes, updated) = order
                 
                # Пытаемся распарсить notes на предмет количества и цены
                # "Заказ из корзины. Кол-во: {quantity}. Цена: {price}. Опции: {options}"
                import re
                
                final_qty = qty
                final_sum = 0
                
                qty_match = re.search(r"Кол-во: (\d+)", str(notes))
                if qty_match:
                    final_qty = qty_match.group(1)
                    
                price_val = 0
                try:
                    price_val = float(str(price).replace(' ', ''))
                except:
                    pass
                    
                try:
                    qty_val = float(final_qty)
                    final_sum = price_val * qty_val
                except:
                    pass

                row = [
                    id, date, type_, status, buyer_id, buyer_name,
                    item_id, title, price, seller_id or "", seller_name or "",
                    final_qty, final_sum, notes, updated
                ]
                data_rows.append(row)
                
            # Записываем (оставляем заголовки)
            sheet.clear()
            headers = [
                "ID заказа", "Дата заказа", "Тип", "Статус", "ID покупателя", "Username покупателя", 
                "ID товара", "Название товара", "Цена", "ID продавца", "Username продавца", 
                "Количество", "Сумма", "Примечания", "Дата обновления"
            ]
            sheet.update('A1', [headers])
            sheet.update('A2', data_rows)
            print(f"✅ Таблица '{SHEET_REAL_ORDERS}' обновлена: {len(data_rows)} строк")
            
        else:
            sheet.clear()
            headers = [
                "ID заказа", "Дата заказа", "Тип", "Статус", "ID покупателя", "Username покупателя", 
                "ID товара", "Название товара", "Цена", "ID продавца", "Username продавца", 
                "Количество", "Сумма", "Примечания", "Дата обновления"
            ]
            sheet.update('A1', [headers])

        return True

    except Exception as e:
        print(f"❌ Ошибка синхронизации заказов: {e}")
        return False