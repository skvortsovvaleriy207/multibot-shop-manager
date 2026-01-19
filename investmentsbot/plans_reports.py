from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dispatcher import dp
from config import ADMIN_ID
from utils import check_blocked_user

async def show_plans_reports_menu(callback: CallbackQuery):
    """Показать меню планов и отчетов"""
    await plans_reports_menu(callback)

@dp.callback_query(F.data == "plans_reports")
async def plans_reports_menu(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📦 Партнеры по товарам", callback_data="partners_products"))
    builder.add(types.InlineKeyboardButton(text="🛠 Партнеры по услугам", callback_data="partners_services"))
    builder.add(types.InlineKeyboardButton(text="📊 Статистика магазина", callback_data="store_statistics"))
    builder.add(types.InlineKeyboardButton(text="📈 Отчеты по продажам", callback_data="sales_reports"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(2, 1, 1, 1)
    
    text = """📈 **Планы и отчеты**

Управление партнерскими программами и аналитика магазина:

📦 **Партнеры по товарам** - управление поставщиками товаров
🛠 **Партнеры по услугам** - управление поставщиками услуг  
📊 **Статистика** - детальная аналитика магазина
📈 **Отчеты** - отчеты по продажам и заказам"""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "partners_products")
async def partners_products(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        try:
            await callback.answer("Доступ запрещен.", show_alert=True)
        except Exception:
            pass
        return
    
    from config import AUTO_PRODUCTS_SHEET_URL
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="📈 Открыть таблицу партнеров по товарам",
        url=AUTO_PRODUCTS_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="plans_reports"))
    builder.adjust(1)
    
    text = """📦 **Партнеры по товарам**

Управление партнерскими программами с поставщиками товаров:

• Учет данных партнеров-поставщиков
• Редактирование партнерских программ  
• Выгрузка данных в карточки товаров
• Синхронизация 1 раз в день в 17:00 МСК
    
Данные автоматически обновляются в Google Sheets."""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "partners_services")
async def partners_services(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        try:
            await callback.answer("Доступ запрещен.", show_alert=True)
        except Exception:
            pass
        return
    
    from config import AUTO_SERVICES_SHEET_URL
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="📈 Открыть таблицу партнеров по услугам",
        url=AUTO_SERVICES_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="plans_reports"))
    builder.adjust(1)
    
    text = """🛠 **Партнеры по услугам**

Управление партнерскими программами с поставщиками услуг:

• Учет данных партнеров-поставщиков услуг
• Редактирование партнерских программ
• Выгрузка данных в карточки услуг  
• Синхронизация 1 раз в день в 17:00 МСК
    
Данные автоматически обновляются в Google Sheets."""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "store_statistics")
async def store_statistics(callback: CallbackQuery):
    # Перенаправляем на существующую статистику
    from automarket_stats import automarket_stats
    await automarket_stats(callback)

@dp.callback_query(F.data == "sales_reports")
async def sales_reports(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        try:
            await callback.answer("Доступ запрещен.", show_alert=True)
        except Exception:
            pass
        return
    
    from config import AUTO_ORDERS_SHEET_URL
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="📈 Открыть отчеты по продажам",
        url=AUTO_ORDERS_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="plans_reports"))
    builder.adjust(1)
    
    text = """📈 **Отчеты по продажам**

Детальная аналитика продаж магазина:

• Все заказы и их статусы
• Статистика по категориям товаров/услуг
• Анализ эффективности продавцов
• Отчеты по выручке и конверсии
    
Данные обновляются автоматически каждые 6 часов."""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass