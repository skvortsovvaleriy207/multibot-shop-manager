import aiosqlite
import os
from datetime import datetime

DB_FILE = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.commit()
            
            print("DB: Creating users table...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    has_completed_survey INTEGER DEFAULT 0,
                    created_at TEXT,
                    survey_date TEXT,
                    full_name TEXT,
                    birth_date TEXT,
                    location TEXT,
                    email TEXT,
                    phone TEXT,
                    employment TEXT,
                    financial_problem TEXT,
                    social_problem TEXT,
                    ecological_problem TEXT,
                    passive_subscriber TEXT,
                    active_partner TEXT,
                    investor_trader TEXT,
                    business_proposal TEXT,
                    bonus_total REAL,
                    bonus_adjustment REAL DEFAULT 0,
                    current_balance REAL,
                    problem_cost TEXT,
                    notes TEXT,
                    partnership_date TEXT,
                    referral_count INTEGER,
                    referral_payment TEXT,
                    subscription_date TEXT,
                    subscription_payment_date TEXT,
                    purchases TEXT,
                    sales TEXT,
                    requisites TEXT,
                    shop_id TEXT,
                    business TEXT,
                    products_services TEXT,
                    account_status TEXT,
                    requests_text TEXT,
                    user_status TEXT
                )
            """)

            # Проверка и добавление колонки requests_text если её нет (миграция)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN requests_text TEXT")
                print("Added column requests_text to users table")
            except Exception:
                pass # Колонка уже существует

            await db.commit() # Commit after users table creation


            # Проверка и добавление колонки user_status если её нет (миграция)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN user_status TEXT")
                print("Added column user_status to users table")
            except Exception:
                pass # Колонка уже существует

            cursor = await db.execute("SELECT COUNT(*) FROM users")
            count = (await cursor.fetchone())[0]

            if count == 0:

                await db.execute("""
                    INSERT INTO users (
                        survey_date, user_id, username, full_name, birth_date, location, email, phone, employment,
                        financial_problem, social_problem, ecological_problem, passive_subscriber, active_partner,
                        investor_trader, business_proposal, bonus_total, bonus_adjustment, current_balance, problem_cost,
                        notes, partnership_date, referral_count, referral_payment, subscription_date,
                        subscription_payment_date, purchases, sales, requisites, shop_id, business,
                        products_services, account_status, first_name, last_name, has_completed_survey, created_at, requests_text, user_status
                    ) VALUES (
                        'Дата опроса', 0, 'Telegram ID', 'ФИО', 'Дата рождения', 'Место жительства', 'Email', 'Телефон', 'Занятость',
                        'Финансовая проблема', 'Социальная проблема', 'Экологическая проблема', 'Пассивный подписчик', 'Активный партнер',
                        'Инвестор/трейдер', 'Бизнес-предложение', 0, 0, 0, 'Стоимость проблем',
                        'Примечания', 'Дата партнерства', 0, 'Оплата за рефералов', 'Дата подписки',
                        'Дата оплаты подписки', 'Покупки', 'Продажи', 'Реквизиты', 'ID в магазине', 'Бизнес',
                        'Товары/услуги', 'Статус аккаунта', '', '', 0, datetime('now'), '0 / 0', 'Статус подписчика'
                    )
                """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS survey_answers (
                    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question_id INTEGER,
                    answer_text TEXT,
                    answered_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)


            await db.execute("""
                CREATE TABLE IF NOT EXISTS showcase_messages (
                    message_id INTEGER,
                    chat_id INTEGER,
                    PRIMARY KEY (message_id, chat_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_bonuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    bonus_total REAL,
                    bonus_adjustment REAL DEFAULT 0,
                    current_balance REAL,
                    adjustment_reason TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Таблицы для магазина
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auto_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL, -- 'tech' или 'service'
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES auto_categories (id)
                )
            """)
            
            # Таблица категорий для управления
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS auto_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL,
                    images TEXT, -- JSON массив ID изображений
                    specifications TEXT, -- JSON характеристики
                    status TEXT DEFAULT 'active', -- active, sold, inactive
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (category_id) REFERENCES auto_categories (id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS auto_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL,
                    location TEXT,
                    contact_info TEXT,
                    images TEXT, -- JSON массив ID изображений
                    status TEXT DEFAULT 'active',
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (category_id) REFERENCES auto_categories (id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_type TEXT NOT NULL, -- 'product' или 'service'
                    item_id INTEGER NOT NULL, -- ID товара или услуги
                    seller_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'new', -- new, processing, confirmed, completed, cancelled
                    order_date TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (seller_id) REFERENCES users (user_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_type TEXT NOT NULL, -- 'product' или 'service'
                    item_id INTEGER NOT NULL,
                    added_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Проверяем, есть ли уже категории
            cursor = await db.execute("SELECT COUNT(*) FROM auto_categories")
            cat_count = (await cursor.fetchone())[0]
            
            if cat_count == 0:
                # Универсальные категории
                categories = [
                    ('Товары', 'tech', None),
                    ('Услуги', 'service', None)
                ]
                
                for name, cat_type, parent_id in categories:
                    await db.execute(
                        "INSERT INTO auto_categories (name, type, parent_id) VALUES (?, ?, ?)",
                        (name, cat_type, parent_id)
                    )
            
            # Инициализация категорий для управления
            cursor = await db.execute("SELECT COUNT(*) FROM categories")
            categories_count = (await cursor.fetchone())[0]
            
            if categories_count == 0:
                # Главные категории
                await db.execute("INSERT INTO categories (id, name, parent_id) VALUES (1, 'Товары', NULL)")
                await db.execute("INSERT INTO categories (id, name, parent_id) VALUES (2, 'Услуги', NULL)")
            
            # Таблицы категорий для ТОВАРОВ
            await db.execute("CREATE TABLE IF NOT EXISTS product_purposes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS product_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS product_classes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS product_views (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS product_other_chars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            
            # Таблицы категорий для УСЛУГ
            await db.execute("CREATE TABLE IF NOT EXISTS service_purposes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS service_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS service_classes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS service_views (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS service_views (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS service_other_chars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")

            # Таблицы для предложений (Offers)
            await db.execute("CREATE TABLE IF NOT EXISTS offer_purposes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS offer_classes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS offer_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS offer_views (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            await db.execute("CREATE TABLE IF NOT EXISTS offer_other_chars (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
            
            # Инициализация категорий товаров
            # Инициализация категорий товаров
            # Убрана предустановка жилищных категорий по запросу пользователя

            # Инициализация категорий услуг
            # Убрана предустановка жилищных категорий по запросу пользователя


            # Добавляем новые столбцы для автомагазина
            new_columns = [
                "updated_at TEXT",
                "order_status TEXT",
                "partner_auto_tech TEXT", 
                "partner_auto_services TEXT",
                "auto_purchases TEXT",
                "auto_sales TEXT",
                "operation_type TEXT DEFAULT 'sale_tech'",
                "order_date TEXT"
            ]
            
            for column in new_columns:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {column}")
                except Exception:
                    pass
            
            # Таблица для отзывов и рейтингов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT NOT NULL, -- 'product' или 'service'
                    item_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 10),
                    review_text TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица сообщений согласно ТЗ п.1.10
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    recipient_id INTEGER NOT NULL,
                    subject TEXT,
                    message_text TEXT NOT NULL,
                    sent_at TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (sender_id) REFERENCES users (user_id),
                    FOREIGN KEY (recipient_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица партнеров по автотехнике согласно ТЗ п.3
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auto_tech_partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_name TEXT NOT NULL,
                    contact_info TEXT,
                    specialization TEXT,
                    status TEXT DEFAULT 'ПАРТНЕР',
                    created_at TEXT
                )
            """)
            
            # Таблица партнеров по автоуслугам согласно ТЗ п.4
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auto_service_partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_name TEXT NOT NULL,
                    contact_info TEXT,
                    services TEXT,
                    status TEXT DEFAULT 'ПАРТНЕР',
                    created_at TEXT
                )
            """)
            
            # Таблица инвесторов согласно ТЗ п.5
            await db.execute("""
                CREATE TABLE IF NOT EXISTS investors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investor_name TEXT NOT NULL,
                    contact_info TEXT,
                    investment_amount REAL,
                    status TEXT DEFAULT 'ИНВЕСТОР',
                    created_at TEXT
                )
            """)
            
            # Добавляем поля для рейтинга в товары и услуги
            rating_columns = [
                "rating REAL DEFAULT 0",
                "reviews_count INTEGER DEFAULT 0",
                "availability_status TEXT DEFAULT 'В наличии'",
                "delivery_info TEXT",
                "warranty_info TEXT",
                "operation_type TEXT DEFAULT 'sale_tech'",
                "order_date TEXT",
                "duration TEXT",
                "contact_info TEXT",
                "purpose_id INTEGER",
                "type_id INTEGER",
                "class_id INTEGER",
                "view_id INTEGER"
            ]
            
            for column in rating_columns:
                try:
                    await db.execute(f"ALTER TABLE auto_products ADD COLUMN {column}")
                except Exception:
                    pass
                try:
                    await db.execute(f"ALTER TABLE auto_services ADD COLUMN {column}")
                except Exception:
                    pass
            
            # Добавляем поля для партнерской информации согласно ТЗ п.3-5
            partner_columns = [
                "partner_info TEXT",
                "partner_conditions TEXT", 
                "partner_status TEXT"
            ]
            
            for column in partner_columns:
                try:
                    await db.execute(f"ALTER TABLE auto_products ADD COLUMN {column}")
                except Exception:
                    pass
                try:
                    await db.execute(f"ALTER TABLE auto_services ADD COLUMN {column}")
                except Exception:
                    pass
            
            # Добавляем поля для инвестиционных программ в профили пользователей
            investor_columns = [
                "investment_program TEXT",
                "investor_conditions TEXT",
                "notified_at TEXT",
                "proposal_status TEXT DEFAULT 'Новое предложение'",
                "last_proposal_notification TEXT",
                "referrer_id INTEGER"
            ]
            
            for column in investor_columns:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {column}")
                except Exception:
                    pass

            # Добавляем столбцы для покупок и продаж согласно ТЗ п.1.8
            purchase_sale_columns = [
                "purchases_count INTEGER DEFAULT 0",
                "sales_count INTEGER DEFAULT 0",
                "total_purchases REAL DEFAULT 0",
                "total_sales REAL DEFAULT 0"
            ]
            
            for column in purchase_sale_columns:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {column}")
                except Exception:
                    pass


            # Проверяем и обновляем таблицу order_requests
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    category TEXT,
                    item_class TEXT,
                    item_type_detail TEXT,
                    item_kind TEXT,
                    title TEXT NOT NULL,
                    purpose TEXT,
                    name TEXT,
                    creation_date TEXT,
                    condition TEXT,
                    specifications TEXT,
                    advantages TEXT,
                    additional_info TEXT,
                    images TEXT,
                    price TEXT,
                    availability TEXT,
                    detailed_specs TEXT,
                    reviews TEXT,
                    rating TEXT,
                    delivery_info TEXT,
                    supplier_info TEXT,
                    statistics TEXT,
                    deadline TEXT,
                    tags TEXT,
                    contact TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Таблица заявок на услуги (восстановлена для синхронизации)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS service_orders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    operation TEXT,
                    category TEXT,
                    item_class TEXT,
                    item_type TEXT,
                    item_kind TEXT,
                    title TEXT,
                    works TEXT,
                    materials TEXT,
                    service_date TEXT,
                    conditions TEXT,
                    pricing TEXT,
                    guarantees TEXT,
                    additional_info TEXT,
                    images TEXT,
                    price TEXT,
                    deadline TEXT,
                    reviews TEXT,
                    rating TEXT,
                    supplier_info TEXT,
                    statistics TEXT,
                    tags TEXT,
                    contact TEXT,
                    status TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Таблица категорий
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    catalog_type TEXT NOT NULL, -- 'product', 'service', 'offer'
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    created_at TEXT,
                    FOREIGN KEY(parent_id) REFERENCES categories(id)
                )
            """)
            
            # Миграция: добавляем столбец catalog_type в categories, если его нет
            try:
                await db.execute("ALTER TABLE categories ADD COLUMN catalog_type TEXT DEFAULT 'product'")
            except Exception:
                pass
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart_order (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_type TEXT NOT NULL, -- 'order_request'
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    selected_options TEXT,
                    price TEXT,
                    added_at TEXT,
                    source_table TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Миграция: добавляем столбец source_table в cart_order, если его нет
            try:
                await db.execute("ALTER TABLE cart_order ADD COLUMN source_table TEXT")
            except Exception:
                pass

            # Обновленная таблица order_requests с новыми полями (Миграция)
            new_request_columns = [
                "deadline TEXT", "tags TEXT", "catalog_id TEXT", "service_date TEXT",
                "works TEXT", "materials TEXT", "main_photo TEXT", "additional_photos TEXT",
                "pricing TEXT", "guarantees TEXT", "conditions TEXT"
            ]
            
            for col in new_request_columns:
                try:
                    await db.execute(f"ALTER TABLE order_requests ADD COLUMN {col}")
                except Exception:
                    pass

            # Таблица для разделов магазина
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_type TEXT NOT NULL, -- 'promotion', 'new', 'popular'
                    title TEXT NOT NULL,
                    content TEXT,
                    image_url TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT
                )
            """)

            # Миграция: добавляем sub_category в shop_sections
            try:
                await db.execute("ALTER TABLE shop_sections ADD COLUMN sub_category TEXT")
            except Exception:
                pass



            # Таблица постов для контента
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    title TEXT,
                    content_text TEXT,
                    media_file_id TEXT,
                    media_type TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY(category_id) REFERENCES categories(id)
                )
            """)
            
            # Миграция: created_at для categories
            try:
                await db.execute("ALTER TABLE categories ADD COLUMN created_at TEXT")
            except Exception:
                pass
            
            # Предзаполнение категорий контента
            content_sections = {
                'news': ['Тематические новости', 'Факты/Ситуации', 'Объявления', 'Новости партнеров', 'Новости инвесторов', 'Анонсы товаров/услуг', 'Успехи', 'Отчеты', 'Отзывы', 'Оценки'],
                'promotions': ['Покупки/Продажи', 'Мероприятия', 'Прогнозы/Советы', 'Аналитика', 'Образовательные материалы'],
                'popular': ['Хиты контента', 'Тренды заявок', 'Плейлисты', 'Познавательное', 'Развлекательное', 'Юмор-шоу', 'Реакции', 'Обзоры', 'Уроки', 'Истории успехов'],
                'new_items': []
            }
            
            # Pre-populate Categories for News, Promo, Popular if empty
            cursor = await db.execute("SELECT COUNT(*) FROM categories WHERE catalog_type IN ('news', 'promotions', 'popular', 'new_items')")
            count = (await cursor.fetchone())[0]
            if count == 0: # Only pre-populate if categories are empty
                root_name_map = {'news': 'Новости', 'promotions': 'Акции', 'popular': 'Популярное', 'new_items': 'Новинки'}
                for root_key, subcats in content_sections.items():
                    await db.execute("INSERT INTO categories (catalog_type, name, parent_id, created_at) VALUES (?, ?, NULL, datetime('now'))",
                                     (root_key, root_name_map.get(root_key, root_key)))
                    cursor = await db.execute("SELECT last_insert_rowid()")
                    root_id = (await cursor.fetchone())[0]
                
                    for sub in subcats:
                        await db.execute("INSERT INTO categories (catalog_type, name, parent_id, created_at) VALUES (?, ?, ?, datetime('now'))",
                                         (root_key, sub, root_id))

            await db.commit()

async def check_channel_subscription(bot, user_id: int, channel_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def check_account_status(user_id: int) -> bool:
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT account_status FROM users WHERE user_id = ?", (user_id,))
        status = await cursor.fetchone()
        return status and status[0] == "Р" 
