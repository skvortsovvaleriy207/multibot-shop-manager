from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp
from config import ADMIN_ID
from utils import check_blocked_user

@dp.callback_query(F.data == "stats")
async def automarket_stats(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Статистика по товарам
        cursor = await db.execute("SELECT COUNT(*) FROM auto_products WHERE status = 'active'")
        active_products = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM auto_products")
        total_products = (await cursor.fetchone())[0]
        
        # Статистика по услугам
        cursor = await db.execute("SELECT COUNT(*) FROM auto_services WHERE status = 'active'")
        active_services = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM auto_services")
        total_services = (await cursor.fetchone())[0]
        
        # Статистика по заказам
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        total_orders = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
        completed_orders = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")
        new_orders = (await cursor.fetchone())[0]
        
        # Статистика по пользователям
        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM auto_products")
        sellers_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM orders")
        buyers_count = (await cursor.fetchone())[0]
        
        # Топ категории товаров
        cursor = await db.execute("""
            SELECT ac.name, COUNT(ap.id) as count
            FROM auto_categories ac
            LEFT JOIN auto_products ap ON ac.id = ap.category_id
            WHERE ac.type = 'tech'
            GROUP BY ac.id, ac.name
            ORDER BY count DESC
            LIMIT 3
        """)
        top_product_categories = await cursor.fetchall()
        
        # Топ категории услуг
        cursor = await db.execute("""
            SELECT ac.name, COUNT(as_.id) as count
            FROM auto_categories ac
            LEFT JOIN auto_services as_ ON ac.id = as_.category_id
            WHERE ac.type = 'service'
            GROUP BY ac.id, ac.name
            ORDER BY count DESC
            LIMIT 3
        """)
        top_service_categories = await cursor.fetchall()
    
    text = "📊 **Статистика магазина**\n\n"
    
    text += "📦 **Товары:**\n"
    text += f"• Активных: {active_products}\n"
    text += f"• Всего: {total_products}\n"
    text += f"• Продавцов: {sellers_count}\n\n"
    
    text += "🛠 **Услуги:**\n"
    text += f"• Активных: {active_services}\n"
    text += f"• Всего: {total_services}\n\n"
    
    text += "📋 **Заказы:**\n"
    text += f"• Всего: {total_orders}\n"
    text += f"• Выполнено: {completed_orders}\n"
    text += f"• Новых: {new_orders}\n"
    text += f"• Покупателей: {buyers_count}\n\n"
    
    if top_product_categories:
        text += "🏆 **Топ категории товаров:**\n"
        for name, count in top_product_categories:
            text += f"• {name}: {count}\n"
        text += "\n"
    
    if top_service_categories:
        text += "🏆 **Топ категории услуг:**\n"
        for name, count in top_service_categories:
            text += f"• {name}: {count}\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="stats"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass