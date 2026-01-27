from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from datetime import datetime
from dispatcher import dp
from config import ADMIN_ID
from partner_sheets import export_all_partner_data
from db import DB_FILE


class PartnerManagementStates(StatesGroup):
    waiting_for_partner_action = State()

@dp.callback_query(F.data == "admin_partners")
async def admin_partners_menu(callback: types.CallbackQuery):
    """Меню управления партнерскими программами"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="👤 пассивные подписчики", callback_data="partners_passive"))
    builder.add(types.InlineKeyboardButton(text="📊 Партнеры", callback_data="partners"))
    builder.add(types.InlineKeyboardButton(text="💰 Инвесторы", callback_data="investors"))

    # Добавляем кнопку для перехода к Google таблице
    from config import MAIN_SURVEY_SHEET_URL
    
    if MAIN_SURVEY_SHEET_URL:
        builder.add(types.InlineKeyboardButton(text="📊 Таблица партнеров", url=MAIN_SURVEY_SHEET_URL))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(2)
    
    await callback.message.edit_text(
        "🤝 Управление партнерскими программами\n\n"
        "Выберите раздел для управления:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "partners_passive")
async def partners_passive_list(callback: types.CallbackQuery):
    """Список партнеров по автотехнике"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT DISTINCT u.user_id, u.username, u.full_name, u.business, 
                   u.products_services, u.account_status
            FROM users u
            WHERE u.passive_subscriber = 'Да'
            GROUP BY u.user_id
        """)
        partners = await cursor.fetchall()

    if not partners:
        await callback.message.edit_text(
            "📊 Пассивные подписчики \n\n"
            "Партнеров пока нет.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")
            ).as_markup()
        )
        return

    text = "📊 Пассивные подписчики:\n\n"
    builder = InlineKeyboardBuilder()

    for partner in partners[:10]:  # Показываем первых 10
        user_id, username, full_name, business, products, status = partner
        name = full_name or username or f"ID{user_id}"
        text += f"👤 {name}\n"
        text += f"🏢 {business or 'Не указано'}\n"
        text += f"📊 Статус: {status}\n\n"

        builder.add(types.InlineKeyboardButton(
            text=f"👤 {name[:20]}...",
            callback_data=f"partner_detail_{user_id}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "partners")
async def partners_list(callback: types.CallbackQuery):
    """Список партнеров"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT DISTINCT u.user_id, u.username, u.full_name, u.business, 
                   u.products_services, u.account_status, COUNT(ap.id) as products_count
            FROM users u
            LEFT JOIN auto_products ap ON u.user_id = ap.user_id
            WHERE u.active_partner = 'Да' OR u.account_status = 'ПАРТНЕР'
            GROUP BY u.user_id
            ORDER BY products_count DESC
        """)
        partners = await cursor.fetchall()
    
    if not partners:
        await callback.message.edit_text(
            "📊 Партнеры \n\n"
            "Партнеров пока нет.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")
            ).as_markup()
        )
        return
    
    text = "📊 Партнеры:\n\n"
    builder = InlineKeyboardBuilder()
    
    for partner in partners[:10]:  # Показываем первых 10
        user_id, username, full_name, business, products, status, count = partner
        name = full_name or username or f"ID{user_id}"
        text += f"👤 {name}\n"
        text += f"🏢 {business or 'Не указано'}\n"
        text += f"📊 Статус: {status}\n\n"
        
        builder.add(types.InlineKeyboardButton(
            text=f"👤 {name[:20]}...", 
            callback_data=f"partner_detail_{user_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())



@dp.callback_query(F.data == "investors")
async def investors_list(callback: types.CallbackQuery):
    """Список инвесторов"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT u.user_id, u.username, u.full_name, u.business, 
                   ub.bonus_total, ub.current_balance, u.account_status
            FROM users u
            LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
            WHERE u.investor_trader = 'Да' OR u.account_status = 'ИНВЕСТОР'
            GROUP BY u.user_id
            ORDER BY ub.current_balance DESC
        """)
        investors = await cursor.fetchall()
    
    if not investors:
        await callback.message.edit_text(
            "💰 Инвесторы\n\n"
            "Инвесторов пока нет.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")
            ).as_markup()
        )
        return
    
    text = "💰 Инвесторы:\n\n"
    builder = InlineKeyboardBuilder()
    
    for investor in investors[:10]:
        user_id, username, full_name, business, bonus_total, balance, status = investor
        name = full_name or username or f"ID{user_id}"
        text += f"👤 {name}\n"
        text += f"🏢 {business or 'Не указано'}\n"
        text += f"💰 Баланс: {balance or 0}\n"
        text += f"📊 Статус: {status}\n\n"
        
        builder.add(types.InlineKeyboardButton(
            text=f"👤 {name[:20]}...", 
            callback_data=f"investor_detail_{user_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())








