from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dispatcher import dp
from utils import check_blocked_user

@dp.callback_query(F.data == "payment")
async def payment_info(callback: CallbackQuery):
    """Информационная функция оплаты согласно ТЗ п.1.7"""
    if await check_blocked_user(callback):
        return
    
    text = "💳 **Информация об оплате**\n\n"
    text += "1. Оплата сделок производится напрямую между покупателем и продавцом.\n\n"
    text += "2. Магазин не рекламирует и не ведёт учет товаров и услуг, не отвечает за безопасность сделок и не взимает комиссию за свои информационные услуги в сообществе."
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 Мой баланс", callback_data="my_balance"))
    builder.add(types.InlineKeyboardButton(text="📊 История операций", callback_data="payment_history"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(2, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "my_balance")
async def my_balance(callback: CallbackQuery):
    """Показать баланс пользователя"""
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    import aiosqlite
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT bonus_total, current_balance, bonus_adjustment
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        balance_data = await cursor.fetchone()
        
        # Получаем статусы
        cursor = await db.execute("""
            SELECT passive_subscriber, active_partner, investor_trader, referral_count
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        status_data = await cursor.fetchone()
    
    if not balance_data:
        balance_data = (0, 0, 0)
    if not status_data:
        status_data = ("", "", "", 0)
    
    bonus_total, current_balance, bonus_adjustment = balance_data
    passive_sub, active_partner, investor_trader, referral_count = status_data
    
    text = "💰 **Мой баланс**\n\n"
    text += "Свой баланс бонусов-монет см. в Истории баланса\n\n"
    
    text += "📋 **Мои статусы:**\n"
    if passive_sub and "да" in passive_sub.lower():
        text += "• 🟢 Пассивный подписчик (+1.0 монета/месяц)\n"
    if active_partner and "да" in active_partner.lower():
        text += "• 🟡 Активный партнер (+2.0 монеты/месяц)\n"
    if investor_trader and "да" in investor_trader.lower():
        text += "• 🔴 Инвестор/трейдер (+3.0 монеты/месяц)\n"
    
    if referral_count and referral_count > 0:
        text += f"• 🔗 Рефералов: {referral_count} (+{referral_count * 0.1} монет)\n"
    
    text += f"\n💎 **Номинальная стоимость:**\n"
    text += f"1.0 монета = 1.0 Ethereum"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📊 История", callback_data="payment_history"))
    builder.add(types.InlineKeyboardButton(text="◀️ К оплате", callback_data="payment"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "payment_history")
async def payment_history(callback: CallbackQuery):
    """История операций пользователя"""
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    import aiosqlite
    async with aiosqlite.connect("bot_database.db") as db:
        # Получаем историю из user_bonuses
        cursor = await db.execute("""
            SELECT bonus_total, bonus_adjustment, current_balance, adjustment_reason, updated_at
            FROM user_bonuses 
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 10
        """, (user_id,))
        history = await cursor.fetchall()
    
    text = "📊 **История операций**\n\n"
    
    if not history:
        text += "❌ История операций пуста\n\n"
        text += "Операции появятся после:\n"
        text += "• Прохождения опроса\n"
        text += "• Приглашения рефералов\n"
        text += "• Участия в партнерских программах"
    else:
        for bonus_total, bonus_adjustment, current_balance, reason, updated_at in history:
            date = updated_at[:16] if updated_at else "Неизвестно"
            text += f"📅 **{date}**\n"
            text += f"💰 Баланс: {current_balance} монет\n"
            if bonus_adjustment != 0:
                text += f"⚖️ Изменение: {bonus_adjustment:+.1f} монет\n"
            if reason:
                text += f"📝 Причина: {reason}\n"
            text += "\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 К балансу", callback_data="my_balance"))
    builder.add(types.InlineKeyboardButton(text="◀️ К оплате", callback_data="payment"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()