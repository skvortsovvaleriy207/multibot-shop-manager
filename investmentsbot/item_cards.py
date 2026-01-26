from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
import json
from dispatcher import dp
from utils import check_blocked_user

# @dp.callback_query(F.data.startswith("item_tech_"))
async def show_tech_card_DISABLED(callback: CallbackQuery):
    """Карточка предложения/товара/объекта согласно ТЗ п.2.3"""
    if await check_blocked_user(callback):
        return
    
    item_id = int(callback.data.split("_")[2])
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT ap.*, u.username, u.phone, c.name as category_name
            FROM auto_products ap
            LEFT JOIN users u ON ap.user_id = u.user_id
            LEFT JOIN categories c ON ap.category_id = c.id
            WHERE ap.id = ?
        """, (item_id,))
        
        item = await cursor.fetchone()
        
        # Получаем отзывы
        cursor = await db.execute("""
            SELECT r.rating, r.review_text, u.username, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.item_type = 'product' AND r.item_id = ?
            ORDER BY r.created_at DESC
            LIMIT 5
        """, (item_id,))
        
        reviews = await cursor.fetchall()
    
    if not item:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Формируем карточку товара согласно ТЗ п.1.2
    text = f"🚗 **{item[3]}**\n\n"  # Название товара
    text += f"📂 **Категория:** {item[-1]}\n"  # Категория
    text += f"💰 **Цена:** {item[5]}₽\n" if item[5] else "💰 **Цена:** не указана\n"
    
    # Описание товара
    if item[4]:
        text += f"\n📝 **Описание:**\n{item[4]}\n"
    
    # Характеристики
    if item[7]:  # specifications
        try:
            specs = json.loads(item[7])
            text += "\n🔧 **Характеристики:**\n"
            for key, value in specs.items():
                text += f"• {key}: {value}\n"
        except:
            pass
    
    # Наличие товара
    availability = item[11] if len(item) > 11 and item[11] else "В наличии"
    text += f"\n📦 **Наличие:** {availability}\n"
    
    # Информация о доставке и оплате
    if len(item) > 12 and item[12]:  # delivery_info
        text += f"🚚 **Доставка:** {item[12]}\n"
    
    # Гарантии
    if len(item) > 13 and item[13]:  # warranty_info
        text += f"🛡 **Гарантия:** {item[13]}\n"
    
    # Поставщик-гарант товара
    text += f"\n👤 **Продавец:** @{item[-3]}\n"  # username
    if item[-2]:  # phone
        text += f"📱 **Телефон:** {item[-2]}\n"
    
    # Рейтинг товара из 10 звезд
    if reviews:
        avg_rating = sum(r[0] for r in reviews) / len(reviews)
        stars = "⭐" * int(avg_rating)
        text += f"\n⭐ **Рейтинг:** {avg_rating:.1f}/10 {stars}\n"
        text += f"💬 **Отзывов:** {len(reviews)}\n"
    
    # Отзывы покупателей
    if reviews:
        text += "\n📝 **Последние отзывы:**\n"
        for rating, review_text, username, created_at in reviews[:3]:
            stars = "⭐" * rating
            text += f"• {stars} @{username}: {review_text[:50]}...\n"
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки действия
    if item[1] != callback.from_user.id:  # Не свой товар
        builder.add(types.InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_cart_tech_{item_id}"))
        builder.add(types.InlineKeyboardButton(text="📞 Связаться", callback_data=f"contact_{item[1]}"))
        builder.add(types.InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews_tech_{item_id}"))
    else:
        builder.add(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_tech_{item_id}"))
        builder.add(types.InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews_tech_{item_id}"))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_tech"))
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# @dp.callback_query(F.data.startswith("item_service_"))
async def show_service_card_DISABLED(callback: CallbackQuery):
    """Карточка услуги согласно ТЗ п.2.4"""
    if await check_blocked_user(callback):
        return
    
    item_id = int(callback.data.split("_")[2])
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT as_.*, u.username, u.phone, c.name as category_name
            FROM auto_services as_
            LEFT JOIN users u ON as_.user_id = u.user_id
            LEFT JOIN categories c ON as_.category_id = c.id
            WHERE as_.id = ?
        """, (item_id,))
        
        item = await cursor.fetchone()
        
        # Получаем отзывы
        cursor = await db.execute("""
            SELECT r.rating, r.review_text, u.username, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.item_type = 'service' AND r.item_id = ?
            ORDER BY r.created_at DESC
            LIMIT 5
        """, (item_id,))
        
        reviews = await cursor.fetchall()
    
    if not item:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    
    # Формируем карточку автоуслуги согласно ТЗ п.1.4
    text = f"🛠 **{item[3]}**\n\n"  # Название услуги
    text += f"📂 **Категория:** {item[-1]}\n"  # Категория
    text += f"💰 **Цена:** {item[5]}₽\n" if item[5] else "💰 **Цена:** по договоренности\n"
    
    # Местоположение
    if item[6]:  # location
        text += f"📍 **Местоположение:** {item[6]}\n"
    
    # Срок выполнения
    if len(item) > 14 and item[14]:  # duration
        text += f"⏱ **Срок выполнения:** {item[14]}\n"
    
    # Описание услуги
    if item[4]:
        text += f"\n📝 **Описание услуги:**\n{item[4]}\n"
    
    # Контактная информация
    if item[7]:  # contact_info
        text += f"\n📞 **Контакты:** {item[7]}\n"
    
    # Данные поставщика автосервиса
    text += f"\n🏢 **Поставщик услуг:**\n"
    text += f"👤 **Исполнитель:** @{item[-3]}\n"  # username
    if item[-2]:  # phone
        text += f"📱 **Телефон:** {item[-2]}\n"
    
    # Рейтинг услуги из 10 звезд
    if reviews:
        avg_rating = sum(r[0] for r in reviews) / len(reviews)
        stars = "⭐" * int(avg_rating)
        text += f"\n⭐ **Рейтинг:** {avg_rating:.1f}/10 {stars}\n"
        text += f"💬 **Отзывов:** {len(reviews)}\n"
    
    # Отзывы клиентов
    if reviews:
        text += "\n📝 **Последние отзывы:**\n"
        for rating, review_text, username, created_at in reviews[:3]:
            stars = "⭐" * rating
            text += f"• {stars} @{username}: {review_text[:50]}...\n"
    
    # Гарантии сервиса
    if len(item) > 13 and item[13]:  # warranty_info
        text += f"\n🛡 **Гарантии:** {item[13]}\n"
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки действия
    if item[1] != callback.from_user.id:  # Не своя услуга
        builder.add(types.InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_cart_service_{item_id}"))
        builder.add(types.InlineKeyboardButton(text="📞 Связаться", callback_data=f"contact_{item[1]}"))
        builder.add(types.InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews_service_{item_id}"))
    else:
        builder.add(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_service_{item_id}"))
        builder.add(types.InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews_service_{item_id}"))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_services"))
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("reviews_"))
async def show_reviews(callback: CallbackQuery):
    """Показать все отзывы о товаре/услуге"""
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    item_type = parts[1]  # tech или service
    item_id = int(parts[2])
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Получаем название товара/услуги
        if item_type == "tech":
            cursor = await db.execute("SELECT title FROM auto_products WHERE id = ?", (item_id,))
            table_type = "product"
        else:
            cursor = await db.execute("SELECT title FROM auto_services WHERE id = ?", (item_id,))
            table_type = "service"
        
        item_title = await cursor.fetchone()
        
        # Получаем все отзывы
        cursor = await db.execute("""
            SELECT r.rating, r.review_text, u.username, r.created_at
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.item_type = ? AND r.item_id = ?
            ORDER BY r.created_at DESC
        """, (table_type, item_id))
        
        reviews = await cursor.fetchall()
    
    if not item_title:
        await callback.answer("Товар/услуга не найдена", show_alert=True)
        return
    
    text = f"💬 **Отзывы: {item_title[0]}**\n\n"
    
    if not reviews:
        text += "❌ Пока нет отзывов\n\nБудьте первым, кто оставит отзыв!"
    else:
        avg_rating = sum(r[0] for r in reviews) / len(reviews)
        stars = "⭐" * int(avg_rating)
        text += f"⭐ **Средний рейтинг:** {avg_rating:.1f}/10 {stars}\n"
        text += f"📊 **Всего отзывов:** {len(reviews)}\n\n"
        
        for rating, review_text, username, created_at in reviews[:10]:
            stars = "⭐" * rating
            date = created_at[:10] if created_at else "Неизвестно"
            text += f"{stars} **@{username}** ({date})\n"
            text += f"{review_text}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data=f"add_review_{item_type}_{item_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ К товару", callback_data=f"item_{item_type}_{item_id}"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("contact_"))
async def contact_seller(callback: CallbackQuery):
    """Связаться с продавцом/поставщиком"""
    if await check_blocked_user(callback):
        return
    
    seller_id = int(callback.data.split("_")[1])
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("SELECT username, phone FROM users WHERE user_id = ?", (seller_id,))
        seller = await cursor.fetchone()
    
    if not seller:
        await callback.answer("Продавец не найден", show_alert=True)
        return
    
    username, phone = seller
    text = "📞 **Контактная информация:**\n\n"
    
    if username:
        text += f"👤 Telegram: @{username}\n"
    
    if phone:
        text += f"📱 Телефон: {phone}\n"
    
    text += "\n💬 Вы можете написать продавцу в Telegram для обсуждения деталей сделки."
    
    await callback.answer(text, show_alert=True)