from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from dispatcher import dp
from config import ADMIN_ID

class CategoryStates(StatesGroup):
    waiting_product_purpose = State()
    waiting_product_type = State()
    waiting_product_class = State()
    waiting_product_view = State()
    waiting_product_other = State()
    waiting_service_purpose = State()
    waiting_service_type = State()
    waiting_service_class = State()
    waiting_service_view = State()
    waiting_service_other = State()

@dp.callback_query(F.data == "admin_catalog_manager")
async def admin_catalog_manager(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📦 Управление категориями товаров", callback_data="manage_product_cats"))
    builder.add(types.InlineKeyboardButton(text="🛠 Управление категориями услуг", callback_data="manage_service_cats"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    builder.adjust(1)
    
    await callback.message.edit_text("🔧 **Управление категориями каталога**\n\nВыберите раздел:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "manage_product_cats")
async def manage_product_cats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Категории по назначению", callback_data="manage_product_purposes"))
    builder.add(types.InlineKeyboardButton(text="Подкатегории по типам", callback_data="manage_product_types"))
    builder.add(types.InlineKeyboardButton(text="Классы", callback_data="manage_product_classes"))
    builder.add(types.InlineKeyboardButton(text="Виды", callback_data="manage_product_views"))
    builder.add(types.InlineKeyboardButton(text="Иные характеристики", callback_data="manage_product_other"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_catalog_manager"))
    builder.adjust(1)
    
    await callback.message.edit_text("📦 **Категории товаров**\n\nВыберите раздел:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "manage_service_cats")
async def manage_service_cats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Категории по назначению", callback_data="manage_service_purposes"))
    builder.add(types.InlineKeyboardButton(text="Подкатегории по типам", callback_data="manage_service_types"))
    builder.add(types.InlineKeyboardButton(text="Классы", callback_data="manage_service_classes"))
    builder.add(types.InlineKeyboardButton(text="Виды", callback_data="manage_service_views"))
    builder.add(types.InlineKeyboardButton(text="Иные характеристики", callback_data="manage_service_other"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_catalog_manager"))
    builder.adjust(1)
    
    await callback.message.edit_text("🛠 **Категории услуг**\n\nВыберите раздел:", reply_markup=builder.as_markup())
    await callback.answer()
