from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user


class SearchStates(StatesGroup):
    """Состояния для системы поиска"""
    waiting_search_in_products = State()
    waiting_search_in_services = State()
    waiting_search_in_offers = State()


# ========== ПОИСК В КАТАЛОГЕ ТОВАРОВ ==========

@dp.callback_query(F.data == "search_in_products")
async def search_in_products_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска в каталоге товаров"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск по названию/тегам", callback_data="search_products_by_name"))
    builder.add(types.InlineKeyboardButton(text="🏷 Поиск по категории", callback_data="search_products_by_category"))
    builder.add(types.InlineKeyboardButton(text="📊 Поиск по классу", callback_data="search_products_by_class"))
    builder.add(types.InlineKeyboardButton(text="📋 Поиск по типу", callback_data="search_products_by_type"))
    builder.add(types.InlineKeyboardButton(text="👁 Поиск по виду", callback_data="search_products_by_kind"))
    builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID", callback_data="search_products_by_id"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="product_catalog"))
    builder.adjust(2)

    await callback.message.edit_text(
        "🔍 **Поиск в товарах**\n\n"
        "Выберите вариант для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ========== ПОИСК В КАТАЛОГЕ УСЛУГ ==========

@dp.callback_query(F.data == "search_in_services")
async def search_in_services_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска в каталоге услуг"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск по названию/тегам", callback_data="search_services_by_name"))
    builder.add(types.InlineKeyboardButton(text="🏷 Поиск по категории", callback_data="search_services_by_category"))
    builder.add(types.InlineKeyboardButton(text="📊 Поиск по классу", callback_data="search_services_by_class"))
    builder.add(types.InlineKeyboardButton(text="📋 Поиск по типу", callback_data="search_services_by_type"))
    builder.add(types.InlineKeyboardButton(text="👁 Поиск по виду", callback_data="search_services_by_kind"))
    builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID", callback_data="search_services_by_id"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="service_catalog"))
    builder.adjust(2)

    await callback.message.edit_text(
        "🔍 **Поиск в услугах**\n\n"
        "Выберите вариант для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ========== ПОИСК В КАТАЛОГЕ ПРЕДЛОЖЕНИЙ ==========

@dp.callback_query(F.data == "search_in_offers")
async def search_in_offers_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска в каталоге предложений"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск по названию/тегам", callback_data="search_offers_by_name"))
    builder.add(types.InlineKeyboardButton(text="🏷 Поиск по категории", callback_data="search_offers_by_category"))
    builder.add(types.InlineKeyboardButton(text="📊 Поиск по классу", callback_data="search_offers_by_class"))
    builder.add(types.InlineKeyboardButton(text="📋 Поиск по типу", callback_data="search_offers_by_type"))
    builder.add(types.InlineKeyboardButton(text="👁 Поиск по виду", callback_data="search_offers_by_kind"))
    builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID", callback_data="search_offers_by_id"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="property_catalog"))
    builder.adjust(2)

    await callback.message.edit_text(
        "🔍 **Поиск в предложениях**\n\n"
        "Выберите вариант для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ========== ОБЩИЕ ФУНКЦИИ ПОИСКА ==========

async def perform_search_in_catalog(search_query: str, item_type: str, user_id: int) -> list:
    """Выполнение поиска в конкретном каталоге"""
    if not search_query:
        return []

    search_terms = search_query.lower().split()
    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            if item_type == "product":
                # Поиск в auto_products
                cursor = await db.execute("""
                    SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                    FROM auto_products ap
                    LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                    WHERE ap.status = 'active'
                """)
                auto_items = await cursor.fetchall()

                # Поиск в order_requests
                cursor = await db.execute("""
                    SELECT id, title, price, category, operation, description
                    FROM order_requests 
                    WHERE item_type = 'product' AND status IN ('active', 'approved', 'processing')
                """)
                order_items = await cursor.fetchall()

                # Объединяем все товары
                all_items = list(auto_items) + list(order_items)

            elif item_type == "service":
                # Поиск в service_orders
                cursor = await db.execute("""
                    SELECT id, title, price, category, operation, description
                    FROM service_orders 
                    WHERE status IN ('active', 'approved', 'processing')
                """)
                service_items = await cursor.fetchall()
                all_items = list(service_items)

            else:  # offer
                # Для предложений только order_requests
                cursor = await db.execute("""
                    SELECT id, title, price, category, operation, description
                    FROM order_requests 
                    WHERE item_type = 'offer' AND status IN ('active', 'approved', 'processing')
                """)
                all_items = await cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
            return []

    # Фильтруем по поисковому запросу
    for item in all_items:
        item_id, title, price, category, operation, description = item

        # Собираем текст для поиска
        search_text = f"{title or ''} {description or ''} {category or ''} {operation or ''} {item_id}".lower()

        # Проверяем совпадение с поисковыми терминами
        match_score = 0
        for term in search_terms:
            if term in search_text:
                match_score += 1

        # Если есть хотя бы одно совпадение
        if match_score > 0:
            results.append(item)

    # Сортируем по релевантности
    def relevance_score(item):
        item_id, title, price, category, operation, description = item
        search_text = f"{title or ''} {description or ''} {category or ''} {operation or ''}".lower()
        score = 0
        for term in search_terms:
            if term in (title or "").lower():
                score += 3
            if term in (description or "").lower():
                score += 2
            if term in (category or "").lower():
                score += 1
            if term in (operation or "").lower():
                score += 1
        return score

    results.sort(key=relevance_score, reverse=True)
    return results


async def search_items_by_id(search_query: str, item_type: str, user_id: int) -> list:
    """Поиск товаров/услуг/предложений по ID"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        for item_id in id_list:
            try:
                item_id_int = int(item_id)

                if item_type == "product":
                    # Ищем в auto_products
                    cursor = await db.execute("""
                        SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                        FROM auto_products ap
                        LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                        WHERE ap.id = ?
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)
                    else:
                        # Ищем в order_requests
                        cursor = await db.execute("""
                            SELECT id, title, price, category, operation, description
                            FROM order_requests 
                            WHERE item_type = 'product' AND id = ? 
                        """, (item_id_int,))

                        item = await cursor.fetchone()
                        if item:
                            results.append(item)

                elif item_type == "service":
                    # Ищем в service_orders
                    cursor = await db.execute("""
                        SELECT id, title, price, category, operation, description
                        FROM service_orders 
                        WHERE id = ?
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)

                else:  # offer
                    # Ищем в order_requests
                    cursor = await db.execute("""
                        SELECT id, title, price, category, operation, description
                        FROM order_requests 
                        WHERE item_type = 'offer'
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)

            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results


# ========== ОБРАБОТЧИКИ ПОИСКА ПО НАЗВАНИЮ/ТЕГАМ ==========

@dp.callback_query(F.data == "search_products_by_name")
async def search_products_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Поиск товаров по названию или тегам"""
    await state.set_state(SearchStates.waiting_search_in_products)
    await state.update_data(search_by_id=False)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🔍 **Поиск товаров по названию или тегам**\n\n"
        "Введите поисковый запрос:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_services_by_name")
async def search_services_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Поиск услуг по названию или тегам"""
    await state.set_state(SearchStates.waiting_search_in_services)
    await state.update_data(search_by_id=False)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🔍 **Поиск услуг по названию или тегам**\n\n"
        "Введите поисковый запрос:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_offers_by_name")
async def search_offers_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Поиск предложений по названию или тегам"""
    await state.set_state(SearchStates.waiting_search_in_offers)
    await state.update_data(search_by_id=False)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🔍 **Поиск предложений по названию или тегам**\n\n"
        "Введите поисковый запрос:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ========== ОБРАБОТЧИКИ ПОИСКА ПО КАТЕГОРИИ ==========

@dp.callback_query(F.data == "search_products_by_category")
async def search_products_by_category_start(callback: CallbackQuery):
    """Поиск товаров по категории"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Получаем категории из auto_categories
            cursor = await db.execute("""
                SELECT DISTINCT name FROM auto_categories 
                WHERE type = 'product' AND name IS NOT NULL AND name != ''
                ORDER BY name
            """)
            categories = await cursor.fetchall()
        except:
            categories = []

        if not categories:
            try:
                # Если нет в auto_categories, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT category FROM order_requests 
                    WHERE item_type = 'product' AND category IS NOT NULL AND category != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY category
                """)
                categories = await cursor.fetchall()
            except:
                categories = []

        if categories:
            for category in categories:
                if category[0]:
                    builder.add(types.InlineKeyboardButton(
                        text=category[0],
                        callback_data=f"prod_cat_search:{category[0]}"
                    ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Категории не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🏷 **Поиск товаров по категории**\n\n"
        "Выберите категорию для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_services_by_category")
async def search_services_by_category_start(callback: CallbackQuery):
    """Поиск услуг по категории"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Получаем категории из service_orders
            cursor = await db.execute("""
                SELECT DISTINCT category FROM service_orders 
                WHERE category IS NOT NULL AND category != ''
                AND status IN ('active', 'approved', 'processing')
                ORDER BY category
            """)
            categories = await cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении категорий услуг: {e}")
            categories = []

        if not categories:
            try:
                # Если нет в service_orders, берем из auto_categories
                cursor = await db.execute("""
                    SELECT DISTINCT name FROM auto_categories 
                    WHERE type = 'service' AND name IS NOT NULL AND name != ''
                    ORDER BY name
                """)
                categories = await cursor.fetchall()
            except:
                categories = []

        if categories:
            for category in categories:
                if category[0]:
                    builder.add(types.InlineKeyboardButton(
                        text=category[0],
                        callback_data=f"serv_cat_search:{category[0]}"
                    ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Категории не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🏷 **Поиск услуг по категории**\n\n"
        "Выберите категорию для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_offers_by_category")
async def search_offers_by_category_start(callback: CallbackQuery):
    """Поиск предложений по категории"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Получаем категории из order_requests для предложений
            cursor = await db.execute("""
                SELECT DISTINCT category FROM order_requests 
                WHERE item_type = 'offer' AND category IS NOT NULL AND category != '' 
                AND status IN ('active', 'approved', 'processing')
                ORDER BY category
            """)
            categories = await cursor.fetchall()
        except:
            categories = []

        if categories:
            for category in categories:
                if category[0]:
                    builder.add(types.InlineKeyboardButton(
                        text=category[0],
                        callback_data=f"offer_cat_search:{category[0]}"
                    ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Категории не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🏷 **Поиск предложений по категории**\n\n"
        "Выберите категорию для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("prod_cat_search:"))
async def search_products_by_category_execute(callback: CallbackQuery):
    """Выполнение поиска товаров по категории"""
    category = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в auto_products
            cursor = await db.execute("""
                SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                FROM auto_products ap
                JOIN auto_categories ac ON ap.category_id = ac.id
                WHERE ac.name = ? AND ap.status = 'active'
                ORDER BY ap.created_at DESC
            """, (category,))
            auto_results = await cursor.fetchall()

            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'product' AND category = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (category,))
            order_results = await cursor.fetchall()

            results = list(auto_results) + list(order_results)

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Категория: {category}", "category", "products", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске товаров по категории: {e}")

    await display_search_results(callback, results, f"категории: '{category}'", "product")


@dp.callback_query(F.data.startswith("serv_cat_search:"))
async def search_services_by_category_execute(callback: CallbackQuery):
    """Выполнение поиска услуг по категории"""
    category = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в service_orders
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM service_orders 
                WHERE category = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (category,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Категория: {category}", "category", "services", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске услуг по категории: {e}")

    await display_search_results(callback, results, f"категории: '{category}'", "service")


@dp.callback_query(F.data.startswith("offer_cat_search:"))
async def search_offers_by_category_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по категории"""
    category = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'offer' AND category = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (category,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Категория: {category}", "category", "offers", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске предложений по категории: {e}")

    await display_search_results(callback, results, f"категории: '{category}'", "offer")


# ========== ОБРАБОТЧИКИ ПОИСКА ПО КЛАССУ ==========

@dp.callback_query(F.data == "search_products_by_class")
async def search_products_by_class_start(callback: CallbackQuery):
    """Поиск товаров по классу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Получаем классы из product_classes
            cursor = await db.execute("""
                SELECT name FROM product_classes 
                WHERE name IS NOT NULL AND name != '' 
                ORDER BY name
            """)
            items = await cursor.fetchall()
        except:
            items = []

        if not items:
            try:
                # Если нет в product_classes, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_class FROM order_requests 
                    WHERE item_type = 'product' AND item_class IS NOT NULL AND item_class != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_class
                """)
                items = await cursor.fetchall()
            except:
                items = []

        if items:
            for i in items:
                class_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=class_name,
                    callback_data=f"prod_cls_search:{class_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Классы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📊 **Поиск товаров по классу**\n\n"
        "Выберите класс для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_services_by_class")
async def search_services_by_class_start(callback: CallbackQuery):
    """Поиск услуг по классу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Проверяем существование таблицы service_classes
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_classes'")
            table_exists = await cursor.fetchone()

            if table_exists:
                cursor = await db.execute(
                    "SELECT name FROM service_classes WHERE name IS NOT NULL AND name != '' ORDER BY name")
                items = await cursor.fetchall()
            else:
                items = []
        except:
            items = []

        if not items:
            try:
                # Если нет в service_classes, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_class FROM order_requests 
                    WHERE item_type = 'service' AND item_class IS NOT NULL AND item_class != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_class
                """)
                items = await cursor.fetchall()
            except:
                items = []

        if items:
            for i in items:
                class_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=class_name,
                    callback_data=f"serv_cls_search:{class_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Классы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📊 **Поиск услуг по классу**\n\n"
        "Выберите класс для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_offers_by_class")
async def search_offers_by_class_start(callback: CallbackQuery):
    """Поиск предложений по классу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT DISTINCT item_class FROM order_requests 
                WHERE item_type = 'offer' AND item_class IS NOT NULL AND item_class != '' 
                AND status IN ('active', 'approved', 'processing')
                ORDER BY item_class
            """)
            items = await cursor.fetchall()
        except:
            items = []

        if items:
            for i in items:
                class_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=class_name,
                    callback_data=f"offer_cls_search:{class_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Классы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📊 **Поиск предложений по классу**\n\n"
        "Выберите класс для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("prod_cls_search:"))
async def search_products_by_class_execute(callback: CallbackQuery):
    """Выполнение поиска товаров по классу"""
    item_class = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в auto_products через product_classes
            cursor = await db.execute("""
                SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                FROM auto_products ap
                JOIN product_classes pc ON ap.class_id = pc.id
                LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                WHERE pc.name = ? AND ap.status = 'active'
                ORDER BY ap.created_at DESC
            """, (item_class,))
            auto_results = await cursor.fetchall()

            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'product' AND item_class = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_class,))
            order_results = await cursor.fetchall()

            results = list(auto_results) + list(order_results)

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Класс: {item_class}", "class", "products", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске товаров по классу: {e}")

    await display_search_results(callback, results, f"классу: '{item_class}'", "product")


@dp.callback_query(F.data.startswith("serv_cls_search:"))
async def search_services_by_class_execute(callback: CallbackQuery):
    """Выполнение поиска услуг по классу"""
    item_class = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Для услуг поиск по классу в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'service' AND item_class = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_class,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Класс: {item_class}", "class", "services", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске услуг по классу: {e}")

    await display_search_results(callback, results, f"классу: '{item_class}'", "service")


@dp.callback_query(F.data.startswith("offer_cls_search:"))
async def search_offers_by_class_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по классу"""
    item_class = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'offer' AND item_class = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_class,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Класс: {item_class}", "class", "offers", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске предложений по классу: {e}")

    await display_search_results(callback, results, f"классу: '{item_class}'", "offer")


# ========== ОБРАБОТЧИКИ ПОИСКА ПО ТИПУ ==========

@dp.callback_query(F.data == "search_products_by_type")
async def search_products_by_type_start(callback: CallbackQuery):
    """Поиск товаров по типу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Проверяем существование таблицы product_types
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_types'")
            table_exists = await cursor.fetchone()

            if table_exists:
                cursor = await db.execute(
                    "SELECT name FROM product_types WHERE name IS NOT NULL AND name != '' ORDER BY name")
                items = await cursor.fetchall()
            else:
                items = []
        except:
            items = []

        if not items:
            try:
                # Если нет в product_types, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_type_detail FROM order_requests 
                    WHERE item_type = 'product' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_type_detail
                """)
                items = await cursor.fetchall()
            except:
                items = []

        if items:
            for i in items:
                type_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=type_name,
                    callback_data=f"prod_type_search:{type_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Типы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Поиск товаров по типу**\n\n"
        "Выберите тип для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_services_by_type")
async def search_services_by_type_start(callback: CallbackQuery):
    """Поиск услуг по типу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Проверяем существование таблицы service_types
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_types'")
            table_exists = await cursor.fetchone()

            if table_exists:
                cursor = await db.execute(
                    "SELECT name FROM service_types WHERE name IS NOT NULL AND name != '' ORDER BY name")
                items = await cursor.fetchall()
            else:
                items = []
        except:
            items = []

        if not items:
            try:
                # Если нет в service_types, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_type_detail FROM order_requests 
                    WHERE item_type = 'service' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_type_detail
                """)
                items = await cursor.fetchall()
            except:
                items = []

        if items:
            for i in items:
                type_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=type_name,
                    callback_data=f"serv_type_search:{type_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Типы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Поиск услуг по типу**\n\n"
        "Выберите тип для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_offers_by_type")
async def search_offers_by_type_start(callback: CallbackQuery):
    """Поиск предложений по типу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT DISTINCT item_type_detail FROM order_requests 
                WHERE item_type = 'offer' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
                AND status IN ('active', 'approved', 'processing')
                ORDER BY item_type_detail
            """)
            items = await cursor.fetchall()
        except:
            items = []

        if items:
            for i in items:
                type_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=type_name,
                    callback_data=f"offer_type_search:{type_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Типы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Поиск предложений по типу**\n\n"
        "Выберите тип для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("prod_type_search:"))
async def search_products_by_type_execute(callback: CallbackQuery):
    """Выполнение поиска товаров по типу"""
    item_type_detail = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'product' AND item_type_detail = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_type_detail,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Тип: {item_type_detail}", "type", "products", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске товаров по типу: {e}")

    await display_search_results(callback, results, f"типу: '{item_type_detail}'", "product")


@dp.callback_query(F.data.startswith("serv_type_search:"))
async def search_services_by_type_execute(callback: CallbackQuery):
    """Выполнение поиска услуг по типу"""
    item_type_detail = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'service' AND item_type_detail = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_type_detail,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Тип: {item_type_detail}", "type", "services", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске услуг по типу: {e}")

    await display_search_results(callback, results, f"типу: '{item_type_detail}'", "service")


@dp.callback_query(F.data.startswith("offer_type_search:"))
async def search_offers_by_type_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по типу"""
    item_type_detail = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'offer' AND item_type_detail = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_type_detail,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Тип: {item_type_detail}", "type", "offers", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске предложений по типу: {e}")

    await display_search_results(callback, results, f"типу: '{item_type_detail}'", "offer")


# ========== ОБРАБОТЧИКИ ПОИСКА ПО ВИДУ ==========

@dp.callback_query(F.data == "search_products_by_kind")
async def search_products_by_kind_start(callback: CallbackQuery):
    """Поиск товаров по виду"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Проверяем существование таблицы product_kinds
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_kinds'")
            table_exists = await cursor.fetchone()

            if table_exists:
                cursor = await db.execute(
                    "SELECT name FROM product_kinds WHERE name IS NOT NULL AND name != '' ORDER BY name")
                items = await cursor.fetchall()
            else:
                items = []
        except:
            items = []

        if not items:
            try:
                # Если нет в product_kinds, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_kind FROM order_requests 
                    WHERE item_type = 'product' AND item_kind IS NOT NULL AND item_kind != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_kind
                """)
                items = await cursor.fetchall()
            except:
                items = []

        if items:
            for i in items:
                kind_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=kind_name,
                    callback_data=f"prod_kind_search:{kind_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Виды не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    await callback.message.edit_text(
        "👁 **Поиск товаров по виду**\n\n"
        "Выберите вид для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_services_by_kind")
async def search_services_by_kind_start(callback: CallbackQuery):
    """Поиск услуг по виду"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Проверяем существование таблицы service_kinds
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_kinds'")
            table_exists = await cursor.fetchone()

            if table_exists:
                cursor = await db.execute(
                    "SELECT name FROM service_kinds WHERE name IS NOT NULL AND name != '' ORDER BY name")
                items = await cursor.fetchall()
            else:
                items = []
        except:
            items = []

        if not items:
            try:
                # Если нет в service_kinds, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_kind FROM order_requests 
                    WHERE item_type = 'service' AND item_kind IS NOT NULL AND item_kind != '' 
                    AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_kind
                """)
                items = await cursor.fetchall()
            except:
                items = []

        if items:
            for i in items:
                kind_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=kind_name,
                    callback_data=f"serv_kind_search:{kind_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Виды не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    await callback.message.edit_text(
        "👁 **Поиск услуг по виду**\n\n"
        "Выберите вид для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_offers_by_kind")
async def search_offers_by_kind_start(callback: CallbackQuery):
    """Поиск предложений по виду"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT DISTINCT item_kind FROM order_requests 
                WHERE item_type = 'offer' AND item_kind IS NOT NULL AND item_kind != '' 
                AND status IN ('active', 'approved', 'processing')
                ORDER BY item_kind
            """)
            items = await cursor.fetchall()
        except:
            items = []

        if items:
            for i in items:
                kind_name = i[0]
                builder.add(types.InlineKeyboardButton(
                    text=kind_name,
                    callback_data=f"offer_kind_search:{kind_name}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Виды не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    await callback.message.edit_text(
        "👁 **Поиск предложений по виду**\n\n"
        "Выберите вид для поиска:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("prod_kind_search:"))
async def search_products_by_kind_execute(callback: CallbackQuery):
    """Выполнение поиска товаров по виду"""
    item_kind = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'product' AND item_kind = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_kind,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Вид: {item_kind}", "kind", "products", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске товаров по виду: {e}")

    await display_search_results(callback, results, f"виду: '{item_kind}'", "product")


@dp.callback_query(F.data.startswith("serv_kind_search:"))
async def search_services_by_kind_execute(callback: CallbackQuery):
    """Выполнение поиска услуг по виду"""
    item_kind = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'service' AND item_kind = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_kind,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Вид: {item_kind}", "kind", "services", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске услуг по виду: {e}")

    await display_search_results(callback, results, f"виду: '{item_kind}'", "service")


@dp.callback_query(F.data.startswith("offer_kind_search:"))
async def search_offers_by_kind_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по виду"""
    item_kind = callback.data.split(":")[1]
    user_id = callback.from_user.id

    results = []

    async with aiosqlite.connect("bot_database.db") as db:
        try:
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, description
                FROM order_requests 
                WHERE item_type = 'offer' AND item_kind = ? AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """, (item_kind,))
            results = await cursor.fetchall()

            # Сохраняем в историю поиска
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"Вид: {item_kind}", "kind", "offers", datetime.now().isoformat())
            )
            await db.commit()
        except Exception as e:
            print(f"Ошибка при поиске предложений по виду: {e}")

    await display_search_results(callback, results, f"виду: '{item_kind}'", "offer")


# ========== ОБРАБОТЧИКИ ПОИСКА ПО ID ==========

@dp.callback_query(F.data == "search_products_by_id")
async def search_products_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Поиск товаров по ID в каталоге"""
    await state.set_state(SearchStates.waiting_search_in_products)
    await state.update_data(search_by_id=True)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🆔 **Поиск товаров по ID**\n\n"
        "Введите ID товара (можно несколько через запятую):",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_services_by_id")
async def search_services_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Поиск услуг по ID в каталоге"""


    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🆔 **Поиск услуг по ID**\n\n"
        "Введите ID услуги (можно несколько через запятую):",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "search_offers_by_id")
async def search_offers_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Поиск предложений по ID в каталоге"""
    await state.set_state(SearchStates.waiting_search_in_offers)
    await state.update_data(search_by_id=True)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🆔 **Поиск предложений по ID**\n\n"
        "Введите ID предложения (можно несколько через запятую):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(SearchStates.waiting_search_in_services)
    await state.update_data(search_by_id=True)
    await callback.answer()


# ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ДЛЯ ПОИСКА ==========

@dp.message(SearchStates.waiting_search_in_products)
async def process_search_in_products(message: Message, state: FSMContext):
    """Обработка поиска в товарах"""
    await process_search_message(message, state, "product")


@dp.message(SearchStates.waiting_search_in_services)
async def process_search_in_services(message: Message, state: FSMContext):
    """Обработка поиска в услугах"""
    await process_search_message(message, state, "service")


@dp.message(SearchStates.waiting_search_in_offers)
async def process_search_in_offers(message: Message, state: FSMContext):
    """Обработка поиска в предложениях"""
    await process_search_message(message, state, "offer")


async def process_search_message(message: Message, state: FSMContext, item_type: str):
    """Обработка поискового сообщения"""
    search_query = message.text.strip()
    if not search_query:
        await message.answer("❌ Введите поисковый запрос!")
        return

    user_id = message.from_user.id
    state_data = await state.get_data()
    search_by_id = state_data.get("search_by_id", False)

    # Сохраняем историю поиска
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            await db.execute(
                "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, search_query, "quick", f"{item_type}s", datetime.now().isoformat())
            )
            await db.commit()
        except:
            pass  # Если таблицы нет, пропускаем

    # Выполняем поиск
    if search_by_id:
        results = await search_items_by_id(search_query, item_type, user_id)
        search_type_text = "по ID"
    else:
        results = await perform_search_in_catalog(search_query, item_type, user_id)
        search_type_text = "по названию/тегам"

    if not results:
        builder = InlineKeyboardBuilder()

        if item_type == "product":
            back_callback = "search_in_products"
            if search_by_id:
                builder.add(
                    types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_products_by_id"))
            else:
                builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_products_by_name"))
            builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))
        elif item_type == "service":
            back_callback = "search_in_services"
            if search_by_id:
                builder.add(
                    types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_services_by_id"))
            else:
                builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_services_by_name"))
            builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))
        else:  # offer
            back_callback = "search_in_offers"
            if search_by_id:
                builder.add(types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_offers_by_id"))
            else:
                builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_offers_by_name"))
            builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

        builder.adjust(1)

        await message.answer(
            f"🔍 **Результаты поиска {search_type_text} по запросу: '{search_query}'**\n\n"
            "❌ Ничего не найдено.",
            reply_markup=builder.as_markup()
        )
        await state.clear()
        return

    # Формируем заголовок результатов
    catalog_name = "товаров" if item_type == "product" else "услуг" if item_type == "service" else "предложений"

    if search_by_id:
        response = f"🆔 **Результаты поиска {catalog_name} по ID: '{search_query}'**\n\n"
    else:
        response = f"🔍 **Результаты поиска в {catalog_name}: '{search_query}'**\n\n"

    response += f"📊 Найдено: {len(results)} позиций\n\n"

    # Формируем список результатов
    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        if item_type == "product":
            response += f"{i}. 📦 **{title}**\n"
        elif item_type == "service":
            response += f"{i}. 🛠 **{title}**\n"
        else:
            response += f"{i}. 🤝 **{title}**\n"

        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        # Короткое описание
        if description and len(description) > 0:
            short_desc = description[:80] + "..." if len(description) > 80 else description
            response += f"   📝 {short_desc}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text=f"{i}. {title[:15]}...",
            callback_data=f"view_item_{item_type}_{item_id}"
        ))

    builder.adjust(1)

    # Дополнительные кнопки
    if item_type == "product":
        if search_by_id:
            builder.row(types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_products_by_id"))
        else:
            builder.row(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_products_by_name"))
        builder.row(types.InlineKeyboardButton(text="◀️ В каталог товаров", callback_data="product_catalog"))
    elif item_type == "service":
        if search_by_id:
            builder.row(types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_services_by_id"))
        else:
            builder.row(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_services_by_name"))
        builder.row(types.InlineKeyboardButton(text="◀️ В каталог услуг", callback_data="service_catalog"))
    else:  # offer
        if search_by_id:
            builder.row(types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_offers_by_id"))
        else:
            builder.row(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_offers_by_name"))
        builder.row(types.InlineKeyboardButton(text="◀️ В каталог предложений", callback_data="property_catalog"))

    await message.answer(response, reply_markup=builder.as_markup())
    await state.clear()


# ========== ФУНКЦИЯ ОТОБРАЖЕНИЯ РЕЗУЛЬТАТОВ ==========

async def display_search_results(callback: CallbackQuery, results: list, search_criteria: str, item_type: str):
    """Отображение результатов поиска"""
    if not results:
        builder = InlineKeyboardBuilder()

        catalog_name = "товаров" if item_type == "product" else "услуг" if item_type == "service" else "предложений"

        # Определяем кнопку "назад" в зависимости от типа поиска
        if "категории" in search_criteria:
            builder.add(types.InlineKeyboardButton(text=f"🏷 Выбрать другую категорию",
                                                   callback_data=f"search_{item_type}s_by_category"))
        elif "классу" in search_criteria:
            builder.add(types.InlineKeyboardButton(text=f"📊 Выбрать другой класс",
                                                   callback_data=f"search_{item_type}s_by_class"))
        elif "типу" in search_criteria:
            builder.add(
                types.InlineKeyboardButton(text=f"📋 Выбрать другой тип", callback_data=f"search_{item_type}s_by_type"))
        elif "виду" in search_criteria:
            builder.add(
                types.InlineKeyboardButton(text=f"👁 Выбрать другой вид", callback_data=f"search_{item_type}s_by_kind"))

        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data=f"search_in_{item_type}s"))

        # Кнопка в каталог
        if item_type == "product":
            builder.add(types.InlineKeyboardButton(text="◀️ В каталог товаров", callback_data="product_catalog"))
        elif item_type == "service":
            builder.add(types.InlineKeyboardButton(text="◀️ В каталог услуг", callback_data="service_catalog"))
        else:
            builder.add(types.InlineKeyboardButton(text="◀️ В каталог предложений", callback_data="property_catalog"))

        builder.adjust(1)

        await callback.message.edit_text(
            f"**Результаты поиска {catalog_name} по {search_criteria}**\n\n"
            "❌ Ничего не найдено.\n\n"
            "Попробуйте выбрать другие параметры.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # Формируем заголовок
    catalog_name = "товаров" if item_type == "product" else "услуг" if item_type == "service" else "предложений"

    response = f"**Результаты поиска {catalog_name} по {search_criteria}**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    # Формируем список результатов
    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        if item_type == "product":
            response += f"{i}. 📦 **{title}**\n"
        elif item_type == "service":
            response += f"{i}. 🛠 **{title}**\n"
        else:
            response += f"{i}. 🤝 **{title}**\n"

        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        # Короткое описание
        if description and len(description) > 0:
            short_desc = description[:80] + "..." if len(description) > 80 else description
            response += f"   📝 {short_desc}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text=f"{i}. {title[:15]}...",
            callback_data=f"view_item_{item_type}_{item_id}"
        ))

    builder.adjust(1)

    # Кнопки навигации
    if "категории" in search_criteria:
        builder.row(types.InlineKeyboardButton(text="🏷 Выбрать другую категорию",
                                               callback_data=f"search_{item_type}s_by_category"))
    elif "классу" in search_criteria:
        builder.row(
            types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data=f"search_{item_type}s_by_class"))
    elif "типу" in search_criteria:
        builder.row(
            types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data=f"search_{item_type}s_by_type"))
    elif "виду" in search_criteria:
        builder.row(
            types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data=f"search_{item_type}s_by_kind"))

    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data=f"search_in_{item_type}s"))

    # Кнопка в каталог
    if item_type == "product":
        builder.row(types.InlineKeyboardButton(text="◀️ В каталог товаров", callback_data="product_catalog"))
    elif item_type == "service":
        builder.row(types.InlineKeyboardButton(text="◀️ В каталог услуг", callback_data="service_catalog"))
    else:
        builder.row(types.InlineKeyboardButton(text="◀️ В каталог предложений", callback_data="property_catalog"))

    await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


# ========== ОБРАБОТЧИКИ ДЛЯ ПРОСМОТРА ТОВАРОВ ==========

@dp.callback_query(F.data.startswith("view_item_"))
async def view_search_result_item(callback: CallbackQuery):
    """Просмотр найденного товара/услуги/предложения"""
    if await check_blocked_user(callback):
        return

    data_parts = callback.data.split("_")
    if len(data_parts) < 4:
        await callback.answer("❌ Ошибка при загрузке товара", show_alert=True)
        return

    item_type = data_parts[2]
    item_id = data_parts[3]

    # Получаем информацию о товаре
    item = None
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            if item_type == "service":
                # Для услуг ищем в service_orders
                cursor = await db.execute("""
                    SELECT 
                        id, user_id, operation, category, title, description, price,
                        availability, contact, status, created_at
                    FROM service_orders 
                    WHERE id = ?
                """, (item_id,))
                item_data = await cursor.fetchone()

                if item_data:
                    item = {
                        'id': item_data[0],
                        'user_id': item_data[1],
                        'operation': item_data[2],
                        'category': item_data[3],
                        'title': item_data[4],
                        'description': item_data[5],
                        'price': item_data[6],
                        'availability': item_data[7],
                        'contact': item_data[8],
                        'status': item_data[9],
                        'created_at': item_data[10]
                    }

            elif item_type == "product" or item_type == "offer":
                # Для товаров и предложений ищем в order_requests
                cursor = await db.execute("""
                    SELECT 
                        id, user_id, operation, item_type, category, item_class, item_kind,
                        item_type_detail, title, purpose, name, creation_date, condition,
                        specifications, advantages, additional_info, images, price,
                        availability, detailed_specs, reviews, rating, delivery_info,
                        supplier_info, statistics, deadline, tags, contact, status, created_at
                    FROM order_requests 
                    WHERE id = ? AND item_type = ?
                """, (item_id, item_type))
                item_data = await cursor.fetchone()

                if item_data:
                    item = {
                        'id': item_data[0],
                        'user_id': item_data[1],
                        'operation': item_data[2],
                        'item_type': item_data[3],
                        'category': item_data[4],
                        'item_class': item_data[5],
                        'item_kind': item_data[6],
                        'item_type_detail': item_data[7],
                        'title': item_data[8],
                        'purpose': item_data[9],
                        'name': item_data[10],
                        'creation_date': item_data[11],
                        'condition': item_data[12],
                        'specifications': item_data[13],
                        'advantages': item_data[14],
                        'additional_info': item_data[15],
                        'images': item_data[16],
                        'price': item_data[17],
                        'availability': item_data[18],
                        'detailed_specs': item_data[19],
                        'reviews': item_data[20],
                        'rating': item_data[21],
                        'delivery_info': item_data[22],
                        'supplier_info': item_data[23],
                        'statistics': item_data[24],
                        'deadline': item_data[25],
                        'tags': item_data[26],
                        'contact': item_data[27],
                        'status': item_data[28],
                        'created_at': item_data[29]
                    }
        except Exception as e:
            print(f"Ошибка при получении данных товара: {e}")

    if not item:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    # Формируем карточку
    response = ""

    if item_type == "product":
        response += "📦 **КАРТОЧКА ТОВАРА**\n\n"
    elif item_type == "service":
        response += "🛠 **КАРТОЧКА УСЛУГИ**\n\n"
    else:
        response += "🤝 **КАРТОЧКА ПРЕДЛОЖЕНИЯ**\n\n"

    # Основная информация
    response += f"🏷 **{item.get('title', 'Без названия')}**\n"
    response += f"🆔 ID: {item.get('id', 'N/A')}\n"

    if item.get('item_class'):
        response += f"📊 Класс: {item['item_class']}\n"
    if item.get('category'):
        response += f"🏷 Категория: {item['category']}\n"
    if item.get('item_kind'):
        response += f"👁 Вид: {item['item_kind']}\n"

    # Операция
    if item.get('operation'):
        response += f"🎯 Операция: {item['operation']}\n"

    # Цена
    if item.get('price'):
        response += f"💰 Цена: {item['price']}\n"

    # Наличие
    if item.get('availability'):
        response += f"📦 Наличие: {item['availability']}\n"

    # Срок
    if item.get('deadline'):
        response += f"⏰ Желательный срок: {item['deadline']}\n"

    # Теги
    if item.get('tags'):
        response += f"🏷 Теги: {item['tags']}\n"

    # Контакты
    if item.get('contact'):
        response += f"📞 Контакты: {item['contact']}\n"

    response += "\n──────\n\n"

    # Дополнительная информация
    if item.get('description'):
        response += f"📝 **Описание:**\n{item['description']}\n\n"

    if item.get('purpose'):
        response += f"📝 **Назначение:**\n{item['purpose']}\n\n"

    if item.get('specifications'):
        response += f"⚙️ **Характеристики:**\n{item['specifications']}\n\n"

    if item.get('advantages'):
        response += f"✅ **Преимущества:**\n{item['advantages']}\n\n"

    if item.get('condition'):
        response += f"🔄 **Состояние:**\n{item['condition']}\n\n"

    if item.get('detailed_specs'):
        response += f"📋 **Детальные характеристики:**\n{item['detailed_specs']}\n\n"

    if item.get('reviews'):
        response += f"💬 **Отзывы:**\n{item['reviews']}\n\n"

    if item.get('rating'):
        response += f"⭐ **Рейтинг:** {item['rating']}/10\n\n"

    if item.get('delivery_info'):
        response += f"🚚 **Доставка и оплата:**\n{item['delivery_info']}\n\n"

    if item.get('supplier_info'):
        response += f"🏢 **Поставщик:**\n{item['supplier_info']}\n\n"

    if item.get('additional_info'):
        response += f"📄 **Дополнительная информация:**\n{item['additional_info']}\n\n"

    # Статус
    status = item.get('status', 'unknown')
    status_icon = "🆕" if status == "new" else "📊" if status == "processing" else "✅"
    response += f"{status_icon} **Статус:** {status}\n"

    # Дата создания
    if item.get('created_at'):
        try:
            date_str = datetime.fromisoformat(item['created_at']).strftime("%d.%m.%Y %H:%M")
            response += f"📅 **Дата создания:** {date_str}\n"
        except:
            pass

    # Кнопки действий
    builder = InlineKeyboardBuilder()

    # Основные действия
    operation = item.get('operation', '')
    if operation and "прода" in str(operation).lower():
        builder.add(types.InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_item_{item_type}_{item_id}"))
    else:
        builder.add(types.InlineKeyboardButton(text="💰 Продать", callback_data=f"sell_item_{item_type}_{item_id}"))

    builder.add(types.InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_to_cart_{item_type}_{item_id}"))
    if item.get('user_id'):  # user_id
        builder.add(types.InlineKeyboardButton(text="💬 Связаться", callback_data=f"contact_seller_{item['user_id']}"))

    builder.adjust(2)

    # Дополнительные кнопки
    builder.row(types.InlineKeyboardButton(text="📋 Подробнее", callback_data=f"item_details_{item_type}_{item_id}"))
    builder.row(types.InlineKeyboardButton(text="⭐ Оценить", callback_data=f"rate_item_{item_type}_{item_id}"))

    # Кнопка назад в зависимости от типа
    if item_type == "product":
        builder.row(types.InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="search_in_products"))
    elif item_type == "service":
        builder.row(types.InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="search_in_services"))
    else:
        builder.row(types.InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="search_in_offers"))

    await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("add_to_cart_"))
async def add_search_result_to_cart(callback: CallbackQuery):
    """Добавление найденного товара в корзину"""
    if await check_blocked_user(callback):
        return

    data_parts = callback.data.split("_")
    if len(data_parts) < 4:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    item_type = data_parts[3]
    item_id = data_parts[4]
    user_id = callback.from_user.id

    # Проверяем, существует ли товар
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            if item_type == "service":
                # Для услуг проверяем в service_orders
                cursor = await db.execute("""
                    SELECT id, title, price FROM service_orders 
                    WHERE id = ? AND status IN ('active', 'approved', 'processing')
                """, (item_id,))
            else:
                # Для товаров и предложений проверяем в order_requests
                cursor = await db.execute("""
                    SELECT id, title, price FROM order_requests 
                    WHERE id = ? AND item_type = ? AND status IN ('active', 'approved', 'processing')
                """, (item_id, item_type))

            item = await cursor.fetchone()
        except Exception as e:
            print(f"Ошибка при проверке товара: {e}")
            item = None

        if not item:
            await callback.answer("❌ Товар не найден или недоступен", show_alert=True)
            return

        # Проверяем, не добавлен ли уже в корзину
        try:
            cursor = await db.execute("""
                SELECT id FROM cart_order 
                WHERE user_id = ? AND item_type = ? AND item_id = ?
            """, (user_id, item_type, item_id))

            existing = await cursor.fetchone()

            if existing:
                await callback.answer("✅ Уже в корзине", show_alert=True)
                return

            # Добавляем в корзину
            await db.execute("""
                INSERT INTO cart_order (
                    user_id, item_type, item_id, quantity, selected_options, price, added_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                item_type,
                item_id,
                1,
                "",
                item[2] or "0",
                datetime.now().isoformat()
            ))

            await db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении в корзину: {e}")

    await callback.answer("✅ Добавлено в корзину", show_alert=True)

    # Определяем, откуда пришли
    back_callback = "search_in_products"
    catalog_name = "товаров"
    if item_type == "service":
        back_callback = "search_in_services"
        catalog_name = "услуг"
    elif item_type == "offer":
        back_callback = "search_in_offers"
        catalog_name = "предложений"

    # Показываем сообщение с подтверждением
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data=back_callback))
    builder.adjust(1)

    await callback.message.answer(
        f"✅ Товар добавлен в корзину!\n\n"
        f"📦 **{item[1]}**\n"
        f"🆔 ID: {item_id}\n"
        f"📋 Каталог: {catalog_name}\n\n"
        f"Вы можете перейти в корзину для оформления заказа.",
        reply_markup=builder.as_markup()
    )


# Инициализация таблицы истории поиска
async def init_search_history_table():
    """Инициализация таблицы истории поиска"""
    async with aiosqlite.connect("bot_database.db") as db:
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    search_query TEXT NOT NULL,
                    search_type TEXT NOT NULL,
                    catalog_type TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            await db.commit()
        except:
            pass


# Экспорт функции для добавления кнопки поиска
def get_search_system_handlers():
    """Получить обработчики системы поиска"""
    return dp