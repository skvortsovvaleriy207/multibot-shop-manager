import gspread
import aiosqlite
from datetime import datetime
from config import CREDENTIALS_FILE, AUTO_PRODUCTS_SHEET_URL, AUTO_SERVICES_SHEET_URL, AUTO_ORDERS_SHEET_URL
import asyncio

def get_google_sheets_client():
    return gspread.service_account(filename=CREDENTIALS_FILE)

async def sync_products_to_sheet():
    """Синхронизация товаров автотехники с Google Sheets"""
    try:
        gc = get_google_sheets_client()
        
        # Создаем или открываем таблицу товаров
        if not AUTO_PRODUCTS_SHEET_URL:
            print("Ошибка: AUTO_PRODUCTS_SHEET_URL не указан в config.py")
            return False
            
        try:
            spreadsheet = gc.open_by_url(AUTO_PRODUCTS_SHEET_URL)
            try:
                sheet = spreadsheet.worksheet('Товары')
            except Exception:
                sheet = spreadsheet.add_worksheet(title='Товары', rows=1000, cols=20)
        except Exception as e:
            print(f"Ошибка открытия таблицы товаров: {e}")
            return False
        
        # Заголовки для таблицы товаров
        headers = [
            "ID товара", "Дата добавления", "Telegram ID продавца", "Username продавца",
            "Категория", "Название товара", "Описание", "Цена", "Характеристики",
            "Статус", "Количество фото", "Контакты продавца"
        ]
        
        # Получаем данные из БД
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT ap.id, ap.created_at, ap.user_id, u.username, c.name, 
                       ap.title, ap.description, ap.price, ap.specifications, 
                       ap.status, ap.images, u.phone
                FROM auto_products ap
                LEFT JOIN users u ON ap.user_id = u.user_id
                LEFT JOIN categories c ON ap.category_id = c.id
                ORDER BY ap.created_at DESC
            """)
            products = await cursor.fetchall()
            print(f"DEBUG: Найдено {len(products)} товаров в базе")
        
        # Подготавливаем данные для записи
        data = [headers]
        for product in products:
            import json
            images_count = 0
            try:
                images = json.loads(product[10] or "[]")
                images_count = len(images)
            except Exception:
                pass
            
            row = [
                product[0],  # ID
                product[1][:10] if product[1] else "",  # Дата
                product[2],  # User ID
                product[3] or "",  # Username
                product[4] or "",  # Категория
                product[5] or "",  # Название
                product[6] or "",  # Описание
                product[7] or "",  # Цена
                product[8] or "",  # Характеристики
                product[9] or "",  # Статус
                images_count,  # Количество фото
                product[11] or ""  # Телефон
            ]
            data.append(row)
        
        # Очищаем и записываем данные
        try:
            sheet.clear()
            if data:
                sheet.update('A1', data)
                print(f"DEBUG: Записано {len(data)-1} строк в Google Sheets")
        except Exception as e:
            print(f"Ошибка записи в таблицу: {e}")
            return False
        
        print(f"Синхронизировано {len(products)} товаров в Google Sheets")
        return True
        
    except Exception as e:
        print(f"Ошибка синхронизации товаров: {e}")
        return False

async def sync_services_to_sheet():
    """Синхронизация автоуслуг с Google Sheets"""
    try:
        gc = get_google_sheets_client()
        
        if not AUTO_SERVICES_SHEET_URL:
            print("Ошибка: AUTO_SERVICES_SHEET_URL не указан в config.py")
            return False
            
        try:
            spreadsheet = gc.open_by_url(AUTO_SERVICES_SHEET_URL)
            try:
                sheet = spreadsheet.worksheet('Услуги')
            except Exception:
                sheet = spreadsheet.add_worksheet(title='Услуги', rows=1000, cols=20)
        except Exception as e:
            print(f"Ошибка открытия таблицы услуг: {e}")
            return False
        
        headers = [
            "ID услуги", "Дата добавления", "Telegram ID поставщика", "Username поставщика",
            "Категория", "Название услуги", "Описание", "Цена", "Местоположение",
            "Контактная информация", "Статус", "Количество фото"
        ]
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT as_.id, as_.created_at, as_.user_id, u.username, c.name,
                       as_.title, as_.description, as_.price, as_.location,
                       as_.contact_info, as_.status, as_.images
                FROM auto_services as_
                LEFT JOIN users u ON as_.user_id = u.user_id
                LEFT JOIN categories c ON as_.category_id = c.id
                ORDER BY as_.created_at DESC
            """)
            services = await cursor.fetchall()
            print(f"DEBUG: Найдено {len(services)} услуг в базе")
        
        data = [headers]
        for service in services:
            import json
            images_count = 0
            try:
                images = json.loads(service[11] or "[]")
                images_count = len(images)
            except Exception:
                pass
            
            row = [
                service[0],  # ID
                service[1][:10] if service[1] else "",  # Дата
                service[2],  # User ID
                service[3] or "",  # Username
                service[4] or "",  # Категория
                service[5] or "",  # Название
                service[6] or "",  # Описание
                service[7] or "",  # Цена
                service[8] or "",  # Местоположение
                service[9] or "",  # Контакты
                service[10] or "",  # Статус
                images_count  # Количество фото
            ]
            data.append(row)
        
        sheet.clear()
        if data:
            sheet.update('A1', data)
        
        print(f"Синхронизировано {len(services)} услуг в Google Sheets")
        return True
        
    except Exception as e:
        print(f"Ошибка синхронизации услуг: {e}")
        return False

async def sync_orders_to_sheet():
    """Синхронизация заказов с Google Sheets"""
    try:
        gc = get_google_sheets_client()
        
        if not AUTO_ORDERS_SHEET_URL:
            print("Ошибка: AUTO_ORDERS_SHEET_URL не указан в config.py")
            return False
            
        try:
            spreadsheet = gc.open_by_url(AUTO_ORDERS_SHEET_URL)
            try:
                sheet = spreadsheet.worksheet('Заказы')
            except Exception:
                sheet = spreadsheet.add_worksheet(title='Заказы', rows=1000, cols=20)
        except Exception as e:
            print(f"Ошибка открытия таблицы заказов: {e}")
            return False
        
        headers = [
            "ID заказа", "Дата заказа", "Тип заказа", "ID товара/услуги", "Название",
            "Telegram ID покупателя", "Username покупателя", "Telegram ID продавца", 
            "Username продавца", "Статус заказа", "Цена", "Примечания"
        ]
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT o.id, o.order_date, o.order_type, o.item_id, 
                       CASE 
                           WHEN o.order_type = 'tech' THEN ap.title
                           ELSE as_.title
                       END as title,
                       o.user_id, u1.username as buyer_username,
                       o.seller_id, u2.username as seller_username,
                       o.status,
                       CASE 
                           WHEN o.order_type = 'tech' THEN ap.price
                           ELSE as_.price
                       END as price,
                       o.notes
                FROM orders o
                LEFT JOIN auto_products ap ON o.order_type = 'tech' AND o.item_id = ap.id
                LEFT JOIN auto_services as_ ON o.order_type = 'service' AND o.item_id = as_.id
                LEFT JOIN users u1 ON o.user_id = u1.user_id
                LEFT JOIN users u2 ON o.seller_id = u2.user_id
                ORDER BY o.order_date DESC
            """)
            orders = await cursor.fetchall()
        
        data = [headers]
        for order in orders:
            row = [
                order[0],  # ID заказа
                order[1][:10] if order[1] else "",  # Дата
                "Автотехника" if order[2] == 'tech' else "Автоуслуги",  # Тип
                order[3],  # ID товара/услуги
                order[4] or "",  # Название
                order[5],  # ID покупателя
                order[6] or "",  # Username покупателя
                order[7],  # ID продавца
                order[8] or "",  # Username продавца
                order[9] or "",  # Статус
                order[10] or "",  # Цена
                order[11] or ""  # Примечания
            ]
            data.append(row)
        
        sheet.clear()
        if data:
            sheet.update('A1', data)
        
        print(f"Синхронизировано {len(orders)} заказов в Google Sheets")
        return True
        
    except Exception as e:
        print(f"Ошибка синхронизации заказов: {e}")
        return False

# Мгновенная выгрузка всех данных автомагазина (вызывается при старте)
async def export_all_automarket_data():
    """Мгновенная выгрузка всех данных автомагазина"""
    print("Начинаем выгрузку данных автомагазина...")
    
    # Serialized execution to avoid API Quota Limits
    # results = await asyncio.gather(...) - REPLACED
    r1 = await sync_products_to_sheet()
    r2 = await sync_services_to_sheet()
    r3 = await sync_orders_to_sheet()
    results = [r1, r2, r3]
    
    success_count = sum(1 for result in results if result is True)
    print(f"Выгрузка завершена: {success_count}/3 таблиц обновлено")
    
    return success_count == 3

async def sync_products_from_sheet():
    """Синхронизация товаров из Google Sheets в БД"""
    try:
        gc = get_google_sheets_client()
        if not AUTO_PRODUCTS_SHEET_URL:
            return False
            
        spreadsheet = gc.open_by_url(AUTO_PRODUCTS_SHEET_URL)
        try:
            sheet = spreadsheet.worksheet('Товары')
        except:
            return False
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                product_id = row.get('ID товара')
                if not product_id:
                    continue
                    
                await db.execute("""
                    UPDATE auto_products 
                    SET title = ?, description = ?, price = ?, status = ?
                    WHERE id = ?
                """, (
                    row.get('Название товара', ''),
                    row.get('Описание', ''),
                    row.get('Цена', ''),
                    row.get('Статус', 'active'),
                    product_id
                ))
            await db.commit()
        
        print(f"Синхронизировано товаров из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации товаров из Google Sheets: {e}")
        return False

async def sync_services_from_sheet():
    """Синхронизация услуг из Google Sheets в БД"""
    try:
        gc = get_google_sheets_client()
        if not AUTO_SERVICES_SHEET_URL:
            return False
            
        spreadsheet = gc.open_by_url(AUTO_SERVICES_SHEET_URL)
        try:
            sheet = spreadsheet.worksheet('Услуги')
        except:
            return False
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                service_id = row.get('ID услуги')
                if not service_id:
                    continue
                    
                await db.execute("""
                    UPDATE auto_services 
                    SET title = ?, description = ?, price = ?, status = ?
                    WHERE id = ?
                """, (
                    row.get('Название услуги', ''),
                    row.get('Описание', ''),
                    row.get('Цена', ''),
                    row.get('Статус', 'active'),
                    service_id
                ))
            await db.commit()
        
        print(f"Синхронизировано услуг из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации услуг из Google Sheets: {e}")
        return False

async def sync_orders_from_sheet():
    """Синхронизация статусов заказов из Google Sheets в БД"""
    try:
        gc = get_google_sheets_client()
        if not AUTO_ORDERS_SHEET_URL:
            return False
            
        spreadsheet = gc.open_by_url(AUTO_ORDERS_SHEET_URL)
        try:
            sheet = spreadsheet.worksheet('Заказы')
        except:
            return False
        data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            for row in data:
                order_id = row.get('ID заказа')
                new_status = str(row.get('Статус заказа', '')).strip()
                if not order_id or not new_status:
                    continue
                    
                # Получаем текущий статус
                cursor = await db.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
                current = await cursor.fetchone()
                
                current_status = str(current[0]).strip() if current and current[0] else ""
                
                if current and current_status != new_status:
                    await db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
                    
                    # Уведомляем пользователей об изменении
                    cursor = await db.execute("SELECT user_id, seller_id FROM orders WHERE id = ?", (order_id,))
                    order_data = await cursor.fetchone()
                    if order_data:
                        await notify_order_status_change(order_data[0], order_data[1], order_id, new_status)
            
            await db.commit()
        
        print(f"Синхронизированы статусы заказов из Google Sheets")
        return True
    except Exception as e:
        print(f"Ошибка синхронизации заказов из Google Sheets: {e}")
        return False

async def notify_order_status_change(user_id: int, seller_id: int, order_id: int, new_status: str):
    """Уведомление об изменении статуса заказа"""
    try:
        from dispatcher import bot
        message = f"📋 Статус заказа #{order_id} изменен на: {new_status}"
        await bot.send_message(user_id, message)
        if seller_id != user_id:
            await bot.send_message(seller_id, message)
    except Exception as e:
        print(f"Ошибка уведомления: {e}")

async def sync_all_from_sheets():
    """Синхронизация всех данных из Google Sheets в БД"""
    # Serialized execution
    r1 = await sync_products_from_sheet()
    r2 = await sync_services_from_sheet()
    r3 = await sync_orders_from_sheet()
    results = [r1, r2, r3]
    success_count = sum(1 for result in results if result is True)
    print(f"Синхронизация из Google Sheets: {success_count}/3 таблиц обновлено")
    return success_count >= 2

# Функция для периодической синхронизации (вызывается из main.py)
async def scheduled_automarket_sync():
    """Периодическая загрузка товаров/услуг из Google Sheets в 17:00 МСК"""
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
            
            # Загрузка товаров и услуг в 17:00
            await sync_products_from_sheet()
            await sync_services_from_sheet()
            
        except Exception as e:
            print(f"Ошибка в scheduled_automarket_sync: {e}")
            await asyncio.sleep(3600)

# Мгновенная выгрузка при создании/изменении товаров/услуг
async def instant_export_product(product_id: int):
    """Мгновенная выгрузка товара в Google Sheets"""
    try:
        await sync_products_to_sheet()
        print(f"✅ Товар {product_id} мгновенно выгружен в Google Sheets")
    except Exception as e:
        print(f"❌ Ошибка мгновенной выгрузки товара: {e}")

async def instant_export_service(service_id: int):
    """Мгновенная выгрузка услуги в Google Sheets"""
    try:
        await sync_services_to_sheet()
        print(f"✅ Услуга {service_id} мгновенно выгружена в Google Sheets")
    except Exception as e:
        print(f"❌ Ошибка мгновенной выгрузки услуги: {e}")

    except Exception as e:
        print(f"❌ Ошибка мгновенной выгрузки заказа: {e}")

async def export_request_to_sheet(request_id: int, item_type: str, catalog_id: int):
    """Экспорт одобренной заявки в Google Sheets (Заявки)"""
    try:
        from config import SHEET_ORDERS
        gc = get_google_sheets_client()
        
        # URL должен быть определен в config/google_sheets, но здесь используем общий URL
        # Предполагаем, что SHEET_ORDERS - это имя листа в главной таблице опросов?
        # Или отдельная таблица?
        # По ТЗ "доп. гугл таблицу Заявки". Пусть это будет вкладка "Заявки" в таблице автомагазина
        
        if not AUTO_ORDERS_SHEET_URL:
            # Fallback to survey sheet URL if orders sheet url is not set (unlikely)
            print("Ошибка: AUTO_ORDERS_SHEET_URL не установлен.")
            return False

        try:
            spreadsheet = gc.open_by_url(AUTO_ORDERS_SHEET_URL)
            try:
                sheet = spreadsheet.worksheet('Заявки')
            except Exception:
                sheet = spreadsheet.add_worksheet(title='Заявки', rows=1000, cols=20)
        except Exception as e:
            print(f"Ошибка открытия таблицы Заявок: {e}")
            return False

        headers = [
            "ID заявки", "Дата одобрения", "Тип", "Название", "Описание",
            "Цена", "Категория", "Класс", "Тип (Деталь)", "Вид",
            "Telegram ID поставщика", "ID в каталоге", "Статус"
        ]
        
        # Получаем данные заявки
        table_name = "service_orders" if item_type == "service" else "order_requests"
        
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(f"SELECT * FROM {table_name} WHERE id = ?", (request_id,))
            row = await cursor.fetchone()
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))
            
        if not data:
            return False

        # Подготавливаем строку
        row_values = [
            data.get('id'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            item_type,
            data.get('title'),
            data.get('additional_info') or data.get('description', ''),
            data.get('price'),
            data.get('category'),
            data.get('item_class'),
            data.get('item_type_detail'),
            data.get('item_kind'),
            data.get('user_id'), # ID поставщика (автора заявки)
            catalog_id,
            "Одобрено"
        ]
        
        # Если таблица пустая, добавляем заголовки
        if not sheet.get_all_values():
            sheet.append_row(headers)
            
        sheet.append_row(row_values)
        print(f"✅ Заявка #{request_id} экспортирована в таблицу 'Заявки'")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка экспорта заявки в таблицу: {e}")
        return False