from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp
from utils import check_blocked_user
from config import ADMIN_ID
from datetime import datetime
from db import DB_FILE


class CategoryStates(StatesGroup):
    waiting_catalog_type = State()
    waiting_category_name = State()
    waiting_parent_id = State()
    waiting_action = State()


@dp.callback_query(F.data == "manage_categories")
async def manage_categories(callback: CallbackQuery, state: FSMContext):
    """Управление категориями"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📦 Товары", callback_data="cat_type_product"))
    builder.add(types.InlineKeyboardButton(text="🛠 Услуги", callback_data="cat_type_service"))
    builder.add(types.InlineKeyboardButton(text="🤝 Предложения", callback_data="cat_type_offer"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📁 **Управление категориями**\n\n"
        "Выберите тип каталога:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CategoryStates.waiting_catalog_type)
    await callback.answer()


@dp.callback_query(F.data.startswith("cat_type_"))
async def select_catalog_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа каталога"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    catalog_type = callback.data.split("_")[-1]
    await state.update_data(catalog_type=catalog_type)

    # Получаем существующие категории
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT id, name, parent_id FROM categories 
            WHERE catalog_type = ? 
            ORDER BY parent_id NULLS FIRST, name
        """, (catalog_type,))
        categories = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    # Группируем по родительским категориям
    parent_categories = {}
    for cat_id, name, parent_id in categories:
        if parent_id is None:
            parent_categories[cat_id] = {"name": name, "children": []}

    # Добавляем подкатегории
    for cat_id, name, parent_id in categories:
        if parent_id is not None and parent_id in parent_categories:
            parent_categories[parent_id]["children"].append((cat_id, name))

    # Создаем кнопки
    for parent_id, data in parent_categories.items():
        builder.add(types.InlineKeyboardButton(
            text=f"📁 {data['name']} (ред.)",
            callback_data=f"edit_cat_{parent_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text=f"❌ {data['name']} (удал.)",
            callback_data=f"delete_cat_{parent_id}"
        ))

        for child_id, child_name in data["children"]:
            builder.add(types.InlineKeyboardButton(
                text=f"   └─ {child_name} (ред.)",
                callback_data=f"edit_cat_{child_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text=f"   └─ {child_name} (удал.)",
                callback_data=f"delete_cat_{child_id}"
            ))

    builder.add(types.InlineKeyboardButton(text="➕ Добавить категорию", callback_data="add_category"))
    builder.add(types.InlineKeyboardButton(text="➕ Добавить подкатегорию", callback_data="add_subcategory"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="manage_categories"))
    builder.adjust(2)

    type_names = {"product": "товаров", "service": "услуг", "offer": "предложений"}

    await callback.message.edit_text(
        f"📁 **Категории {type_names[catalog_type]}**\n\n"
        "Существующие категории:\n"
        "Для редактирования или удаления нажмите соответствующую кнопку.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Добавление новой категории"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    data = await state.get_data()
    catalog_type = data.get('catalog_type')

    await callback.message.edit_text(
        "➕ **Добавление новой категории**\n\n"
        f"Тип каталога: {catalog_type}\n\n"
        "Введите название новой категории:"
    )
    await state.set_state(CategoryStates.waiting_category_name)
    await callback.answer()


@dp.message(CategoryStates.waiting_category_name)
async def process_category_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("Доступ запрещен.")
        return

    category_name = message.text
    data = await state.get_data()
    catalog_type = data.get('catalog_type')

    # Сохраняем категорию в БД
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO categories (catalog_type, name, created_at) 
            VALUES (?, ?, ?)
        """, (catalog_type, category_name, datetime.now().isoformat()))
        await db.commit()

    await message.answer(f"✅ Категория '{category_name}' успешно добавлена!")

    # Возвращаемся к списку категорий
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к категориям", callback_data=f"cat_type_{catalog_type}"))
    builder.adjust(1)

    await message.answer(
        f"Категория добавлена. Что дальше?",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "add_subcategory")
async def add_subcategory_start(callback: CallbackQuery, state: FSMContext):
    """Добавление новой подкатегории"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    data = await state.get_data()
    catalog_type = data.get('catalog_type')

    # Получаем родительские категории
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT id, name FROM categories 
            WHERE catalog_type = ? AND parent_id IS NULL
        """, (catalog_type,))
        parents = await cursor.fetchall()

    builder = InlineKeyboardBuilder()
    for parent_id, parent_name in parents:
        builder.add(types.InlineKeyboardButton(
            text=parent_name,
            callback_data=f"select_parent_{parent_id}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_type_{catalog_type}"))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавление подкатегории**\n\n"
        "Выберите родительскую категорию:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("select_parent_"))
async def select_parent_category(callback: CallbackQuery, state: FSMContext):
    """Выбор родительской категории для подкатегории"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    parent_id = int(callback.data.split("_")[-1])
    await state.update_data(parent_id=parent_id)

    # Получаем информацию о родительской категории
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT name, catalog_type FROM categories WHERE id = ?
        """, (parent_id,))
        parent = await cursor.fetchone()

    if parent:
        parent_name, catalog_type = parent
        await callback.message.edit_text(
            f"➕ **Добавление подкатегории**\n\n"
            f"Родительская категория: {parent_name}\n\n"
            f"Введите название подкатегории:"
        )
        await state.set_state(CategoryStates.waiting_category_name)

    await callback.answer()


@dp.callback_query(F.data.startswith("edit_cat_"))
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    """Редактирование категории"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    category_id = int(callback.data.split("_")[-1])

    # Получаем информацию о категории
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT name, catalog_type FROM categories WHERE id = ?
        """, (category_id,))
        category = await cursor.fetchone()

    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return

    category_name, catalog_type = category

    await state.update_data(editing_category_id=category_id)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"rename_cat_{category_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_type_{catalog_type}"))
    builder.adjust(1)

    await callback.message.edit_text(
        f"✏️ **Редактирование категории**\n\n"
        f"Название: {category_name}\n"
        f"Тип каталога: {catalog_type}\n"
        f"ID: {category_id}\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_cat_"))
async def delete_category(callback: CallbackQuery):
    """Удаление категории"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    category_id = int(callback.data.split("_")[-1])

    # Получаем информацию о категории
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT name, catalog_type FROM categories WHERE id = ?
        """, (category_id,))
        category = await cursor.fetchone()

    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return

    category_name, catalog_type = category

    # Проверяем, есть ли подкатегории
    cursor = await db.execute("""
        SELECT COUNT(*) FROM categories WHERE parent_id = ?
    """, (category_id,))
    has_children = (await cursor.fetchone())[0] > 0

    if has_children:
        await callback.answer("❌ Нельзя удалить категорию с подкатегориями", show_alert=True)
        return

    # Удаляем категорию
    await db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    await db.commit()

    await callback.answer(f"✅ Категория '{category_name}' удалена", show_alert=True)

    # Возвращаемся к списку категорий
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к категориям", callback_data=f"cat_type_{catalog_type}"))
    builder.adjust(1)

    await callback.message.edit_text(
        f"Категория '{category_name}' удалена.",
        reply_markup=builder.as_markup()
    )