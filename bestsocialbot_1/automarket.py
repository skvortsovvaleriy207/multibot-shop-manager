from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
import json
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user

class AutoMarketStates(StatesGroup):
    ADD_PRODUCT_CATEGORY = State()
    ADD_PRODUCT_TITLE = State()
    ADD_PRODUCT_DESCRIPTION = State()
    ADD_PRODUCT_PRICE = State()
    ADD_PRODUCT_SPECS = State()
    ADD_PRODUCT_CONTACT = State()
    ADD_PRODUCT_DELIVERY = State()
    ADD_PRODUCT_WARRANTY = State()
    ADD_PRODUCT_IMAGES = State()
    
    ADD_SERVICE_CATEGORY = State()
    ADD_SERVICE_TITLE = State()
    ADD_SERVICE_DESCRIPTION = State()
    ADD_SERVICE_PRICE = State()
    ADD_SERVICE_DURATION = State()
    ADD_SERVICE_LOCATION = State()
    ADD_SERVICE_CONTACT = State()
    ADD_SERVICE_IMAGES = State()

# Каталог товаров
@dp.callback_query(F.data == "products")
async def products_catalog(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT ap.id, ap.title, ap.price, u.username
            FROM auto_products ap
            JOIN users u ON ap.user_id = u.user_id
            WHERE ap.status = 'active'
            ORDER BY ap.created_at DESC
            LIMIT 20
        """)
        items = await cursor.fetchall()
    
    builder = InlineKeyboardBuilder()
    
    if items:
        for item_id, title, price, username in items:
            price_text = f"{price}₽" if price else "Цена не указана"
            button_text = f"{title[:30]}... - {price_text}"
            builder.add(types.InlineKeyboardButton(text=button_text, callback_data=f"item_tech_{item_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет товаров", callback_data="empty"))
    
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data="search_products"))
    builder.add(types.InlineKeyboardButton(text="💰 Фильтр по цене", callback_data="filter_price_products"))
    builder.add(types.InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_from_products"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
    builder.adjust(*[1]*len(items[:20]), 2, 1, 2, 1)
    
    text = "📦 **Каталог товаров**\n\n"
    if items:
        text += f"Найдено товаров: {len(items)}\n\nВыберите интересующий вариант:"
    else:
        text += "Пока нет товаров."
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
    await callback.answer()

# Каталог услуг
@dp.callback_query(F.data == "services")
async def services_catalog(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT as_.id, as_.title, as_.price, u.username
            FROM auto_services as_
            JOIN users u ON as_.user_id = u.user_id
            WHERE as_.status = 'active'
            ORDER BY as_.created_at DESC
            LIMIT 20
        """)
        items = await cursor.fetchall()
    
    builder = InlineKeyboardBuilder()
    
    if items:
        for item_id, title, price, username in items:
            price_text = f"{price}₽" if price else "Цена не указана"
            button_text = f"{title[:30]}... - {price_text}"
            builder.add(types.InlineKeyboardButton(text=button_text, callback_data=f"item_service_{item_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет услуг", callback_data="empty"))
    
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data="search_services"))
    builder.add(types.InlineKeyboardButton(text="💰 Фильтр по цене", callback_data="filter_price_services"))
    builder.add(types.InlineKeyboardButton(text="➕ Добавить услугу", callback_data="add_service"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_from_services"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
    builder.adjust(*[1]*len(items[:20]), 2, 1, 2, 1)
    
    text = "🛠 **Каталог услуг**\n\n"
    if items:
        text += f"Найдено услуг: {len(items)}\n\nВыберите интересующий вариант:"
    else:
        text += "Пока нет услуг."
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
    await callback.answer()



# Просмотр карточки товара/услуги - ОТКЛЮЧЕНО, используется catalog.py
# @dp.callback_query(F.data.startswith("item_"))
async def view_item_DISABLED(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    item_type = parts[1]  # 'tech' или 'service'
    item_id = int(parts[2])
    
    async with aiosqlite.connect("bot_database.db") as db:
        if item_type == 'tech':
            cursor = await db.execute("""
                SELECT ap.*, u.username, u.phone, ac.name as category_name
                FROM auto_products ap 
                JOIN users u ON ap.user_id = u.user_id 
                JOIN auto_categories ac ON ap.category_id = ac.id
                WHERE ap.id = ?
            """, (item_id,))
        else:
            cursor = await db.execute("""
                SELECT as_.*, u.username, u.phone, ac.name as category_name
                FROM auto_services as_ 
                JOIN users u ON as_.user_id = u.user_id 
                JOIN auto_categories ac ON as_.category_id = ac.id
                WHERE as_.id = ?
            """, (item_id,))
        
        item = await cursor.fetchone()
    
    if not item:
        await callback.answer("Предложение не найдено", show_alert=True)
        return
    
    # Формируем текст карточки
    if item_type == 'tech':
        text = f"🚗 **{item[3]}**\n\n"  # title
        text += f"📂 Категория: {item[-1]}\n"  # category_name
        text += f"💰 Цена: {item[5]}₽\n" if item[5] else "💰 Цена: не указана\n"
        text += f"📝 Описание: {item[4]}\n\n" if item[4] else ""
        
        # Характеристики
        if item[7]:  # specifications
            try:
                specs = json.loads(item[7])
                text += "🔧 **Характеристики:**\n"
                for key, value in specs.items():
                    text += f"• {key}: {value}\n"
                text += "\n"
            except:
                pass
    else:
        text = f"🛠 **{item[3]}**\n\n"  # title
        text += f"📂 Категория: {item[-1]}\n"  # category_name
        text += f"💰 Цена: {item[5]}₽\n" if item[5] else "💰 Цена: не указана\n"
        text += f"📍 Местоположение: {item[6]}\n" if item[6] else ""
        text += f"📞 Контакты: {item[7]}\n" if item[7] else ""
        text += f"📝 Описание: {item[4]}\n\n" if item[4] else ""
    
    text += f"👤 Продавец: @{item[-3]}\n"  # username
    text += f"📱 Телефон: {item[-2]}" if item[-2] else ""
    
    builder = InlineKeyboardBuilder()
    
    # Проверяем, не свой ли это товар
    if item[1] != callback.from_user.id:  # user_id
        builder.add(types.InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_cart_{item_type}_{item_id}"))
        builder.add(types.InlineKeyboardButton(text="📞 Связаться", callback_data=f"contact_{item[1]}"))
        builder.add(types.InlineKeyboardButton(text="📝 Отзывы", callback_data=f"view_reviews_{item_type}_{item_id}"))
    else:
        builder.add(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{item_type}_{item_id}"))
        builder.add(types.InlineKeyboardButton(text="📝 Отзывы", callback_data=f"view_reviews_{item_type}_{item_id}"))
    
    # Кнопка назад к каталогу
    if item_type == 'tech':
        builder.add(types.InlineKeyboardButton(text="◀️ К товарам", callback_data="products"))
    else:
        builder.add(types.InlineKeyboardButton(text="◀️ К услугам", callback_data="services"))
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Добавление в корзину
@dp.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    item_type = parts[2]
    item_id = int(parts[3])
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        # Проверяем, нет ли уже в корзине
        cursor = await db.execute(
            "SELECT id FROM cart WHERE user_id = ? AND item_type = ? AND item_id = ?",
            (user_id, item_type, item_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            await callback.answer("Товар уже в корзине!", show_alert=True)
            return
        
        # Добавляем в корзину
        await db.execute(
            "INSERT INTO cart (user_id, item_type, item_id, added_at) VALUES (?, ?, ?, ?)",
            (user_id, item_type, item_id, datetime.now().isoformat())
        )
        await db.commit()
    
    await callback.answer("✅ Добавлено в корзину!")

# Корзина
@dp.callback_query(F.data.contains("cart"))
async def view_cart(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    # Определяем источник перехода для кнопки Назад
    source = "shop"
    if "from_products" in callback.data:
        source = "products"
    elif "from_services" in callback.data:
        source = "services" 
    elif "from_account" in callback.data:
        source = "account"
    # Для remove_cart и других действий сохраняем источник
    elif "_products" in callback.data:
        source = "products"
    elif "_services" in callback.data:
        source = "services"
    elif "_account" in callback.data:
        source = "account"

    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT c.id, c.item_type, c.item_id, c.added_at,
                   CASE 
                       WHEN c.item_type = 'tech' THEN ap.title
                       ELSE as_.title
                   END as title,
                   CASE 
                       WHEN c.item_type = 'tech' THEN ap.price
                       ELSE as_.price
                   END as price
            FROM cart c
            LEFT JOIN auto_products ap ON c.item_type = 'tech' AND c.item_id = ap.id
            LEFT JOIN auto_services as_ ON c.item_type = 'service' AND c.item_id = as_.id
            WHERE c.user_id = ?
            ORDER BY c.added_at DESC
        """, (user_id,))
        
        cart_items = await cursor.fetchall()
    
    # Определяем callback для кнопки Назад
    back_callback = "main_shop_page"
    if source == "products":
        back_callback = "products"
    elif source == "services":
        back_callback = "services"
    elif source == "account":
        back_callback = "personal_account"

    if not cart_items:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📦 К товарам", callback_data="products"))
        builder.add(types.InlineKeyboardButton(text="🛠 К услугам", callback_data="services"))
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback))
        builder.adjust(2, 1)
        
        if callback.message.content_type == types.ContentType.PHOTO:
            await callback.message.edit_caption(
                caption="🛒 **Ваша корзина пуста**\n\nДобавьте товары или услуги из каталога.",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(
                text="🛒 **Ваша корзина пуста**\n\nДобавьте товары или услуги из каталога.",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
        return
    
    text = "🛒 **Ваша корзина**\n\n"
    total_price = 0
    
    builder = InlineKeyboardBuilder()
    
    for cart_id, item_type, item_id, added_at, title, price in cart_items:
        icon = "🚗" if item_type == 'tech' else "🛠"
        price_text = f"{price}₽" if price else "Цена не указана"
        text += f"{icon} {title}\n💰 {price_text}\n\n"
        
        if price:
            total_price += price
        
        # Кнопки для каждого товара
        builder.add(types.InlineKeyboardButton(
            text=f"👁 {title[:20]}...", 
            callback_data=f"item_{item_type}_{item_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text="🗑", 
            callback_data=f"remove_cart_{cart_id}_{source}"
        ))
    
    text += f"💰 **Общая сумма: {total_price}₽**" if total_price > 0 else ""
    
    # Кнопки управления корзиной
    builder.add(types.InlineKeyboardButton(text="📋 Оформить заказы", callback_data="checkout"))
    builder.add(types.InlineKeyboardButton(text="🗑 Очистить корзину", callback_data=f"clear_cart_{source}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback))
    
    builder.adjust(2)  # По 2 кнопки в ряд для товаров
    builder.adjust(*[2] * (len(cart_items)), 1, 2, 1)  # Последние кнопки отдельно
    
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass

# Удаление из корзины
@dp.callback_query(F.data.startswith("remove_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    cart_id = int(parts[2])
    # Пытаемся получить источник если он есть
    source = "shop"
    if len(parts) > 3:
        source = parts[3]
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        await db.commit()
    
    await callback.answer("🗑 Удалено из корзины")
    
    # Модифицируем callback.data чтобы view_cart распознал источник
    # Мы не можем изменить callback.data напрямую, но можем вызвать функцию
    # Создаем фейковый или просто вызываем с нужным контекстом?
    # Проще просто вызвать view_cart, но view_cart читает callback.data
    # Поэтому передадим источник через подмену callback.data (это хак, но работает в рамках объекта)
    
    original_data = callback.data
    callback.data = f"cart_from_{source}" # Подменяем для view_cart
    await view_cart(callback)
    callback.data = original_data # Возвращаем на всякий случай

# Очистка корзины
@dp.callback_query(F.data.startswith("clear_cart"))
async def clear_cart(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    # Получаем источник
    source = "shop"
    if "_products" in callback.data:
        source = "products"
    elif "_services" in callback.data:
        source = "services"
    elif "_account" in callback.data:
        source = "account"
        
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()
    
    await callback.answer("🗑 Корзина очищена")
    
    # Подменяем callback.data для правильного возврата
    original_data = callback.data
    callback.data = f"cart_from_{source}"
    await view_cart(callback)
    callback.data = original_data

# Оформление заказов
@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        # Получаем товары из корзины
        cursor = await db.execute("""
            SELECT c.item_type, c.item_id,
                   CASE 
                       WHEN c.item_type = 'tech' THEN ap.user_id
                       ELSE as_.user_id
                   END as seller_id
            FROM cart c
            LEFT JOIN auto_products ap ON c.item_type = 'tech' AND c.item_id = ap.id
            LEFT JOIN auto_services as_ ON c.item_type = 'service' AND c.item_id = as_.id
            WHERE c.user_id = ?
        """, (user_id,))
        
        cart_items = await cursor.fetchall()
        
        if not cart_items:
            await callback.answer("Корзина пуста!", show_alert=True)
            return
        
        # Создаем заказы
        order_count = 0
        for item_type, item_id, seller_id in cart_items:
            await db.execute("""
                INSERT INTO orders (user_id, order_type, item_id, seller_id, status, order_date)
                VALUES (?, ?, ?, ?, 'new', ?)
            """, (user_id, item_type, item_id, seller_id, datetime.now().isoformat()))
            order_count += 1
        
        # Очищаем корзину
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders"))
    builder.add(types.InlineKeyboardButton(text="◀️ В магазин", callback_data="main_shop_page"))
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"✅ **Заказы оформлены!**\n\n"
        f"Создано заказов: {order_count}\n"
        f"Статус: Новая заявка\n\n"
        f"Продавцы получат уведомления о ваших заказах.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()