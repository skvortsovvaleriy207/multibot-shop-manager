from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from datetime import datetime
from dispatcher import dp
from config import ADMIN_ID
from partner_sheets import export_all_partner_data
# Статусы заказов
ORDER_STATUSES = [
    "Новая заявка", "В обработке", "В работе", "В ожидании", "Подтвержден",
    "Партнер-поставщик", "В производстве", "На складе поставщика", 
    "В доставке", "Доставлен/Завершен", "Заказ выполнен", "Заказ отменен"
]

async def update_order_status_in_db(order_id: int, new_status: str) -> bool:
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            await db.commit()
        return True
    except:
        return False

async def notify_user_status_change(bot_instance, user_id: int, order_id: int, new_status: str, item_title: str):
    try:
        await bot_instance.send_message(
            user_id,
            f"📋 Статус заказа #{order_id} изменен на: **{new_status}**\n"
            f"Товар/услуга: {item_title}"
        )
    except:
        pass
from bot_instance import bot

class PartnerManagementStates(StatesGroup):
    waiting_for_partner_action = State()
    waiting_for_status_change = State()
    waiting_for_order_id = State()

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
    builder.add(types.InlineKeyboardButton(text="📋 Статусы заказов", callback_data="order_statuses"))

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

    async with aiosqlite.connect("bot_database.db") as db:
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
    
    async with aiosqlite.connect("bot_database.db") as db:
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
    
    async with aiosqlite.connect("bot_database.db") as db:
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

@dp.callback_query(F.data == "order_statuses")
async def order_statuses_menu(callback: types.CallbackQuery):
    """Меню управления статусами заказов"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT status, COUNT(*) as count
            FROM orders
            GROUP BY status
            ORDER BY count DESC
        """)
        status_counts = await cursor.fetchall()
    
    text = "📋 Статусы заказов:\n\n"
    builder = InlineKeyboardBuilder()
    
    for status, count in status_counts:
        text += f"📊 {status}: {count} заказов\n"
        builder.add(types.InlineKeyboardButton(
            text=f"{status} ({count})", 
            callback_data=f"status_orders_{status}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="🔄 Изменить статус", callback_data="change_order_status"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "change_order_status")
async def change_order_status_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса изменения статуса заказа"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    await state.set_state(PartnerManagementStates.waiting_for_order_id)
    await callback.message.edit_text(
        "🔄 Изменение статуса заказа\n\n"
        "Введите ID заказа для изменения статуса:",
        reply_markup=InlineKeyboardBuilder().add(
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order_status_change")
        ).as_markup()
    )

@dp.callback_query(F.data == "cancel_order_status_change")
async def cancel_order_status_change(callback: types.CallbackQuery, state: FSMContext):
    """Отмена изменения статуса заказа"""
    await state.clear()
    await order_statuses_menu(callback)

@dp.message(PartnerManagementStates.waiting_for_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
    """Обработка ID заказа"""
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    
    try:
        order_id = int(message.text)
        
        # Проверяем существование заказа
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                SELECT o.id, o.status, o.user_id, u.username,
                       CASE 
                           WHEN o.order_type = 'tech' THEN ap.title
                           ELSE as_.title
                       END as item_title
                FROM orders o
                LEFT JOIN auto_products ap ON o.order_type = 'tech' AND o.item_id = ap.id
                LEFT JOIN auto_services as_ ON o.order_type = 'service' AND o.item_id = as_.id
                LEFT JOIN users u ON o.user_id = u.user_id
                WHERE o.id = ?
            """, (order_id,))
            order = await cursor.fetchone()
        
        if not order:
            await message.answer("❌ Заказ с таким ID не найден. Попробуйте еще раз:")
            return
        
        await state.update_data(order_id=order_id, order_info=order)
        await state.set_state(PartnerManagementStates.waiting_for_status_change)
        
        # Показываем доступные статусы
        builder = InlineKeyboardBuilder()
        for status in ORDER_STATUSES:
            builder.add(types.InlineKeyboardButton(
                text=status, 
                callback_data=f"set_status_{status}"
            ))
        builder.add(types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order_status_change"))
        builder.adjust(2)
        
        await message.answer(
            f"📦 Заказ #{order[0]}\n"
            f"👤 Пользователь: {order[3] or order[2]}\n"
            f"📋 Товар/услуга: {order[4]}\n"
            f"📊 Текущий статус: {order[1]}\n\n"
            "Выберите новый статус:",
            reply_markup=builder.as_markup()
        )
        
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID заказа:")

@dp.callback_query(F.data.startswith("set_status_"))
async def set_order_status(callback: types.CallbackQuery, state: FSMContext):
    """Установка нового статуса заказа"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        await state.clear()
        return
    
    new_status = callback.data.replace("set_status_", "")
    data = await state.get_data()
    order_id = data.get('order_id')
    order_info = data.get('order_info')
    
    if not order_id or not order_info:
        await callback.answer("❌ Ошибка данных", show_alert=True)
        await state.clear()
        return
    
    # Обновляем статус в БД
    result = await update_order_status_in_db(order_id, new_status)
    
    if result:
        # Уведомляем пользователя
        await notify_user_status_change(
            bot, order_info[2], order_id, new_status, order_info[4]
        )
        
        await callback.message.edit_text(
            f"✅ Статус заказа #{order_id} изменен на '{new_status}'\n"
            f"Пользователь уведомлен об изменении.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◀️ К статусам", callback_data="order_statuses")
            ).as_markup()
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка при изменении статуса заказа #{order_id}",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◀️ К статусам", callback_data="order_statuses")
            ).as_markup()
        )
    
    await state.clear()

