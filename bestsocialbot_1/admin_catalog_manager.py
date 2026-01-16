from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from dispatcher import dp
from config import ADMIN_ID

class CategoryStates(StatesGroup):
    waiting_input = State()

# --- Main Menu ---
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

# --- Product Categories Menu ---
@dp.callback_query(F.data == "manage_product_cats")
async def manage_product_cats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Категории (Category)", callback_data="mng_tbl:product_purposes:Категории товаров"))
    builder.add(types.InlineKeyboardButton(text="Классы (Class)", callback_data="mng_tbl:product_classes:Классы товаров"))
    builder.add(types.InlineKeyboardButton(text="Типы (Type)", callback_data="mng_tbl:product_types:Типы товаров"))
    builder.add(types.InlineKeyboardButton(text="Виды (View)", callback_data="mng_tbl:product_views:Виды"))
    builder.add(types.InlineKeyboardButton(text="Иные (Other)", callback_data="mng_tbl:product_other_chars:Иные"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_catalog_manager"))
    builder.adjust(1)
    
    await callback.message.edit_text("📦 **Категории товаров**\n\nВыберите таблицу для редактирования:", reply_markup=builder.as_markup())
    await callback.answer()

# --- Service Categories Menu ---
@dp.callback_query(F.data == "manage_service_cats")
async def manage_service_cats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Категории (Category)", callback_data="mng_tbl:service_purposes:Категории услуг"))
    builder.add(types.InlineKeyboardButton(text="Классы (Class)", callback_data="mng_tbl:service_classes:Классы услуг"))
    builder.add(types.InlineKeyboardButton(text="Типы (Type)", callback_data="mng_tbl:service_types:Типы услуг"))
    builder.add(types.InlineKeyboardButton(text="Виды (View)", callback_data="mng_tbl:service_views:Виды"))
    builder.add(types.InlineKeyboardButton(text="Иные (Other)", callback_data="mng_tbl:service_other_chars:Иные"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_catalog_manager"))
    builder.adjust(1)
    
    await callback.message.edit_text("🛠 **Категории услуг**\n\nВыберите таблицу для редактирования:", reply_markup=builder.as_markup())
    await callback.answer()

# --- Generic Taxonomy Manager ---

@dp.callback_query(F.data.startswith("mng_tbl:"))
async def manage_taxonomy_table(callback: CallbackQuery, state: FSMContext):
    """
    Generic handler to list items from a taxonomy table.
    Callback data format: mng_tbl:<table_name>:<human_readable_title>
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    _, table_name, title = callback.data.split(":")
    
    # Store context
    await state.update_data(current_table=table_name, current_title=title)

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(f"SELECT id, name FROM {table_name} ORDER BY name")
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()
    
    # List items with Edit/Delete options (simplified flow: List -> Click Item -> Edit/Delete)
    # OR: List items with "❌" button next to them? Telegram buttons are limited.
    # Better: Show list of items as text, and provide "Add", "Edit", "Delete" buttons?
    # Or: Button list of items. Click item -> "Edit value" / "Delete value".
    
    for item_id, name in items:
        # Callback: act_itm:<action>:<id>
        # Let's verify item click -> Edit/Delete menu
        builder.add(types.InlineKeyboardButton(
            text=f"{name}", 
            callback_data=f"sel_itm:{item_id}"
        ))

    builder.add(types.InlineKeyboardButton(text="➕ Добавить", callback_data="add_itm"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="manage_product_cats" if "product" in table_name else "manage_service_cats"))
    builder.adjust(1) # One col for names

    text_list = "\n".join([f"• {name}" for _, name in items]) if items else "Список пуст"

    await callback.message.edit_text(
        f"🔧 **Управление: {title}**\n\n"
        f"Текущий список:\n{text_list}\n\n"
        "Выберите элемент из списка для редактирования/удаления или нажмите «Добавить»:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("sel_itm:"))
async def select_item(callback: CallbackQuery, state: FSMContext):
    """Item selected -> Show Edit/Delete options"""
    item_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    table_name = data.get("current_table")
    title = data.get("current_title")
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(f"SELECT name FROM {table_name} WHERE id = ?", (item_id,))
        res = await cursor.fetchone()
        
    if not res:
        await callback.answer("Элемент не найден", show_alert=True)
        return
        
    item_name = res[0]
    await state.update_data(selected_item_id=item_id, selected_item_name=item_name)
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_itm_act"))
    builder.add(types.InlineKeyboardButton(text="🗑 Удалить", callback_data="del_itm_act"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"mng_tbl:{table_name}:{title}"))
    
    await callback.message.edit_text(
        f"🔧 **{title}**\n\n"
        f"Выбрано: **{item_name}**\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# --- Add Item ---
@dp.callback_query(F.data == "add_itm")
async def add_item_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data.get("current_title")
    
    await callback.message.answer(f"➕ **Добавление: {title}**\n\nВведите название нового элемента:")
    await state.update_data(action="add")
    await state.set_state(CategoryStates.waiting_input)
    await callback.answer()

# --- Edit Item ---
@dp.callback_query(F.data == "edit_itm_act")
async def edit_item_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data.get("current_title")
    item_name = data.get("selected_item_name")
    
    await callback.message.answer(
        f"✏️ **Редактирование: {title}**\n\n"
        f"Текущее название: {item_name}\n"
        f"Введите новое название:"
    )
    await state.update_data(action="edit")
    await state.set_state(CategoryStates.waiting_input)
    await callback.answer()

# --- Delete Item ---
@dp.callback_query(F.data == "del_itm_act")
async def delete_item_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    table_name = data.get("current_table")
    title = data.get("current_title")
    item_id = data.get("selected_item_id")
    item_name = data.get("selected_item_name")
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
        await db.commit()
        
    await callback.answer(f"✅ '{item_name}' удалено", show_alert=True)
    
    # Return to list
    # Use the logic from manage_taxonomy_table manually or simulate a callback if possible (not easy here).
    # Easier to just re-render list.
    
    # Re-fetch items
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(f"SELECT id, name FROM {table_name} ORDER BY name")
        items = await cursor.fetchall()
        
    builder = InlineKeyboardBuilder()
    for i_id, i_name in items:
        builder.add(types.InlineKeyboardButton(text=f"{i_name}", callback_data=f"sel_itm:{i_id}"))
    builder.add(types.InlineKeyboardButton(text="➕ Добавить", callback_data="add_itm"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="manage_product_cats" if "product" in table_name else "manage_service_cats"))
    builder.adjust(1)
    
    text_list = "\n".join([f"• {name}" for _, name in items]) if items else "Список пуст"
    
    await callback.message.edit_text(
        f"🔧 **Управление: {title}**\n\n"
        f"Текущий список:\n{text_list}\n\n"
        "Выберите элемент из списка для редактирования/удаления или нажмите «Добавить»:",
        reply_markup=builder.as_markup()
    )

# --- Process Input (Add/Edit) ---
@dp.message(CategoryStates.waiting_input)
async def process_taxonomy_input(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым.")
        return
        
    data = await state.get_data()
    action = data.get("action")
    table_name = data.get("current_table")
    title = data.get("current_title")
    
    async with aiosqlite.connect("bot_database.db") as db:
        if action == "add":
            await db.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (text,))
            await message.answer(f"✅ Успешно добавлено: {text}")
        elif action == "edit":
            item_id = data.get("selected_item_id")
            await db.execute(f"UPDATE {table_name} SET name = ? WHERE id = ?", (text, item_id))
            await message.answer(f"✅ Успешно обновлено: {text}")
        await db.commit()
    
    # Return to Menu
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Вернуться к списку", callback_data=f"mng_tbl:{table_name}:{title}"))
    
    await message.answer("Действие выполнено.", reply_markup=builder.as_markup())
