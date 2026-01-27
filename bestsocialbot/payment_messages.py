from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dispatcher import dp
from utils import check_blocked_user
import aiosqlite
from db import DB_FILE

# Информация об оплате
@dp.callback_query(F.data == "payment")
async def payment_info(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    text = """💰 **Информация об оплате**

🔹 **Оплата автотехники/автоуслуг** выполняется непосредственно между подписчиками, без комиссии в боте-автомагазине

🔹 **Статусы оплаты:**
• "Оплата" - фиксируется в личном профиле участника
• "ПАРТНЕР" - для партнерских программ с поставщиками
• "ИНВЕСТОР" - для инвестиционных программ
• "Реферал" - для реферальных систем

🔹 **Способы оплаты:**
• Банковские карты
• Банковские переводы
• Электронные кошельки
• Наличные расчеты
• Договоренность с продавцом

🔹 **Безопасность:**
• Проверяйте репутацию продавца
• Используйте безопасные способы оплаты
• Сохраняйте документы об оплате
• При проблемах обращайтесь к администрации

📞 **Поддержка:** Если у вас возникли вопросы по оплате, обратитесь к администратору бота."""
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_personal_account"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Сообщения
@dp.callback_query(F.data == "messages")
async def messages_menu(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📥 Входящие", callback_data="inbox"))
    builder.add(types.InlineKeyboardButton(text="📤 Отправленные", callback_data="outbox"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_personal_account"))
    builder.adjust(2, 1)
    
    text = """📬 **Сообщения**

Здесь вы можете просматривать:
• Уведомления о новых заказах
• Изменения статусов заказов
• Сообщения от администрации
• Уведомления о новых акциях

Выберите раздел:"""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Входящие сообщения
@dp.callback_query(F.data == "inbox")
async def inbox(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    import aiosqlite
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT id, sender_id, subject, message_text, sent_at, is_read
            FROM messages 
            WHERE recipient_id = ? 
            ORDER BY sent_at DESC 
            LIMIT 10
        """, (user_id,))
        messages = await cursor.fetchall()
    
    if not messages:
        text = """📥 **Входящие сообщения**

У вас пока нет новых сообщений.

Здесь будут отображаться:
• Уведомления о новых заказах на ваши товары
• Изменения статусов ваших заказов
• Сообщения от продавцов/покупателей
• Уведомления от администрации"""
    else:
        text = f"📥 **Входящие сообщения ({len(messages)})**\n\n"
        for msg_id, sender_id, subject, message_text, sent_at, is_read in messages:
            status = "📖" if is_read else "📩"
            date = sent_at[:10] if sent_at else ""
            sender = f"ID{sender_id}" if sender_id else "Система"
            text += f"{status} **{subject or 'Уведомление'}**\n"
            text += f"👤 От: {sender} | 📅 {date}\n"
            text += f"💬 {message_text[:50]}...\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ К сообщениям", callback_data="messages"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Отправленные сообщения
@dp.callback_query(F.data == "outbox")
async def outbox(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    user_id = callback.from_user.id
    
    import aiosqlite
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT id, recipient_id, subject, message_text, sent_at
            FROM messages 
            WHERE sender_id = ? 
            ORDER BY sent_at DESC 
            LIMIT 10
        """, (user_id,))
        messages = await cursor.fetchall()
    
    if not messages:
        text = """📤 **Отправленные сообщения**

Здесь будут отображаться ваши отправленные сообщения:
• Запросы к продавцам
• Ответы покупателям
• Обращения к администрации

История сообщений пока пуста."""
    else:
        text = f"📤 **Отправленные сообщения ({len(messages)})**\n\n"
        for msg_id, recipient_id, subject, message_text, sent_at in messages:
            date = sent_at[:10] if sent_at else ""
            recipient = f"ID{recipient_id}" if recipient_id else "Система"
            text += f"📤 **{subject or 'Сообщение'}**\n"
            text += f"👤 Кому: {recipient} | 📅 {date}\n"
            text += f"💬 {message_text[:50]}...\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ К сообщениям", callback_data="messages"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Обработчик для пустых категорий
@dp.callback_query(F.data == "empty")
async def empty_handler(callback: CallbackQuery):
    await callback.answer("В данной категории пока нет предложений", show_alert=True)