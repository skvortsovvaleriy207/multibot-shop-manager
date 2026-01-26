from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
from dispatcher import dp
from config import ADMIN_ID

class AdminSettingsStates(StatesGroup):
    ENTER_SUPPORT_ID = State()

# Функция для получения ID админа для поддержки
async def get_support_admin_id() -> int:
    """Получить ID админа для получения сообщений от подписчиков"""
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = 'support_admin_id'")
        result = await cursor.fetchone()
        if result:
            return int(result[0])
        return ADMIN_ID  # Возвращаем дефолтный ID если не настроено

# Функция для установки ID админа для поддержки
async def set_support_admin_id(admin_id: int):
    """Установить ID админа для получения сообщений от подписчиков"""
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        await db.execute("""
            INSERT OR REPLACE INTO settings (key, value) 
            VALUES ('support_admin_id', ?)
        """, (str(admin_id),))
        await db.commit()

# Обработчик для настроек админа
@dp.callback_query(F.data == "admin_settings")
async def admin_settings_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    support_id = await get_support_admin_id()
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📝 Изменить ID поддержки", callback_data="change_support_id"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu"))
    builder.adjust(1)
    
    text = f"""⚙️ **Настройки админа**

📞 **Текущий ID для получения сообщений от подписчиков:**
`{support_id}`

Этот ID будет получать все сообщения от подписчиков через функцию "Написать админу"."""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "change_support_id")
async def change_support_id_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📝 **Введите новый ID админа для получения сообщений от подписчиков:**\n\n"
        "Отправьте числовой ID пользователя Telegram.\n"
        "Для отмены отправьте /cancel"
    )
    await state.set_state(AdminSettingsStates.ENTER_SUPPORT_ID)
    await callback.answer()

@dp.message(AdminSettingsStates.ENTER_SUPPORT_ID)
async def process_support_id(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Отменено")
        return
    
    try:
        new_id = int(message.text)
        await set_support_admin_id(new_id)
        await state.clear()
        
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"))
        
        await message.answer(
            f"✅ **ID админа для поддержки успешно изменен!**\n\n"
            f"Новый ID: `{new_id}`\n\n"
            f"Теперь все сообщения от подписчиков будут отправляться на этот ID.",
            reply_markup=builder.as_markup()
        )
    except ValueError:
        await message.answer(
            "❌ **Ошибка!** Введите корректный числовой ID.\n\n"
            "Попробуйте еще раз или отправьте /cancel для отмены."
        )
