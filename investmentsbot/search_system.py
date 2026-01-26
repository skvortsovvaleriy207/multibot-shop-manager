from aiogram import F, types
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
import json
import hashlib
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user
from config import ADMIN_ID


class SearchStates(StatesGroup):
    """Состояния для системы поиска"""
    waiting_search_in_products = State()
    waiting_search_in_services = State()
    waiting_search_in_offers = State()  # Добавлено состояние для поиска в предложениях
    waiting_search_in_orders = State()
    advanced_search_menu = State()  # Меню фильтров расширенного поиска
    waiting_filter_price = State()  # Ожидание ввода цены для фильтра
    waiting_price_min = State()
    waiting_price_max = State()
    waiting_rating_filter = State()


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
    builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID в каталоге", callback_data="search_products_by_id"))
    # builder.add(types.InlineKeyboardButton(text="🎯 Расширенный поиск", callback_data="advanced_search_products"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="product_catalog"))
    builder.adjust(2)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🔍 **Поиск**\n\nВыберите вариант для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🔍 **Поиск**\n\nВыберите вариант для поиска:",
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
    builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID в каталоге", callback_data="search_services_by_id"))
    # builder.add(types.InlineKeyboardButton(text="🎯 Расширенный поиск", callback_data="advanced_search_services"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="service_catalog"))
    builder.adjust(2)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🔍 **Поиск**\n\nВыберите вариант для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🔍 **Поиск**\n\nВыберите вариант для поиска:",
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
    builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID в каталоге", callback_data="search_offers_by_id"))
    # builder.add(types.InlineKeyboardButton(text="🎯 Расширенный поиск", callback_data="advanced_search_offers"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="property_catalog"))
    builder.adjust(2)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🔍 **Поиск в предложениях**\n\nВыберите вариант для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🔍 **Поиск в предложениях**\n\nВыберите вариант для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


# Поиск предложений по названию/тегам
@dp.callback_query(F.data == "search_offers_by_name")
async def search_offers_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Поиск предложений по названию или тегам"""
    await state.set_state(SearchStates.waiting_search_in_offers)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🔍 **Поиск предложений по названию или тегам**\n\nВведите поисковый запрос:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🔍 **Поиск предложений по названию или тегам**\n\nВведите поисковый запрос:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


# Поиск предложений по категории
@dp.callback_query(F.data == "search_offers_by_category")
async def search_offers_by_category_start(callback: CallbackQuery):
    """Поиск предложений по категории"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Получаем категории из order_requests для предложений
        cursor = await db.execute("""
            SELECT DISTINCT category FROM order_requests 
            WHERE item_type = 'offer' AND category IS NOT NULL AND category != '' 
            AND category != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY category
        """)
        categories = await cursor.fetchall()

        if categories:
            for category in categories:
                if category[0]:
                    # Create hash for category name to avoid 64 bytes limit
                    cat_hash = hashlib.md5(category[0].encode()).hexdigest()
                    builder.add(types.InlineKeyboardButton(
                        text=category[0],
                        callback_data=f"ocs:{cat_hash}"
                    ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Категории не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🏷 **Поиск предложений по категории**\n\nВыберите категорию для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🏷 **Поиск предложений по категории**\n\nВыберите категорию для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("ocs:"))
async def search_offers_by_category_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по категории"""
    cat_hash = callback.data.split(":")[1]

    user_id = callback.from_user.id
    category = None

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Find category by hash
        cursor = await db.execute("""
            SELECT DISTINCT category FROM order_requests 
            WHERE item_type = 'offer' AND category IS NOT NULL AND category != '' 
            AND category != 'None' AND status IN ('active', 'approved', 'processing')
        """)
        categories = await cursor.fetchall()
        
        for cat in categories:
            if cat[0] and hashlib.md5(cat[0].encode()).hexdigest() == cat_hash:
                category = cat[0]
                break
        
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return

        # Поиск в order_requests для предложений
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
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

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(text="🏷 Выбрать другую категорию", callback_data="search_offers_by_category"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
        builder.adjust(1)

        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.delete()
            await callback.message.answer(
                f"🏷 **Результаты поиска предложений по категории: '{category}'**\n\n"
                "❌ В этой категории ничего не найдено.\n\n"
                "Попробуйте выбрать другой категорию.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                f"🏷 **Результаты поиска предложений по категории: '{category}'**\n\n"
                "❌ В этой категории ничего не найдено.\n\n"
                "Попробуйте выбрать другой категорию.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return

    # Формируем результаты
    response = f"🏷 **Результаты поиска предложений по категории: '{category}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🤝 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text="👁 Просмотр",
            callback_data=f"view_item_offer_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"➕ {title[:15]}",
            callback_data=f"add_to_cart_offer_{item_id}"
        ))

    builder.adjust(2)

    # Дополнительные кнопки
    builder.row(
        types.InlineKeyboardButton(text="🏷 Выбрать другую категорию", callback_data="search_offers_by_category"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск предложений по классу
@dp.callback_query(F.data == "search_offers_by_class")
async def search_offers_by_class_start(callback: CallbackQuery):
    """Поиск предложений по классу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Получаем классы из order_requests для предложений
        cursor = await db.execute("""
            SELECT DISTINCT item_class FROM order_requests 
            WHERE item_type = 'offer' AND item_class IS NOT NULL AND item_class != '' 
            AND item_class != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_class
        """)
        items = await cursor.fetchall()

        if items:
            for i in items:
                class_name = i[0]
                cls_hash = hashlib.md5(class_name.encode()).hexdigest()
                builder.add(types.InlineKeyboardButton(
                    text=class_name,
                    callback_data=f"ocls:{cls_hash}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Классы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="📊 **Поиск предложений по классу**\n\nВыберите класс для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="📊 **Поиск предложений по классу**\n\nВыберите класс для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("ocls:"))
async def search_offers_by_class_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по классу"""
    cls_hash = callback.data.split(":")[1]

    user_id = callback.from_user.id
    item_class = None

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Resolve hash
        cursor = await db.execute("""
            SELECT DISTINCT item_class FROM order_requests 
            WHERE item_type = 'offer' AND item_class IS NOT NULL AND item_class != '' 
            AND item_class != 'None' AND status IN ('active', 'approved', 'processing')
        """)
        items = await cursor.fetchall()
        for i in items:
            if i[0] and hashlib.md5(i[0].encode()).hexdigest() == cls_hash:
                item_class = i[0]
                break
        
        if not item_class:
            await callback.answer("❌ Класс не найден", show_alert=True)
            return

        # Поиск в order_requests для предложений
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
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

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data="search_offers_by_class"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
        builder.adjust(1)

        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.delete()
            await callback.message.answer(
                f"📊 **Результаты поиска предложений по классу: '{item_class}'**\n\n"
                "❌ В этом классе ничего не найдено.\n\n"
                "Попробуйте выбрать другой класс.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                f"📊 **Результаты поиска предложений по классу: '{item_class}'**\n\n"
                "❌ В этом классе ничего не найдено.\n\n"
                "Попробуйте выбрать другой класс.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return

    # Формируем результаты
    response = f"📊 **Результаты поиска предложений по классу: '{item_class}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🤝 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text="👁 Просмотр",
            callback_data=f"view_item_offer_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"➕ {title[:15]}",
            callback_data=f"add_to_cart_offer_{item_id}"
        ))

    builder.adjust(2)

    # Дополнительные кнопки
    builder.row(types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data="search_offers_by_class"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск предложений по типу
@dp.callback_query(F.data == "search_offers_by_type")
async def search_offers_by_type_start(callback: CallbackQuery):
    """Поиск предложений по типу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Получаем типы из order_requests для предложений
        cursor = await db.execute("""
            SELECT DISTINCT item_type_detail FROM order_requests 
            WHERE item_type = 'offer' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
            AND item_type_detail != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_type_detail
        """)
        items = await cursor.fetchall()

        if items:
            for i in items:
                type_name = i[0]
                type_hash = hashlib.md5(type_name.encode()).hexdigest()
                builder.add(types.InlineKeyboardButton(
                    text=type_name,
                    callback_data=f"ots:{type_hash}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Типы не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="📋 **Поиск предложений по типу**\n\nВыберите тип для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="📋 **Поиск предложений по типу**\n\nВыберите тип для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("ots:"))
async def search_offers_by_type_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по типу"""
    type_hash = callback.data.split(":")[1]

    user_id = callback.from_user.id
    item_type_detail = None

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Resolve hash
        cursor = await db.execute("""
            SELECT DISTINCT item_type_detail FROM order_requests 
            WHERE item_type = 'offer' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
            AND item_type_detail != 'None' AND status IN ('active', 'approved', 'processing')
        """)
        items = await cursor.fetchall()
        for i in items:
            if i[0] and hashlib.md5(i[0].encode()).hexdigest() == type_hash:
                item_type_detail = i[0]
                break
        
        if not item_type_detail:
            await callback.answer("❌ Тип не найден", show_alert=True)
            return

        # Поиск в order_requests для предложений
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
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

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data="search_offers_by_type"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
        builder.adjust(1)

        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.delete()
            await callback.message.answer(
                f"📋 **Результаты поиска предложений по типу: '{item_type_detail}'**\n\n"
                "❌ В этом типе ничего не найдено.\n\n"
                "Попробуйте выбрать другой тип.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                f"📋 **Результаты поиска предложений по типу: '{item_type_detail}'**\n\n"
                "❌ В этом типе ничего не найдено.\n\n"
                "Попробуйте выбрать другой тип.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return

    # Формируем результаты
    response = f"📋 **Результаты поиска предложений по типу: '{item_type_detail}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🤝 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text="👁 Просмотр",
            callback_data=f"view_item_offer_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"➕ {title[:15]}",
            callback_data=f"add_to_cart_offer_{item_id}"
        ))

    builder.adjust(2)

    # Дополнительные кнопки
    builder.row(types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data="search_offers_by_type"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск предложений по виду
@dp.callback_query(F.data == "search_offers_by_kind")
async def search_offers_by_kind_start(callback: CallbackQuery):
    """Поиск предложений по виду"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Получаем виды из order_requests для предложений
        cursor = await db.execute("""
            SELECT DISTINCT item_kind FROM order_requests 
            WHERE item_type = 'offer' AND item_kind IS NOT NULL AND item_kind != '' 
            AND item_kind != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_kind
        """)
        items = await cursor.fetchall()

        if items:
            for i in items:
                view_name = i[0]
                view_hash = hashlib.md5(view_name.encode()).hexdigest()
                builder.add(types.InlineKeyboardButton(
                    text=view_name,
                    callback_data=f"ovs:{view_hash}"
                ))
        else:
            builder.add(types.InlineKeyboardButton(
                text="📭 Виды не найдены",
                callback_data="no_action"
            ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="👁 **Поиск предложений по виду**\n\n"
            "Выберите вид для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            "👁 **Поиск предложений по виду**\n\n"
            "Выберите вид для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("ovs:"))
async def search_offers_by_kind_execute(callback: CallbackQuery):
    """Выполнение поиска предложений по виду"""
    view_hash = callback.data.split(":")[1]

    user_id = callback.from_user.id
    item_kind = None

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Resolve hash
        cursor = await db.execute("""
            SELECT DISTINCT item_kind FROM order_requests 
            WHERE item_type = 'offer' AND item_kind IS NOT NULL AND item_kind != '' 
            AND item_kind != 'None' AND status IN ('active', 'approved', 'processing')
        """)
        items = await cursor.fetchall()
        for i in items:
            if i[0] and hashlib.md5(i[0].encode()).hexdigest() == view_hash:
                item_kind = i[0]
                break

        if not item_kind:
            await callback.answer("❌ Вид не найден", show_alert=True)
            return

        # Поиск в order_requests для предложений
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
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

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data="search_offers_by_kind"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
        builder.adjust(1)

        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.delete()
            await callback.message.answer(
                f"👁 **Результаты поиска предложений по виду: '{item_kind}'**\n\n"
                "❌ В этом виде ничего не найдено.\n\n"
                "Попробуйте выбрать другой вид.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                f"👁 **Результаты поиска предложений по виду: '{item_kind}'**\n\n"
                "❌ В этом виде ничего не найдено.\n\n"
                "Попробуйте выбрать другой вид.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return

    # Формируем результаты
    response = f"👁 **Результаты поиска предложений по виду: '{item_kind}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🤝 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text="👁 Просмотр",
            callback_data=f"view_item_offer_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"➕ {title[:15]}",
            callback_data=f"add_to_cart_offer_{item_id}"
        ))

    builder.adjust(2)

    # Дополнительные кнопки
    builder.row(types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data="search_offers_by_kind"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_offers"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск предложений по ID в каталоге
@dp.callback_query(F.data == "search_offers_by_id")
async def search_offers_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Поиск предложений по ID в каталоге"""
    await state.set_state(SearchStates.waiting_search_in_offers)
    await state.update_data(search_by_id=True)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🆔 **Поиск предложений по ID**\n\nВведите ID предложения (можно несколько через запятую):",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🆔 **Поиск предложений по ID**\n\nВведите ID предложения (можно несколько через запятую):",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.message(SearchStates.waiting_search_in_offers)
async def process_search_in_offers(message: Message, state: FSMContext):
    """Обработка поиска в предложениях"""
    search_query = message.text.strip()
    if not search_query:
        await message.answer("❌ Введите поисковый запрос!")
        return

    user_id = message.from_user.id
    state_data = await state.get_data()
    search_by_id = state_data.get("search_by_id", False)

    # Сохраняем историю поиска
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, search_query, "quick", "offers", datetime.now().isoformat())
        )
        await db.commit()

    # Выполняем поиск только в предложениях
    if search_by_id:
        # Поиск по ID
        results = await search_offers_by_id(search_query, user_id)
        search_type = "по ID"
    else:
        # Обычный поиск
        results = await perform_search_in_catalog(search_query, "offer", user_id)
        search_type = "в предложениях"

    if not results:
        builder = InlineKeyboardBuilder()
        if search_by_id:
            builder.add(types.InlineKeyboardButton(text="🆔 Поиск по ID", callback_data="search_offers_by_id"))
        else:
            builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_offers_by_name"))

        # builder.add(types.InlineKeyboardButton(text="🎯 Расширенный поиск", callback_data="advanced_search_offers"))
        builder.add(types.InlineKeyboardButton(text="📋 Создать заявку", callback_data="offer_card_form"))
        builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))
        builder.adjust(1)

        await message.answer(
            f"🔍 **Результаты поиска {search_type} по запросу: '{search_query}'**\n\n"
            "❌ Ничего не найдено.",
            reply_markup=builder.as_markup()
        )
        await state.clear()
        return

    # Формируем результаты
    if search_by_id:
        response = f"🆔 **Результаты поиска предложений по ID: '{search_query}'**\n\n"
    else:
        response = f"🔍 **Результаты поиска в предложениях: '{search_query}'**\n\n"

    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🤝 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого результата (первые 5)
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text="👁 Просмотр",
            callback_data=f"view_item_offer_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"➕ {title[:15]}",
            callback_data=f"add_to_cart_offer_{item_id}"
        ))

    builder.adjust(2)

    # Дополнительные кнопки
    if search_by_id:
        builder.row(types.InlineKeyboardButton(text="🆔 Новый поиск по ID", callback_data="search_offers_by_id"))
    else:
        builder.row(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_offers_by_name"))

    # builder.row(types.InlineKeyboardButton(text="🎯 Расширенный поиск", callback_data="advanced_search_offers"))
    if search_by_id:
        builder.row(types.InlineKeyboardButton(text="📋 Сохранить поиск",
                                               callback_data=f"save_search_id_offers_{search_query.replace(' ', '_')}"))
    else:
        builder.row(types.InlineKeyboardButton(text="📋 Сохранить поиск",
                                               callback_data=f"save_search_offers_{search_query.replace(' ', '_')}"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

    await message.answer(response, reply_markup=builder.as_markup())
    await state.clear()


# Остальной код остается без изменений...
# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def perform_search_in_catalog(search_query: str, item_type: str, user_id: int) -> list:
    """Выполнение поиска в конкретном каталоге по всем таблицам"""
    if not search_query:
        return []

    search_terms = search_query.lower().split()

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        if item_type == "product":
            # Поиск в auto_products
            cursor = await db.execute("""
                SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                FROM auto_products ap
                LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                WHERE ap.status = 'active'
                ORDER BY ap.created_at DESC
            """)
            auto_items = await cursor.fetchall()

            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, NULL as description
                FROM order_requests 
                WHERE item_type = 'product' AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """)
            order_items = await cursor.fetchall()

            # Объединяем все товары
            all_items = list(auto_items) + list(order_items)

        elif item_type == "service":
            # Поиск в auto_services
            cursor = await db.execute("""
                SELECT asv.id, asv.title, asv.price, ac.name as category, asv.operation_type, asv.description
                FROM auto_services asv
                LEFT JOIN auto_categories ac ON asv.category_id = ac.id
                WHERE asv.status = 'active'
                ORDER BY asv.created_at DESC
            """)
            auto_items = await cursor.fetchall()

            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, NULL as description
                FROM order_requests 
                WHERE item_type = 'service' AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """)
            order_items = await cursor.fetchall()

            # Объединяем все услуги
            all_items = list(auto_items) + list(order_items)

        else:  # offer
            # Для предложений только order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, NULL as description
                FROM order_requests 
                WHERE item_type = 'offer' AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """)
            all_items = await cursor.fetchall()

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


async def search_products_by_id(search_query: str, user_id: int) -> list:
    """Поиск товаров по ID в обеих таблицах"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        for item_id in id_list:
            try:
                item_id_int = int(item_id)

                # Ищем в auto_products
                cursor = await db.execute("""
                    SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                    FROM auto_products ap
                    LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                    WHERE ap.id = ? AND ap.status = 'active'
                """, (item_id_int,))

                item = await cursor.fetchone()
                if item:
                    results.append(item)
                else:
                    # Ищем в order_requests
                    cursor = await db.execute("""
                        SELECT id, title, price, category, operation, NULL as description
                        FROM order_requests 
                        WHERE item_type = 'product' AND id = ? AND status IN ('active', 'approved', 'processing')
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)

            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results


async def search_services_by_id(search_query: str, user_id: int) -> list:
    """Поиск услуг по ID в обеих таблицах"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        for item_id in id_list:
            try:
                item_id_int = int(item_id)

                # Ищем в auto_services
                cursor = await db.execute("""
                    SELECT asv.id, asv.title, asv.price, ac.name as category, asv.operation_type, asv.description
                    FROM auto_services asv
                    LEFT JOIN auto_categories ac ON asv.category_id = ac.id
                    WHERE asv.id = ? AND asv.status = 'active'
                """, (item_id_int,))

                item = await cursor.fetchone()
                if item:
                    results.append(item)
                else:
                    # Ищем в order_requests
                    cursor = await db.execute("""
                        SELECT id, title, price, category, operation, NULL as description
                        FROM order_requests 
                        WHERE item_type = 'service' AND id = ? AND status IN ('active', 'approved', 'processing')
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)

            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results


async def search_offers_by_id(search_query: str, user_id: int) -> list:
    """Поиск предложений по ID"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        for item_id in id_list:
            try:
                cursor = await db.execute("""
                    SELECT id, title, price, category, operation, NULL as description
                    FROM order_requests 
                    WHERE item_type = 'offer' AND id = ? AND status IN ('active', 'approved', 'processing')
                """, (int(item_id),))

                item = await cursor.fetchone()
                if item:
                    results.append(item)
            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results
# Поиск услуг по названию/тегам
@dp.callback_query(F.data == "search_services_by_name")
async def search_services_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Поиск услуг по названию или тегам"""
    await state.set_state(SearchStates.waiting_search_in_services)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            "🔍 **Поиск по названию или тегам**",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "🔍 **Поиск по названию или тегам**",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


# Поиск услуг по категории
@dp.callback_query(F.data == "search_services_by_category")
async def search_services_by_category_start(callback: CallbackQuery):
    """Поиск услуг по категории"""
    builder = InlineKeyboardBuilder()

    # Получаем категории из auto_services (через auto_categories)
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT ac.name 
            FROM auto_services asv
            JOIN auto_categories ac ON asv.category_id = ac.id
            WHERE asv.status = 'active' AND ac.type = 'service'
            ORDER BY ac.name
        """)
        categories = await cursor.fetchall()

        if not categories:
            # Если нет в auto_services, берем из order_requests
            cursor = await db.execute("""
                SELECT DISTINCT category FROM order_requests 
                WHERE item_type = 'service' AND category IS NOT NULL AND category != '' 
                AND category != 'None' AND status IN ('active', 'approved', 'processing')
                ORDER BY category
            """)
            categories = await cursor.fetchall()

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

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🏷 **Поиск по категории**\n\nВыберите категорию для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🏷 **Поиск по категории**\n\nВыберите категорию для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("serv_cat_search:"))
async def search_services_by_category_execute(callback: CallbackQuery):
    """Выполнение поиска услуг по категории"""
    category = callback.data.split(":")[1]

    user_id = callback.from_user.id

    # Выполняем поиск по категории в обеих таблицах
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Поиск в auto_services
        cursor = await db.execute("""
            SELECT asv.id, asv.title, asv.price, ac.name as category, asv.operation_type, asv.description
            FROM auto_services asv
            JOIN auto_categories ac ON asv.category_id = ac.id
            WHERE ac.name = ? AND asv.status = 'active' AND ac.type = 'service'
            ORDER BY asv.created_at DESC
        """, (category,))

        auto_services_results = await cursor.fetchall()

        # Поиск в order_requests
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'service' AND category = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (category,))

        order_requests_results = await cursor.fetchall()

        # Объединяем результаты
        results = list(auto_services_results) + list(order_requests_results)

        # Сохраняем в историю поиска
        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Категория: {category}", "category", "services", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(text="🏷 Выбрать другую категорию", callback_data="search_services_by_category"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
        builder.adjust(1)

        await callback.message.edit_text(
            f"🏷 **Результаты поиска по категории: '{category}'**\n\n"
            "❌ В этой категории ничего не найдено.\n\n"
            "Попробуйте выбрать другую категорию.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # Формируем результаты
    response = f"🏷 **Результаты поиска по категории: '{category}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🛠 **{title}**\n"
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
            callback_data=f"view_item_service_{item_id}"
        ))

    builder.adjust(1)

    # Дополнительные кнопки
    builder.row(
        types.InlineKeyboardButton(text="🏷 Выбрать другую категорию", callback_data="search_services_by_category"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))

    await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск услуг по классу
@dp.callback_query(F.data == "search_services_by_class")
async def search_services_by_class_start(callback: CallbackQuery):
    """Поиск услуг по классу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_classes ORDER BY name")
        items = await cursor.fetchall()

        if not items:
            # Получаем классы из auto_services (через service_classes)
            cursor = await db.execute("""
                SELECT DISTINCT sc.name 
                FROM auto_services asv
                JOIN service_classes sc ON asv.class_id = sc.id
                WHERE asv.status = 'active' AND asv.class_id IS NOT NULL
                ORDER BY sc.name
            """)
            items = await cursor.fetchall()

            if not items:
                # Если нет в auto_services, берем из order_requests
                cursor = await db.execute("""
                    SELECT DISTINCT item_class FROM order_requests 
                    WHERE item_type = 'service' AND item_class IS NOT NULL AND item_class != '' 
                    AND item_class != 'None' AND status IN ('active', 'approved', 'processing')
                    ORDER BY item_class
                """)
                items = await cursor.fetchall()

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

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            "📊 **Поиск по классу**\n\n"
            "Выберите класс для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "📊 **Поиск по классу**\n\n"
            "Выберите класс для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("serv_cls_search:"))
async def search_services_by_class_execute(callback: CallbackQuery):
    """Выполнение поиска услуг по классу"""
    item_class = callback.data.split(":")[1]

    user_id = callback.from_user.id

    # Выполняем поиск по классу в обеих таблицах
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Поиск в auto_services (через service_classes)
        cursor = await db.execute("""
            SELECT asv.id, asv.title, asv.price, ac.name as category, asv.operation_type, asv.description
            FROM auto_services asv
            JOIN service_classes sc ON asv.class_id = sc.id
            LEFT JOIN auto_categories ac ON asv.category_id = ac.id
            WHERE sc.name = ? AND asv.status = 'active'
            ORDER BY asv.created_at DESC
        """, (item_class,))

        auto_services_results = await cursor.fetchall()

        # Поиск в order_requests
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'service' AND item_class = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (item_class,))

        order_requests_results = await cursor.fetchall()

        # Объединяем результаты
        results = list(auto_services_results) + list(order_requests_results)

        # Сохраняем в историю поиска
        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Класс: {item_class}", "class", "services", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data="search_services_by_class"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
        builder.adjust(1)

        await callback.message.edit_text(
            f"📊 **Результаты поиска по классу: '{item_class}'**\n\n"
            "❌ В этом классе ничего не найдено.\n\n"
            "Попробуйте выбрать другой класс.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # Формируем результаты
    response = f"📊 **Результаты поиска по классу: '{item_class}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description = item

        response += f"{i}. 🛠 **{title}**\n"
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
            callback_data=f"view_item_service_{item_id}"
        ))

    builder.adjust(1)

    # Дополнительные кнопки
    builder.row(types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data="search_services_by_class"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))

    await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("all_orders_request_search"))
async def all_orders_request_search(callback: CallbackQuery):
    """Выполнение поиска услуг по классу"""


    user_id = callback.from_user.id

    # Выполняем поиск по классу в обеих таблицах
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:

        # Поиск в order_requests
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description, item_type
            FROM order_requests 
            ORDER BY created_at DESC
        """)

        order_requests_results = await cursor.fetchall()

        # Объединяем результаты
        results = list(order_requests_results)

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
        builder.adjust(1)

        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.edit_caption(
                caption=f"📊 **Результаты поиска:**\n\n❌ Заявок не найдено.\n\nПопробуйте позже.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                text=f"📊 **Результаты поиска:**\n\n❌ Заявок не найдено.\n\nПопробуйте позже.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return

    # Формируем результаты
    response = f"📊 **Результаты поиска:**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation, description, item_type = item

        response += f"{i}. 🛠 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        response += f"   📌 Тип: {item_type}\n"
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
        item_id, title, _, _, _, _, item_type = item
        builder.add(types.InlineKeyboardButton(
            text=f"{i}. {title[:15]}...",
            callback_data=f"view_item_{item_type}_{item_id}"
        ))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("all_orders_search"))
async def all_orders_search(callback: CallbackQuery):
    """Выполнение поиска услуг по классу"""


    user_id = callback.from_user.id

    # Выполняем поиск по классу в обеих таблицах
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:

        # Поиск в order_requests
        cursor = await db.execute("""
            SELECT id, order_type, item_id, seller_id, status, order_date
            FROM order 
            ORDER BY order_date DESC
        """)

        order_requests_results = await cursor.fetchall()

        # Объединяем результаты
        results = list(order_requests_results)

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
        builder.adjust(1)

        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.edit_caption(
                caption=f"📊 **Результаты поиска:**\n\n❌ Заявок не найдено.\n\nПопробуйте позже.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                text=f"📊 **Результаты поиска:**\n\n❌ Заявок не найдено.\n\nПопробуйте позже.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return

    # Формируем результаты
    response = f"📊 **Результаты поиска:**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        order_id, order_type, item_id, seller_id, status, order_date = item

        response += f"{i}.  **{order_type}**\n"
        response += f"   🆔 ID: {item_id} | 🏷  ID предмета: {item_id or 'Не указана'}\n"

        response += f"   💰 ID продавца: {seller_id}\n"

        response += f"   🎯 статус: {status}\n"

        response += f"   📝 Дата: {order_date}\n"

        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    # Создаем клавиатуру с результатами
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()
# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def perform_search_in_catalog(search_query: str, item_type: str, user_id: int) -> list:
    """Выполнение поиска в конкретном каталоге по всем таблицам"""
    if not search_query:
        return []

    search_terms = search_query.lower().split()

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        if item_type == "product":
            # Поиск в auto_products
            cursor = await db.execute("""
                SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                FROM auto_products ap
                LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                WHERE ap.status = 'active'
                ORDER BY ap.created_at DESC
            """)
            auto_items = await cursor.fetchall()

            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, NULL as description
                FROM order_requests 
                WHERE item_type = 'product' AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """)
            order_items = await cursor.fetchall()

            # Объединяем все товары
            all_items = list(auto_items) + list(order_items)

        elif item_type == "service":
            # Поиск в auto_services
            cursor = await db.execute("""
                SELECT asv.id, asv.title, asv.price, ac.name as category, asv.operation_type, asv.description
                FROM auto_services asv
                LEFT JOIN auto_categories ac ON asv.category_id = ac.id
                WHERE asv.status = 'active'
                ORDER BY asv.created_at DESC
            """)
            auto_items = await cursor.fetchall()

            # Поиск в order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, NULL as description
                FROM order_requests 
                WHERE item_type = 'service' AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """)
            order_items = await cursor.fetchall()

            # Объединяем все услуги
            all_items = list(auto_items) + list(order_items)

        else:  # offer
            # Для предложений только order_requests
            cursor = await db.execute("""
                SELECT id, title, price, category, operation, NULL as description
                FROM order_requests 
                WHERE item_type = 'offer' AND status IN ('active', 'approved', 'processing')
                ORDER BY created_at DESC
            """)
            all_items = await cursor.fetchall()

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


async def search_products_by_id(search_query: str, user_id: int) -> list:
    """Поиск товаров по ID в обеих таблицах"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        for item_id in id_list:
            try:
                item_id_int = int(item_id)

                # Ищем в auto_products
                cursor = await db.execute("""
                    SELECT ap.id, ap.title, ap.price, ac.name as category, ap.operation_type, ap.description
                    FROM auto_products ap
                    LEFT JOIN auto_categories ac ON ap.category_id = ac.id
                    WHERE ap.id = ? AND ap.status = 'active'
                """, (item_id_int,))

                item = await cursor.fetchone()
                if item:
                    results.append(item)
                else:
                    # Ищем в order_requests
                    cursor = await db.execute("""
                        SELECT id, title, price, category, operation, NULL as description
                        FROM order_requests 
                        WHERE item_type = 'product' AND id = ? AND status IN ('active', 'approved', 'processing')
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)

            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results


async def search_services_by_id(search_query: str, user_id: int) -> list:
    """Поиск услуг по ID в обеих таблицах"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        for item_id in id_list:
            try:
                item_id_int = int(item_id)

                # Ищем в auto_services
                cursor = await db.execute("""
                    SELECT asv.id, asv.title, asv.price, ac.name as category, asv.operation_type, asv.description
                    FROM auto_services asv
                    LEFT JOIN auto_categories ac ON asv.category_id = ac.id
                    WHERE asv.id = ? AND asv.status = 'active'
                """, (item_id_int,))

                item = await cursor.fetchone()
                if item:
                    results.append(item)
                else:
                    # Ищем в order_requests
                    cursor = await db.execute("""
                        SELECT id, title, price, category, operation, NULL as description
                        FROM order_requests 
                        WHERE item_type = 'service' AND id = ? AND status IN ('active', 'approved', 'processing')
                    """, (item_id_int,))

                    item = await cursor.fetchone()
                    if item:
                        results.append(item)

            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results


async def search_offers_by_id(search_query: str, user_id: int) -> list:
    """Поиск предложений по ID"""
    id_list = [id_str.strip() for id_str in search_query.split(',') if id_str.strip()]

    if not id_list:
        return []

    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        for item_id in id_list:
            try:
                cursor = await db.execute("""
                    SELECT id, title, price, category, operation, NULL as description
                    FROM order_requests 
                    WHERE item_type = 'offer' AND id = ? AND status IN ('active', 'approved', 'processing')
                """, (int(item_id),))

                item = await cursor.fetchone()
                if item:
                    results.append(item)
            except ValueError:
                continue  # Пропускаем нечисловые ID

    return results


async def perform_advanced_search_in_catalog(filters: dict, user_id: int) -> list:
    """Выполнение расширенного поиска в каталоге"""
    # Эта функция пока работает только с order_requests
    # Нужно будет адаптировать для работы с тремя таблицами
    where_conditions = ["status IN ('active', 'approved', 'processing')"]
    params = []

    # Применяем фильтры
    if filters.get("item_type"):
        where_conditions.append("item_type = ?")
        params.append(filters["item_type"])

    if filters.get("category"):
        where_conditions.append("category = ?")
        params.append(filters["category"])

    if filters.get("item_class"):
        where_conditions.append("item_class = ?")
        params.append(filters["item_class"])

    if filters.get("price_min") is not None:
        try:
            where_conditions.append("(price IS NOT NULL AND price != '' AND CAST(price AS REAL) >= ?)")
            params.append(float(filters["price_min"]))
        except:
            pass

    if filters.get("price_max") is not None:
        try:
            where_conditions.append("(price IS NOT NULL AND price != '' AND CAST(price AS REAL) <= ?)")
            params.append(float(filters["price_max"]))
        except:
            pass

    if filters.get("condition"):
        where_conditions.append("condition LIKE ?")
        params.append(f"%{filters['condition']}%")

    if filters.get("availability"):
        where_conditions.append("availability LIKE ?")
        params.append(f"%{filters['availability']}%")

    if filters.get("rating_min"):
        try:
            where_conditions.append("(rating IS NOT NULL AND rating != '' AND CAST(rating AS REAL) >= ?)")
            params.append(float(filters["rating_min"]))
        except:
            pass

    # Формируем SQL запрос
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute(f"""
            SELECT id, title, price, category, operation
            FROM order_requests 
            WHERE {where_clause}
            ORDER BY created_at DESC
        """, params)

        results = await cursor.fetchall()

    return results


async def show_current_filters_products(callback: CallbackQuery, state: FSMContext):
    """Показать текущие фильтры для товаров"""
    data = await state.get_data()
    filters = data.get("search_filters", {})

    response = "🎯 **Текущие фильтры поиска в товарах:**\n\n"

    if not filters or len(filters) <= 1:  # Только item_type
        response += "❌ Фильтры не заданы\n"
    else:
        for key, value in filters.items():
            if value and key != "item_type":
                key_name = {
                    "category": "🏷 Категория",
                    "item_class": "📊 Класс",
                    "price_min": "💰 Мин. цена",
                    "price_max": "💰 Макс. цена",
                    "condition": "🔄 Состояние",
                    "availability": "📦 Наличие",
                    "rating_min": "⭐ Мин. рейтинг"
                }.get(key, key)

                if key == "price_min" and "price_max" in filters and filters["price_max"]:
                    response += f"💰 Цена: {value} - {filters['price_max']} руб.\n"
                elif key == "price_min" and ("price_max" not in filters or not filters["price_max"]):
                    response += f"💰 Цена: от {value} руб.\n"
                elif key == "price_max" and "price_min" not in filters:
                    response += f"💰 Цена: до {value} руб.\n"
                elif key not in ["price_min", "price_max"]:
                    response += f"{key_name}: {value}\n"

    response += "\n──────\n\n"
    response += "Выберите следующий фильтр или выполните поиск:"

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🏷 Поиск по категории", callback_data="filter_category_products"))
    builder.add(types.InlineKeyboardButton(text="📊 Поиск по классу", callback_data="filter_class_products"))
    builder.add(types.InlineKeyboardButton(text="💰 Поиск по цене", callback_data="filter_price_products"))
    builder.add(types.InlineKeyboardButton(text="🔄 Поиск по состоянию", callback_data="filter_condition_products"))
    builder.add(types.InlineKeyboardButton(text="📦 Поиск по наличию", callback_data="filter_availability_products"))
    builder.add(types.InlineKeyboardButton(text="⭐ Поиск по рейтингу", callback_data="filter_rating_products"))
    builder.add(types.InlineKeyboardButton(text="🔍 Выполнить поиск", callback_data="execute_advanced_search_products"))
    builder.add(types.InlineKeyboardButton(text="🗑 Сбросить фильтры", callback_data="reset_filters_products"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(2)

    await callback.message.edit_text(response, reply_markup=builder.as_markup())


@dp.callback_query(F.data == "reset_filters_products")
async def reset_filters_products(callback: CallbackQuery, state: FSMContext):
    """Сброс всех фильтров для товаров"""
    await state.update_data(search_filters={"item_type": "product"})

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✅ Фильтры сброшены", callback_data="advanced_search_products"))
    builder.adjust(1)

    await callback.answer("✅ Все фильтры сброшены", show_alert=False)
    await callback.message.edit_text(
        "✅ Все фильтры поиска сброшены.\n\n"
        "Вы можете начать настройку фильтров заново.",
        reply_markup=builder.as_markup()
    )


# ========== ОБРАБОТЧИКИ ДЛЯ ПРОСМОТРА ТОВАРОВ ==========

@dp.callback_query(F.data.startswith("view_item_"))
async def view_search_result_item(callback: CallbackQuery):
    """Просмотр найденного товара/услуги/предложения"""
    if await check_blocked_user(callback):
        return

    # Fix for item_type containing underscores (e.g. cart_order)
    try:
        if not callback.data.startswith("view_item_"):
            raise ValueError("Invalid prefix")
            
        payload = callback.data[10:] # Remove 'view_item_'
        item_type, item_id = payload.rsplit("_", 1)
        
    except ValueError:
        await callback.answer("❌ Ошибка при загрузке товара", show_alert=True)
        return

    # Получаем информацию о товаре
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT 
                id, user_id, operation, item_type, category, item_class, item_kind,
                catalog_id, title, purpose, name, creation_date, condition,
                specifications, advantages, additional_info, images, price,
                availability, detailed_specs, reviews, rating, delivery_info,
                supplier_info, statistics, deadline, tags, contact, status, created_at
            FROM order_requests 
            WHERE id = ? AND item_type = ?
        """, (item_id, item_type))

        item = await cursor.fetchone()

    if not item:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    # Парсим изображения
    images_data = {}
    main_photo_id = None
    has_additional_photos = False
    
    if item[16]:
        try:
            images_data = json.loads(item[16])
            if images_data.get("main") and images_data["main"].get("file_id"):
                main_photo_id = images_data["main"]["file_id"]
            
            if images_data.get("additional") and len(images_data["additional"]) > 0:
                has_additional_photos = True
        except json.JSONDecodeError:
            pass

    # Формируем карточку
    response = ""

    if item_type == "product":
        response += "📦 **КАРТОЧКА ТОВАРА**\n\n"
    elif item_type == "service":
        response += "🛠 **КАРТОЧКА УСЛУГИ**\n\n"
    elif item_type == "cart_order":
        response += "🛒 **ЗАКАЗ ИЗ КОРЗИНЫ**\n\n"
    else:
        response += "🤝 **КАРТОЧКА ПРЕДЛОЖЕНИЯ**\n\n"

    # Основная информация
    response += f"🏷 **{item[8]}**\n"  # title
    response += f"🆔 ID в каталоге: {item[0]}\n"

    if item[5]:  # item_class
        response += f"📊 Класс: {item[5]}\n"
    if item[4]:  # category
        response += f"🏷 Категория: {item[4]}\n"
    if item[6]:  # item_kind
        response += f"👁 Вид: {item[6]}\n"

    # Операция
    if item[2]:  # operation
        response += f"🎯 Операция: {item[2]}\n"

    # Цена
    if item[16]:  # price (BUG: index 16 is images, price is 17! Waiting, let me check SQL query)
                  # SQL: ..., images, price, ... 
                  # images is index 16. price is index 17.
        # FIXING INDEXES BASED ON SQL QUERY:
        # 0: id, 1: user_id, 2: operation, 3: item_type, 4: category, 5: item_class, 6: item_kind
        # 7: catalog_id, 8: title, 9: purpose, 10: name, 11: creation_date, 12: condition
        # 13: specifications, 14: advantages, 15: additional_info, 16: images, 17: price
        # 18: availability, 19: detailed_specs, 20: reviews, 21: rating, 22: delivery_info
        # 23: supplier_info, 24: statistics, 25: deadline, 26: tags, 27: contact, 28: status, 29: created_at
        pass

    # Цена (index 17)
    if item[17]:
        response += f"💰 Цена: {item[17]}\n"

    # Наличие (index 18)
    if item[18]:
        response += f"📦 Наличие: {item[18]}\n"

    # Срок (index 25)
    if item[25]:
        response += f"⏰ Желательный срок: {item[25]}\n"

    # Теги (index 26)
    if item[26]:
        response += f"🏷 Теги: {item[26]}\n"

    # Контакты (index 27)
    if item[27]:
        response += f"📞 Контакты: {item[27]}\n"

    response += "\n──────\n\n"

    # Дополнительная информация (по мере заполнения)
    if item[9]:  # purpose
        response += f"📝 **Назначение:**\n{item[9]}\n\n"

    if item[13]:  # specifications
        response += f"⚙️ **Характеристики:**\n{item[13]}\n\n"

    if item[14]:  # advantages
        response += f"✅ **Преимущества:**\n{item[14]}\n\n"

    if item[12]:  # condition
        response += f"🔄 **Состояние:**\n{item[12]}\n\n"

    if item[19]:  # detailed_specs (index 19)
        response += f"📋 **Детальные характеристики:**\n{item[19]}\n\n"

    if item[20]:  # reviews
        response += f"💬 **Отзывы:**\n{item[20]}\n\n"

    if item[21]:  # rating
        response += f"⭐ **Рейтинг:** {item[21]}/10\n\n"

    if item[22]:  # delivery_info
        response += f"🚚 **Доставка и оплата:**\n{item[22]}\n\n"

    if item[23]:  # supplier_info
        response += f"🏢 **Поставщик:**\n{item[23]}\n\n"

    if item[15]:  # additional_info
        response += f"📄 **Дополнительная информация:**\n{item[15]}\n\n"

    # Статус (index 28)
    status_icon = "🆕" if item[28] == "new" else "📊" if item[28] == "processing" else "✅"
    response += f"{status_icon} **Статус:** {item[28]}\n"

    # Дата создания (index 29)
    try:
        date_str = datetime.fromisoformat(item[29]).strftime("%d.%m.%Y %H:%M")
        response += f"📅 **Дата создания:** {date_str}\n"
    except:
        pass

    # Кнопки действий
    builder = InlineKeyboardBuilder()

    # Основные действия
    if item[2] and "прода" in item[2].lower():
        builder.add(types.InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_item_{item_type}_{item_id}"))
    else:
        builder.add(types.InlineKeyboardButton(text="💰 Продать", callback_data=f"sell_item_{item_type}_{item_id}"))

    builder.add(types.InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_to_cart_{item_type}_{item_id}"))
    builder.add(types.InlineKeyboardButton(text="💬 Связаться", callback_data=f"contact_{item[1]}"))

    builder.adjust(2)

    # Admin Edit Button
    if callback.from_user.id == ADMIN_ID:
        builder.row(types.InlineKeyboardButton(text="✏️ Редактировать (Админ)", callback_data=f"edit_req_{item_type}_{item_id}"))

        # Approve/Reject buttons for Admin (if status is not final)
        if item[28] not in ['approved', 'rejected', 'completed', 'cancelled']:
             builder.row(
                 types.InlineKeyboardButton(text="✅ Одобрить/Завершить", callback_data=f"approve_req_{item_type}_{item_id}"),
                 types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_req_{item_type}_{item_id}")
             )

    # Дополнительные кнопки
    if has_additional_photos:
        builder.row(types.InlineKeyboardButton(text="📸 Галерея фото", callback_data=f"view_gallery_{item_type}_{item_id}"))

    builder.row(types.InlineKeyboardButton(text="📋 Подробнее", callback_data=f"item_details_{item_type}_{item_id}"))
    builder.row(types.InlineKeyboardButton(text="⭐ Оценить", callback_data=f"rate_item_{item_type}_{item_id}"))

    # Кнопка назад в зависимости от типа
    if item_type == "product":
        builder.row(types.InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="search_in_products"))
    elif item_type == "service":
        builder.row(types.InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="search_in_services"))
    else:
        builder.row(types.InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="search_in_offers"))

    # Отправка сообщения
    if main_photo_id:
        try:
            # Удаляем предыдущее сообщение (текстовое меню)
            await callback.message.delete()
            
            # Проверяем длину подписи
            if len(response) <= 1000:
                await callback.message.answer_photo(
                    photo=main_photo_id,
                    caption=response,
                    reply_markup=builder.as_markup()
                )
            else:
                # Если текст слишком длинный для подписи
                short_caption = f"🏷 **{item[8]}**\n💰 Цена: {item[17] or 'Не указана'}\n\n👇 Подробное описание ниже"
                await callback.message.answer_photo(
                    photo=main_photo_id,
                    caption=short_caption
                )
                await callback.message.answer(
                    text=response,
                    reply_markup=builder.as_markup()
                )
        except Exception as e:
            print(f"Error sending photo: {e}")
            # Fallback to text if photo fails
            await callback.message.answer(
                text=response,
                reply_markup=builder.as_markup()
            )
    else:
        # Если нет фото, редактируем текст (как было раньше)
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
        
    await callback.answer()


@dp.callback_query(F.data.startswith("view_gallery_"))
async def view_item_gallery(callback: CallbackQuery):
    """Просмотр галереи изображений"""
    if await check_blocked_user(callback):
        return

    data_parts = callback.data.split("_")
    if len(data_parts) < 4:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    item_type = data_parts[2]
    item_id = data_parts[3]

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("SELECT images FROM order_requests WHERE id = ? AND item_type = ?", (item_id, item_type))
        row = await cursor.fetchone()

    if not row or not row[0]:
        await callback.answer("❌ Фото не найдены", show_alert=True)
        return

    try:
        images_data = json.loads(row[0])
        additional_photos = images_data.get("additional", [])
        
        if not additional_photos:
            await callback.answer("❌ Дополнительных фото нет", show_alert=True)
            return

        media = []
        for photo in additional_photos:
            media.append(InputMediaPhoto(media=photo["file_id"]))

        await callback.message.answer_media_group(media=media)
        await callback.answer()
        
    except Exception as e:
        print(f"Error viewing gallery: {e}")
        await callback.answer("❌ Ошибка при открытии галереи", show_alert=True)


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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price FROM order_requests 
            WHERE id = ? AND item_type = ? AND status IN ('new', 'active', 'approved', 'processing')
        """, (item_id, item_type))

        item = await cursor.fetchone()

        if not item:
            await callback.answer("❌ Товар не найден или недоступен", show_alert=True)
            return

        # Проверяем, не добавлен ли уже в корзину
        cursor = await db.execute("""
            SELECT id FROM cart_order 
            WHERE user_id = ? AND item_type = 'order_request' AND item_id = ?
        """, (user_id, item_id))

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
            "order_request",
            item_id,
            1,
            "",
            item[2] or "0",
            datetime.now().isoformat()
        ))

        await db.commit()

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

# ==========================================
# ОБРАБОТЧИКИ ПОИСКА ТОВАРОВ
# ==========================================

# Поиск товаров по названию/тегам
@dp.callback_query(F.data == "search_products_by_name")
async def search_products_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Поиск товаров по названию или тегам"""
    await state.set_state(SearchStates.waiting_search_in_products)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🔍 **Поиск товаров по названию или тегам**\n\nВведите поисковый запрос:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🔍 **Поиск товаров по названию или тегам**\n\nВведите поисковый запрос:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()

# Поиск товаров по категории
@dp.callback_query(F.data == "search_products_by_category")
async def search_products_by_category_start(callback: CallbackQuery):
    """Поиск товаров по категории"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT category FROM order_requests 
            WHERE item_type = 'product' AND category IS NOT NULL AND category != '' 
            AND category != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY category
        """)
        categories = await cursor.fetchall()
        
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

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="🏷 **Поиск товаров по категории**\n\nВыберите категорию для поиска:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="🏷 **Поиск товаров по категории**\n\nВыберите категорию для поиска:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data.startswith("prod_cat_search:"))
async def search_products_by_category_execute(callback: CallbackQuery):
    """Выполнение поиска товаров по категории"""
    category = callback.data.split(":")[1]
    user_id = callback.from_user.id
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, category, NULL as operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'product' AND category = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (category,))
        results = await cursor.fetchall()

        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Категория: {category}", "category", "products", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🏷 Выбрать другую категорию", callback_data="search_products_by_category"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
        builder.adjust(1)
        
        text = f"🏷 **Результаты поиска товаров по категории: '{category}'**\n\n❌ В этой категории ничего не найдено.\n\nПопробуйте выбрать другую категорию."
        
        if callback.message.content_type == types.ContentType.PHOTO:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
        else:
             await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    response = f"🏷 **Результаты поиска товаров по категории: '{category}'**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, cat_name, op, desc = item
        response += f"{i}. 📦 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {cat_name or 'Не указана'}\n"
        if price and price != "0" and price is not None:
             response += f"   💰 Цена: {price}\n"
        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text=f"{i}. {title[:15]}...",
            callback_data=f"view_item_product_{item_id}"
        ))

    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="🏷 Выбрать другую категорию", callback_data="search_products_by_category"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
         await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск товаров по классу
@dp.callback_query(F.data == "search_products_by_class")
async def search_products_by_class_start(callback: CallbackQuery):
    """Поиск товаров по классу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_class FROM order_requests 
            WHERE item_type = 'product' AND item_class IS NOT NULL AND item_class != '' 
            AND item_class != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_class
        """)
        items = await cursor.fetchall()
        
        if items:
            for i in items:
                builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f"prod_cls_search:{i[0]}"))
        else:
            builder.add(types.InlineKeyboardButton(text="📭 Классы не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="📊 **Поиск товаров по классу**\n\nВыберите класс для поиска:", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text="📊 **Поиск товаров по классу**\n\nВыберите класс для поиска:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("prod_cls_search:"))
async def search_products_by_class_execute(callback: CallbackQuery):
    item_class = callback.data.split(":")[1]
    user_id = callback.from_user.id
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, category, NULL as operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'product' AND item_class = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (item_class,))
        results = await cursor.fetchall()

        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Класс: {item_class}", "class", "products", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data="search_products_by_class"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
        builder.adjust(1)
        
        text = f"📊 **Результаты поиска товаров по классу: '{item_class}'**\n\n❌ Ничего не найдено."
        if callback.message.content_type == types.ContentType.PHOTO:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
        else:
             await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
        await callback.answer()
        return
        
    response = f"📊 **Результаты поиска товаров по классу: '{item_class}'**\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        item_id, title, price, cat_name, _, _ = item
        response += f"{i}. 📦 **{title}**\n   🆔 ID: {item_id}\n"
        if price: response += f"   💰 Цена: {price}\n"
        response += "   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
        builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_product_{item[0]}"))
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="📊 Выбрать другой класс", callback_data="search_products_by_class"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
         await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск товаров по типу
@dp.callback_query(F.data == "search_products_by_type")
async def search_products_by_type_start(callback: CallbackQuery):
    """Поиск товаров по типу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_type_detail FROM order_requests 
            WHERE item_type = 'product' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
            AND item_type_detail != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_type_detail
        """)
        items = await cursor.fetchall()
        
        if items:
            for i in items:
                builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f"prod_type_search:{i[0]}"))
        else:
            builder.add(types.InlineKeyboardButton(text="📭 Типы не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="📋 **Поиск товаров по типу**\n\nВыберите тип для поиска:", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text="📋 **Поиск товаров по типу**\n\nВыберите тип для поиска:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("prod_type_search:"))
async def search_products_by_type_execute(callback: CallbackQuery):
    item_type = callback.data.split(":")[1]
    user_id = callback.from_user.id
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, category, NULL as operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'product' AND item_type_detail = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (item_type,))
        results = await cursor.fetchall()

        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Тип: {item_type}", "type", "products", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data="search_products_by_type"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
        builder.adjust(1)
        
        text = f"📋 **Результаты поиска товаров по типу: '{item_type}'**\n\n❌ Ничего не найдено."
        if callback.message.content_type == types.ContentType.PHOTO:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
        else:
             await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    response = f"📋 **Результаты поиска товаров по типу: '{item_type}'**\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        response += f"{i}. 📦 **{item[1]}**\n   🆔 ID: {item[0]}\n   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
        builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_product_{item[0]}"))
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data="search_products_by_type"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
         await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск товаров по виду
@dp.callback_query(F.data == "search_products_by_kind")
async def search_products_by_kind_start(callback: CallbackQuery):
    """Поиск товаров по виду"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_kind FROM order_requests 
            WHERE item_type = 'product' AND item_kind IS NOT NULL AND item_kind != '' 
            AND item_kind != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_kind
        """)
        items = await cursor.fetchall()
        
        if items:
            for i in items:
                builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f"prod_kind_search:{i[0]}"))
        else:
            builder.add(types.InlineKeyboardButton(text="📭 Виды не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="👁 **Поиск товаров по виду**\n\nВыберите вид для поиска:", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text="👁 **Поиск товаров по виду**\n\nВыберите вид для поиска:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("prod_kind_search:"))
async def search_products_by_kind_execute(callback: CallbackQuery):
    item_kind = callback.data.split(":")[1]
    user_id = callback.from_user.id
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, category, NULL as operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'product' AND item_kind = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (item_kind,))
        results = await cursor.fetchall()

        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Вид: {item_kind}", "kind", "products", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data="search_products_by_kind"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
        builder.adjust(1)
        
        text = f"👁 **Результаты поиска товаров по виду: '{item_kind}'**\n\n❌ Ничего не найдено."
        if callback.message.content_type == types.ContentType.PHOTO:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
        else:
             await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    response = f"👁 **Результаты поиска товаров по виду: '{item_kind}'**\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        response += f"{i}. 📦 **{item[1]}**\n   🆔 ID: {item[0]}\n   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
        builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_product_{item[0]}"))
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data="search_products_by_kind"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_products"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
         await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


# ==========================================
# ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ ПОИСКА УСЛУГ (ТИП/ВИД)
# ==========================================

# Поиск услуг по типу
@dp.callback_query(F.data == "search_services_by_type")
async def search_services_by_type_start(callback: CallbackQuery):
    """Поиск услуг по типу"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_type_detail FROM order_requests 
            WHERE item_type = 'service' AND item_type_detail IS NOT NULL AND item_type_detail != '' 
            AND item_type_detail != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_type_detail
        """)
        items = await cursor.fetchall()
        
        if items:
            for i in items:
                builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f"serv_type_search:{i[0]}"))
        else:
            builder.add(types.InlineKeyboardButton(text="📭 Типы не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="📋 **Поиск услуг по типу**\n\nВыберите тип для поиска:", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text="📋 **Поиск услуг по типу**\n\nВыберите тип для поиска:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("serv_type_search:"))
async def search_services_by_type_execute(callback: CallbackQuery):
    item_type = callback.data.split(":")[1]
    user_id = callback.from_user.id
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'service' AND item_type_detail = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (item_type,))
        results = await cursor.fetchall()

        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Тип: {item_type}", "type", "services", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data="search_services_by_type"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
        builder.adjust(1)
        
        text = f"📋 **Результаты поиска услуг по типу: '{item_type}'**\n\n❌ Ничего не найдено."
        if callback.message.content_type == types.ContentType.PHOTO:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
        else:
             await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    response = f"📋 **Результаты поиска услуг по типу: '{item_type}'**\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        response += f"{i}. 📦 **{item[1]}**\n   🆔 ID: {item[0]}\n   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
        builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_service_{item[0]}"))
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="📋 Выбрать другой тип", callback_data="search_services_by_type"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
         await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


# Поиск услуг по виду
@dp.callback_query(F.data == "search_services_by_kind")
async def search_services_by_kind_start(callback: CallbackQuery):
    """Поиск услуг по виду"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_kind FROM order_requests 
            WHERE item_type = 'service' AND item_kind IS NOT NULL AND item_kind != '' 
            AND item_kind != 'None' AND status IN ('active', 'approved', 'processing')
            ORDER BY item_kind
        """)
        items = await cursor.fetchall()
        
        if items:
            for i in items:
                builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f"serv_kind_search:{i[0]}"))
        else:
            builder.add(types.InlineKeyboardButton(text="📭 Виды не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="👁 **Поиск услуг по виду**\n\nВыберите вид для поиска:", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text="👁 **Поиск услуг по виду**\n\nВыберите вид для поиска:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("serv_kind_search:"))
async def search_services_by_kind_execute(callback: CallbackQuery):
    item_kind = callback.data.split(":")[1]
    user_id = callback.from_user.id
    results = []

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, NULL as description
            FROM order_requests 
            WHERE item_type = 'service' AND item_kind = ? AND status IN ('active', 'approved', 'processing')
            ORDER BY created_at DESC
        """, (item_kind,))
        results = await cursor.fetchall()

        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"Вид: {item_kind}", "kind", "services", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data="search_services_by_kind"))
        builder.add(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
        builder.adjust(1)
        
        text = f"👁 **Результаты поиска услуг по виду: '{item_kind}'**\n\n❌ Ничего не найдено."
        if callback.message.content_type == types.ContentType.PHOTO:
             await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
        else:
             await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    response = f"👁 **Результаты поиска услуг по виду: '{item_kind}'**\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        response += f"{i}. 📦 **{item[1]}**\n   🆔 ID: {item[0]}\n   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
        builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_service_{item[0]}"))
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="👁 Выбрать другой вид", callback_data="search_services_by_kind"))
    builder.row(types.InlineKeyboardButton(text="🔍 Другой тип поиска", callback_data="search_in_services"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
         await callback.message.edit_caption(caption=response, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_text(text=response, reply_markup=builder.as_markup())
    await callback.answer()


# ==========================================
# ОБРАБОТЧИКИ ПОИСКА ПО ID И СООБЩЕНИЙ
# ==========================================

# Поиск товаров по ID
@dp.callback_query(F.data == "search_products_by_id")
async def search_products_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Поиск товаров по ID"""
    await state.set_state(SearchStates.waiting_search_in_products)
    # Можно установить флаг, если нужна специфическая логика, но поиск общий тоже сработает
    await state.update_data(search_by_id=True)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_products"))
    builder.adjust(1)
    
    msg = "🆔 **Поиск товаров по ID**\n\nВведите ID товара:"
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=msg, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=msg, reply_markup=builder.as_markup())
    await callback.answer()

# Поиск услуг по ID
@dp.callback_query(F.data == "search_services_by_id")
async def search_services_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Поиск услуг по ID"""
    await state.set_state(SearchStates.waiting_search_in_services)
    await state.update_data(search_by_id=True)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_services"))
    builder.adjust(1)
    
    msg = "🆔 **Поиск услуг по ID**\n\nВведите ID услуги:"
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=msg, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=msg, reply_markup=builder.as_markup())
    await callback.answer()

# Обработка ввода поискового запроса для товаров
@dp.message(SearchStates.waiting_search_in_products)
async def process_search_in_products(message: Message, state: FSMContext):
    search_query = message.text.strip()
    if not search_query:
        await message.answer("❌ Введите поисковый запрос!")
        return

    results = await perform_search_in_catalog(search_query, "product", message.from_user.id)
    
    # Сохраняем в историю
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, search_query, "text", "products", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔍 Попробовать снова", callback_data="search_in_products"))
        builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))
        builder.adjust(1)
        await message.answer(f"📦 **Результаты поиска:** '{search_query}'\n\n❌ Ничего не найдено.", reply_markup=builder.as_markup())
        return

    response = f"📦 **Результаты поиска:** '{search_query}'\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        # perform_search_in_catalog returns tuples: id, title, price, category, op, desc
        item_id, title, price, category, op, desc = item
        response += f"{i}. 📦 **{title}**\n   🆔 ID: {item_id}\n"
        if price: response += f"   💰 Цена: {price}\n"
        if category: response += f"   🏷 Кат: {category}\n"
        response += "   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
         builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_product_{item[0]}"))
    
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_in_products"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="product_catalog"))
    
    await message.answer(response, reply_markup=builder.as_markup())
    # await state.clear() # Не очищаем, чтобы можно было искать дальше? Обычно очищают или нет?
    # Если не очистить, следующее сообщение тоже будет поиском.
    # User might want to search again immediately.
    # But usually bots clear state after success unless conversational.
    # Given the "New Search" button, clearing state is safer to avoid accidental text capture.
    # But current implementation in offers didn't show strict clear.
    # I'll clear state to be safe.
    await state.clear()


# Обработка ввода поискового запроса для услуг
@dp.message(SearchStates.waiting_search_in_services)
async def process_search_in_services(message: Message, state: FSMContext):
    search_query = message.text.strip()
    if not search_query:
        await message.answer("❌ Введите поисковый запрос!")
        return

    results = await perform_search_in_catalog(search_query, "service", message.from_user.id)
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        await db.execute(
            "INSERT INTO search_history (user_id, search_query, search_type, catalog_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, search_query, "text", "services", datetime.now().isoformat())
        )
        await db.commit()

    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔍 Попробовать снова", callback_data="search_in_services"))
        builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))
        builder.adjust(1)
        await message.answer(f"🛠 **Результаты поиска:** '{search_query}'\n\n❌ Ничего не найдено.", reply_markup=builder.as_markup())
        return

    response = f"🛠 **Результаты поиска:** '{search_query}'\n\n📊 Найдено: {len(results)} позиций\n\n"
    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, op, desc = item
        response += f"{i}. 🛠 **{title}**\n   🆔 ID: {item_id}\n"
        if price: response += f"   💰 Цена: {price}\n"
        if category: response += f"   🏷 Кат: {category}\n"
        response += "   ──────\n"

    builder = InlineKeyboardBuilder()
    for i, item in enumerate(results[:5], 1):
         builder.add(types.InlineKeyboardButton(text=f"{i}. {item[1][:15]}...", callback_data=f"view_item_service_{item[0]}"))
    
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_in_services"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="service_catalog"))
    
    await message.answer(response, reply_markup=builder.as_markup())
    await state.clear()

# Инициализация таблицы истории поиска
async def init_search_history_table():
    """Инициализация таблицы истории поиска"""
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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



# ==========================================
# РАСШИРЕННЫЙ ПОИСК ПРЕДЛОЖЕНИЙ
# ==========================================

@dp.callback_query(F.data == "advanced_search_offers")
async def advanced_search_offers_start(callback: CallbackQuery, state: FSMContext):
    """Start advanced search for offers"""
    await state.set_state(SearchStates.advanced_search_menu)
    
    # Initialize filters if not present
    data = await state.get_data()
    if "search_filters" not in data or data.get("search_filters", {}).get("item_type") != "offer":
        await state.update_data(search_filters={"item_type": "offer"})
    
    await show_current_filters_offers(callback, state)

async def show_current_filters_offers(callback: CallbackQuery, state: FSMContext):
    """Show current filters for offers"""
    data = await state.get_data()
    filters = data.get("search_filters", {})

    response = "🎯 **Текущие фильтры поиска в предложениях:**\n\n"

    if not filters or len(filters) <= 1:  # Only item_type
        response += "❌ Фильтры не заданы\n"
    else:
        for key, value in filters.items():
            if value and key != "item_type":
                key_name = {
                    "category": "🏷 Категория",
                    "item_class": "📊 Класс",
                    "item_type_detail": "📋 Тип",
                    "item_kind": "👁 Вид",
                    "price_min": "💰 Мин. цена",
                    "price_max": "💰 Макс. цена",
                    "condition": "🔄 Состояние",
                    "availability": "📦 Наличие",
                    "rating_min": "⭐ Мин. рейтинг"
                }.get(key, key)

                if key == "price_min" and "price_max" in filters and filters["price_max"]:
                    response += f"💰 Цена: {value} - {filters['price_max']} руб.\n"
                elif key == "price_min" and ("price_max" not in filters or not filters["price_max"]):
                    response += f"💰 Цена: от {value} руб.\n"
                elif key == "price_max" and "price_min" not in filters:
                    response += f"💰 Цена: до {value} руб.\n"
                elif key not in ["price_min", "price_max"]:
                    response += f"{key_name}: {value}\n"

    response += "\n──────\n\n"
    response += "Выберите следующий фильтр или выполните поиск:"

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🏷 Поиск по категории", callback_data="filter_category_offers"))
    builder.add(types.InlineKeyboardButton(text="📊 Поиск по классу", callback_data="filter_class_offers"))
    # builder.add(types.InlineKeyboardButton(text="📋 Поиск по типу", callback_data="filter_type_offers")) # Optional, if needed
    # builder.add(types.InlineKeyboardButton(text="👁 Поиск по виду", callback_data="filter_kind_offers")) # Optional, if needed
    builder.add(types.InlineKeyboardButton(text="💰 Поиск по цене", callback_data="filter_price_offers"))
    builder.add(types.InlineKeyboardButton(text="🔍 Выполнить поиск", callback_data="execute_advanced_search_offers"))
    builder.add(types.InlineKeyboardButton(text="🗑 Сбросить фильтры", callback_data="reset_filters_offers"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="search_in_offers"))
    builder.adjust(2)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "reset_filters_offers")
async def reset_filters_offers(callback: CallbackQuery, state: FSMContext):
    """Reset all filters for offers"""
    await state.update_data(search_filters={"item_type": "offer"})
    
    await callback.answer("✅ Все фильтры сброшены", show_alert=False)
    await show_current_filters_offers(callback, state)


@dp.callback_query(F.data == "execute_advanced_search_offers")
async def execute_advanced_search_offers(callback: CallbackQuery, state: FSMContext):
    """Execute advanced search for offers"""
    data = await state.get_data()
    filters = data.get("search_filters", {})
    user_id = callback.from_user.id
    
    results = await perform_advanced_search_in_catalog(filters, user_id)
    
    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔙 К фильтрам", callback_data="advanced_search_offers"))
        builder.add(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))
        
        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.delete()
            await callback.message.answer(
                "🔍 **Результаты расширенного поиска**\n\n"
                "❌ Ничего не найдено по заданным фильтрам.\n"
                "Попробуйте изменить параметры поиска.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                "🔍 **Результаты расширенного поиска**\n\n"
                "❌ Ничего не найдено по заданным фильтрам.\n"
                "Попробуйте изменить параметры поиска.",
                reply_markup=builder.as_markup()
            )
        return

    # Form results
    response = "🔍 **Результаты расширенного поиска в предложениях:**\n\n"
    response += f"📊 Найдено: {len(results)} позиций\n\n"

    for i, item in enumerate(results[:10], 1):
        item_id, title, price, category, operation = item
        
        response += f"{i}. 🤝 **{title}**\n"
        response += f"   🆔 ID: {item_id} | 🏷 Категория: {category or 'Не указана'}\n"
        if price and price != "0" and price is not None:
            response += f"   💰 Цена: {price}\n"
        if operation:
            response += f"   🎯 Операция: {operation}\n"
        
        response += "   ──────\n"

    if len(results) > 10:
        response += f"\n📄 Показано 10 из {len(results)} результатов\n"

    builder = InlineKeyboardBuilder()
    
    # Results buttons
    for i, item in enumerate(results[:5], 1):
        item_id, title, _, _, _ = item
        builder.add(types.InlineKeyboardButton(
            text="👁 Просмотр",
            callback_data=f"view_item_offer_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"➕ {title[:15]}",
            callback_data=f"add_to_cart_offer_{item_id}"
        ))
        
    builder.adjust(2)
    
    builder.row(types.InlineKeyboardButton(text="🔙 К фильтрам", callback_data="advanced_search_offers"))
    builder.row(types.InlineKeyboardButton(text="◀️ В каталог", callback_data="property_catalog"))

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
        
# ==========================================
# ОБРАБОТЧИКИ ФИЛЬТРОВ ДЛЯ ПРЕДЛОЖЕНИЙ
# ==========================================

@dp.callback_query(F.data == "filter_category_offers")
async def filter_category_offers(callback: CallbackQuery, state: FSMContext):
    """Filter by category for offers"""
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT category FROM order_requests 
            WHERE item_type = 'offer' AND category IS NOT NULL AND category != '' 
            AND status IN ('active', 'approved', 'processing')
            ORDER BY category
        """)
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()
    if items:
        for item in items:
            cat_name = item[0]
            cat_hash = hashlib.md5(cat_name.encode()).hexdigest()
            builder.add(types.InlineKeyboardButton(text=cat_name, callback_data=f"fco:{cat_hash}"))
    else:
        builder.add(types.InlineKeyboardButton(text="📭 Категории не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="advanced_search_offers"))
    builder.adjust(1)
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer("🏷 **Выберите категорию для фильтрации:**", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text("🏷 **Выберите категорию для фильтрации:**", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("fco:"))
async def set_filter_category_offers(callback: CallbackQuery, state: FSMContext):
    """Set category filter for offers"""
    cat_hash = callback.data.split(":")[1]
    category = None
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT category FROM order_requests 
            WHERE item_type = 'offer' AND category IS NOT NULL AND category != '' 
            AND status IN ('active', 'approved', 'processing')
        """)
        items = await cursor.fetchall()
        for item in items:
            if hashlib.md5(item[0].encode()).hexdigest() == cat_hash:
                category = item[0]
                break
    
    if category:
        data = await state.get_data()
        filters = data.get("search_filters", {})
        filters["category"] = category
        await state.update_data(search_filters=filters)
        await show_current_filters_offers(callback, state)
    else:
        await callback.answer("❌ Категория не найдена", show_alert=True)


@dp.callback_query(F.data == "filter_class_offers")
async def filter_class_offers(callback: CallbackQuery, state: FSMContext):
    """Filter by class for offers"""
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_class FROM order_requests 
            WHERE item_type = 'offer' AND item_class IS NOT NULL AND item_class != '' 
            AND status IN ('active', 'approved', 'processing')
            ORDER BY item_class
        """)
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()
    if items:
        for item in items:
            class_name = item[0]
            cls_hash = hashlib.md5(class_name.encode()).hexdigest()
            builder.add(types.InlineKeyboardButton(text=class_name, callback_data=f"fclo:{cls_hash}"))
    else:
        builder.add(types.InlineKeyboardButton(text="📭 Классы не найдены", callback_data="no_action"))

    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="advanced_search_offers"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer("📊 **Выберите класс для фильтрации:**", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text("📊 **Выберите класс для фильтрации:**", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("fclo:"))
async def set_filter_class_offers(callback: CallbackQuery, state: FSMContext):
    """Set class filter for offers"""
    cls_hash = callback.data.split(":")[1]
    item_class = None
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT DISTINCT item_class FROM order_requests 
            WHERE item_type = 'offer' AND item_class IS NOT NULL AND item_class != '' 
            AND status IN ('active', 'approved', 'processing')
        """)
        items = await cursor.fetchall()
        for item in items:
            if hashlib.md5(item[0].encode()).hexdigest() == cls_hash:
                item_class = item[0]
                break
    
    if item_class:
        data = await state.get_data()
        filters = data.get("search_filters", {})
        filters["item_class"] = item_class
        await state.update_data(search_filters=filters)
        await show_current_filters_offers(callback, state)
    else:
        await callback.answer("❌ Класс не найден", show_alert=True)


@dp.callback_query(F.data == "filter_price_offers")
async def filter_price_offers(callback: CallbackQuery, state: FSMContext):
    """Filter by price for offers"""
    await state.set_state(SearchStates.waiting_filter_price)
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Отмена", callback_data="advanced_search_offers"))
    builder.adjust(1)
    
    msg = "💰 **Фильтр по цене**\n\nВведите диапазон цен в формате `мин-макс` (например, `1000-5000`) или просто одно число для минимальной цены."
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(msg, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(msg, reply_markup=builder.as_markup())
    await callback.answer()


@dp.message(SearchStates.waiting_filter_price)
async def process_filter_price_input(message: Message, state: FSMContext):
    """Process price filter input"""
    text = message.text.strip().replace(" ", "")
    
    price_min = None
    price_max = None
    
    try:
        if "-" in text:
            parts = text.split("-")
            price_min = float(parts[0])
            price_max = float(parts[1])
        else:
            price_min = float(text)
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число или диапазон (например, 1000-5000).")
        return

    data = await state.get_data()
    filters = data.get("search_filters", {})
    
    if price_min is not None:
        filters["price_min"] = price_min
    if price_max is not None:
        filters["price_max"] = price_max
        
    await state.update_data(search_filters=filters)
    await state.set_state(SearchStates.advanced_search_menu)
    
    response = "🎯 **Текущие фильтры обновлены.**\nВыберите следующее действие:"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 К фильтрам", callback_data="advanced_search_offers"))
    builder.add(types.InlineKeyboardButton(text="🔍 Выполнить поиск", callback_data="execute_advanced_search_offers"))
    builder.adjust(1)
    
    await message.answer(response, reply_markup=builder.as_markup())


# Экспорт функции для добавления кнопки поиска
def get_search_system_handlers():
    """Получить обработчики системы поиска"""
    return dp