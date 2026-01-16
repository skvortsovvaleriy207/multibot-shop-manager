from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user

# Статусы заказов
ORDER_STATUSES = {
    'new': 'Новая заявка',
    'processing': 'В обработке', 
    'confirmed': 'Подтвержден',
    'partner': 'Партнер-поставщик',
    'production': 'В производстве',
    'warehouse': 'На складе поставщика',
    'delivery': 'В доставке',
    'completed': 'Заказ выполнен',
    'cancelled': 'Заказ отменен'
}

# Мои заказы (покупатель)
@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT o.id, o.order_type, o.item_id, o.status, o.order_date,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.title
                       ELSE as_.title
                   END as title,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.price
                       ELSE as_.price
                   END as price,
                   u.username as seller_username
            FROM orders o
            LEFT JOIN auto_products ap ON o.order_type = 'tech' AND o.item_id = ap.id
            LEFT JOIN auto_services as_ ON o.order_type = 'service' AND o.item_id = as_.id
            LEFT JOIN users u ON o.seller_id = u.user_id
            WHERE o.user_id = ?
            ORDER BY o.order_date DESC
        """, (user_id,))
        
        orders = await cursor.fetchall()
    
    if not orders:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🛒 В магазин", callback_data="main_shop_page"))
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
        builder.adjust(1)
        
        await callback.message.edit_text(
            "📋 **Мои заказы**\n\nУ вас пока нет заказов.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    
    text = "📋 **Мои заказы**\n\n"
    builder = InlineKeyboardBuilder()
    
    for order_id, order_type, item_id, status, order_date, title, price, seller_username in orders[:10]:
        icon = "🚗" if order_type == 'tech' else "🛠"
        status_text = ORDER_STATUSES.get(status, status)
        price_text = f"{price}₽" if price else "Цена не указана"
        
        text += f"{icon} **{title}**\n"
        text += f"💰 {price_text}\n"
        text += f"📊 Статус: {status_text}\n"
        text += f"👤 Продавец: @{seller_username}\n"
        text += f"📅 {order_date[:10]}\n\n"
        
        builder.add(types.InlineKeyboardButton(
            text=f"📋 Заказ #{order_id}",
            callback_data=f"order_details_{order_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Детали заказа
@dp.callback_query(F.data.startswith("order_details_"))
async def order_details(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    order_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT o.id, o.user_id, o.order_type, o.item_id, o.seller_id, o.status, o.order_date, o.notes,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.title
                       ELSE as_.title
                   END as title,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.description
                       ELSE as_.description
                   END as description,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.price
                       ELSE as_.price
                   END as price,
                   u.username as seller_username,
                   u.phone as seller_phone
            FROM orders o
            LEFT JOIN auto_products ap ON o.order_type = 'tech' AND o.item_id = ap.id
            LEFT JOIN auto_services as_ ON o.order_type = 'service' AND o.item_id = as_.id
            LEFT JOIN users u ON o.seller_id = u.user_id
            WHERE o.id = ? AND o.user_id = ?
        """, (order_id, user_id))
        
        order = await cursor.fetchone()
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    icon = "🚗" if order[2] == 'tech' else "🛠"
    status_text = ORDER_STATUSES.get(order[4], order[4])
    
    # Правильные индексы после JOIN: [0-7]=orders fields, [8]=title, [9]=description, [10]=price, [11]=seller_username, [12]=seller_phone
    text = f"📋 **Заказ #{order[0]}**\n\n"
    text += f"{icon} **{order[8] or 'Не указано'}**\n\n"
    text += f"📊 **Статус:** {status_text}\n"
    text += f"💰 **Цена:** {order[10]}₽\n" if order[10] else "💰 **Цена:** не указана\n"
    text += f"📅 **Дата заказа:** {order[6][:10] if order[6] else 'Не указана'}\n"
    text += f"👤 **Продавец:** @{order[11] or 'не указан'}\n"
    text += f"📱 **Телефон:** {order[12]}\n" if order[12] else ""
    
    if order[9]:  # description
        text += f"\n📝 **Описание:**\n{order[9]}\n"
    
    if order[7]:  # notes
        text += f"\n💬 **Примечания:**\n{order[7]}\n"
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки действий в зависимости от статуса
    if order[4] == 'new':
        builder.add(types.InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_order_{order_id}"))
    
    builder.add(types.InlineKeyboardButton(text="💬 Связаться с продавцом", callback_data=f"contact_{order[4]}"))  # order[4] = seller_id
    builder.add(types.InlineKeyboardButton(text="◀️ К заказам", callback_data="my_orders"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Заказы для продавца
@dp.callback_query(F.data == "seller_orders")
async def seller_orders(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT o.id, o.order_type, o.item_id, o.status, o.order_date,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.title
                       ELSE as_.title
                   END as title,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.price
                       ELSE as_.price
                   END as price,
                   u.username as buyer_username
            FROM orders o
            LEFT JOIN auto_products ap ON o.order_type = 'tech' AND o.item_id = ap.id
            LEFT JOIN auto_services as_ ON o.order_type = 'service' AND o.item_id = as_.id
            LEFT JOIN users u ON o.user_id = u.user_id
            WHERE o.seller_id = ?
            ORDER BY o.order_date DESC
        """, (user_id,))
        
        orders = await cursor.fetchall()
    
    if not orders:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
        
        await callback.message.edit_text(
            "📦 **Заказы на мои товары/услуги**\n\nПока нет заказов.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    
    text = "📦 **Заказы на мои товары/услуги**\n\n"
    builder = InlineKeyboardBuilder()
    
    for order_id, order_type, item_id, status, order_date, title, price, buyer_username in orders[:10]:
        icon = "🚗" if order_type == 'tech' else "🛠"
        status_text = ORDER_STATUSES.get(status, status)
        price_text = f"{price}₽" if price else "Цена не указана"
        
        text += f"{icon} **{title}**\n"
        text += f"💰 {price_text}\n"
        text += f"📊 Статус: {status_text}\n"
        text += f"👤 Покупатель: @{buyer_username}\n"
        text += f"📅 {order_date[:10]}\n\n"
        
        builder.add(types.InlineKeyboardButton(
            text=f"📦 Заказ #{order_id}",
            callback_data=f"seller_order_{order_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Детали заказа для продавца
@dp.callback_query(F.data.startswith("seller_order_"))
async def seller_order_details(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    order_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT o.*, 
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.title
                       ELSE as_.title
                   END as title,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.description
                       ELSE as_.description
                   END as description,
                   CASE 
                       WHEN o.order_type = 'tech' THEN ap.price
                       ELSE as_.price
                   END as price,
                   u.username as buyer_username,
                   u.phone as buyer_phone
            FROM orders o
            LEFT JOIN auto_products ap ON o.order_type = 'tech' AND o.item_id = ap.id
            LEFT JOIN auto_services as_ ON o.order_type = 'service' AND o.item_id = as_.id
            LEFT JOIN users u ON o.user_id = u.user_id
            WHERE o.id = ? AND o.seller_id = ?
        """, (order_id, user_id))
        
        order = await cursor.fetchone()
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    icon = "🚗" if order[2] == 'tech' else "🛠"
    status_text = ORDER_STATUSES.get(order[4], order[4])
    
    text = f"📦 **Заказ #{order[0]}**\n\n"
    text += f"{icon} **{order[7]}**\n\n"
    text += f"📊 **Статус:** {status_text}\n"
    text += f"💰 **Цена:** {order[9]}₽\n" if order[9] else "💰 **Цена:** не указана\n"
    text += f"📅 **Дата заказа:** {order[5][:10]}\n"
    text += f"👤 **Покупатель:** @{order[10]}\n"
    text += f"📱 **Телефон:** {order[11]}\n" if order[11] else ""
    
    if order[8]:  # description
        text += f"\n📝 **Описание:**\n{order[8]}\n"
    
    if order[6]:  # notes
        text += f"\n💬 **Примечания:**\n{order[6]}\n"
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки изменения статуса
    current_status = order[4]
    if current_status == 'new':
        builder.add(types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"status_{order_id}_confirmed"))
        builder.add(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status_{order_id}_cancelled"))
    elif current_status == 'confirmed':
        builder.add(types.InlineKeyboardButton(text="🏭 В производство", callback_data=f"status_{order_id}_production"))
    elif current_status == 'production':
        builder.add(types.InlineKeyboardButton(text="📦 На склад", callback_data=f"status_{order_id}_warehouse"))
    elif current_status == 'warehouse':
        builder.add(types.InlineKeyboardButton(text="🚚 В доставку", callback_data=f"status_{order_id}_delivery"))
    elif current_status == 'delivery':
        builder.add(types.InlineKeyboardButton(text="✅ Выполнен", callback_data=f"status_{order_id}_completed"))
    
    builder.add(types.InlineKeyboardButton(text="💬 Связаться с покупателем", callback_data=f"contact_{order[1]}"))
    builder.add(types.InlineKeyboardButton(text="◀️ К заказам", callback_data="seller_orders"))
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Отмена заказа покупателем
@dp.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    try:
        order_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных", show_alert=True)
        return
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT user_id, status FROM orders WHERE id = ?", (order_id,))
        order = await cursor.fetchone()
        
        if not order or order[0] != user_id:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        
        if order[1] != 'new':
            await callback.answer("Можно отменить только новые заказы", show_alert=True)
            return
        
        await db.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        await db.commit()
    
    await callback.answer("❌ Заказ отменен")
    await my_orders(callback)

# Изменение статуса заказа
@dp.callback_query(F.data.startswith("status_"))
async def change_order_status(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[1])
    new_status = parts[2]
    user_id = callback.from_user.id
    
    async with aiosqlite.connect("bot_database.db") as db:
        # Проверяем, что это заказ продавца
        cursor = await db.execute("SELECT seller_id FROM orders WHERE id = ?", (order_id,))
        order = await cursor.fetchone()
        
        if not order or order[0] != user_id:
            await callback.answer("Нет прав на изменение статуса", show_alert=True)
            return
        
        # Обновляем статус
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        await db.commit()
    
    status_text = ORDER_STATUSES.get(new_status, new_status)
    await callback.answer(f"✅ Статус изменен на: {status_text}")
    
    # Обновляем детали заказа
    await seller_order_details(callback)



# Контакт с пользователем
@dp.callback_query(F.data.startswith("contact_"))
async def contact_user(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    contact_user_id = int(callback.data.split("_")[1])
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT username, phone FROM users WHERE user_id = ?", (contact_user_id,))
        user = await cursor.fetchone()
    
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    
    username, phone = user
    text = "📞 **Контактная информация:**\n\n"
    
    if username:
        text += f"👤 Telegram: @{username}\n"
    
    if phone:
        text += f"📱 Телефон: {phone}\n"
    
    text += f"\n💬 Вы можете написать пользователю в Telegram для обсуждения деталей."
    
    await callback.answer(text, show_alert=True)