from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp
from utils import check_blocked_user
from config import ADMIN_ID
from db import DB_FILE


class CategoryStates(StatesGroup):
    waiting_catalog_type = State()
    waiting_category_name = State()
    waiting_parent_id = State()
    waiting_action = State()


@dp.callback_query(F.data == "manage_categories")
async def manage_categories(callback: CallbackQuery):
    """Управление категориями - только для админа"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    # Категории товаров
    builder.add(types.InlineKeyboardButton(text="📦 Категории товаров", callback_data="catalog:product_purposes"))
    builder.add(types.InlineKeyboardButton(text="📦 Классы товаров", callback_data="catalog:product_class"))
    builder.add(types.InlineKeyboardButton(text="📦 Типы товаров", callback_data="catalog:product_types"))
    builder.add(types.InlineKeyboardButton(text="📦 Виды товаров", callback_data="catalog:product_views"))

    # Категории услуг
    builder.add(types.InlineKeyboardButton(text="🛠 Категории услуг", callback_data="catalog:service_purposes"))
    builder.add(types.InlineKeyboardButton(text="🛠 Классы услуг", callback_data="catalog:service_class"))
    builder.add(types.InlineKeyboardButton(text="🛠 Типы услуг", callback_data="catalog:service_types"))
    builder.add(types.InlineKeyboardButton(text="🛠 Виды услуг", callback_data="catalog:service_views"))

    # Категории предложений
    builder.add(types.InlineKeyboardButton(text="🤝 Категории предложений", callback_data="catalog:property_purposes"))
    builder.add(types.InlineKeyboardButton(text="🤝 Классы предложений", callback_data="catalog:property_class"))
    builder.add(types.InlineKeyboardButton(text="🤝 Типы предложений", callback_data="catalog:property_types"))
    builder.add(types.InlineKeyboardButton(text="🤝 Виды предложений", callback_data="catalog:property_views"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))

    # Оптимальное расположение: по 2 кнопки в строке
    builder.adjust(2, 2, 2, 2, 2, 2, 1)

    await callback.message.edit_text(
        text="📁 **Управление категориями каталогов**\n\n"
             "Выберите тип категорий для управления:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("catalog:"))
async def show_catalog_section(callback: CallbackQuery, state: FSMContext):
    """Показать конкретный раздел категорий"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    section = callback.data.split(":")[1]

    # Определяем русское название раздела
    section_names = {
        "product_purposes": "Категории товаров",
        "product_class": "Классы товаров",
        "product_types": "Типы товаров",
        "product_views": "Виды товаров",
        "service_purposes": "Категории услуг",
        "service_class": "Классы услуг",
        "service_types": "Типы услуг",
        "service_views": "Виды услуг",
        "property_purposes": "Категории предложений",
        "property_class": "Классы предложений",
        "property_types": "Типы предложений",
        "property_views": "Виды предложений"
    }

    section_name = section_names.get(section, section)

    async with aiosqlite.connect(DB_FILE) as db:
        # Проверяем, существует ли таблица
        cursor = await db.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{section}'
        """)
        table_exists = await cursor.fetchone()

        if not table_exists:
            # Создаем таблицу если не существует
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS {section} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

        # Получаем существующие записи
        cursor = await db.execute(f"""
            SELECT id, name
            FROM {section}
            ORDER BY name
        """)
        items = await cursor.fetchall()

        builder = InlineKeyboardBuilder()
        for item_id, item_name in items:
            builder.add(types.InlineKeyboardButton(
                text=f"✏️ {item_name}",
                callback_data=f"edit:{section}:{item_id}:{item_name}"
            ))
            builder.add(types.InlineKeyboardButton(
                text=f"❌ {item_name}",
                callback_data=f"delete:{section}:{item_id}"
            ))

        builder.add(types.InlineKeyboardButton(text="➕ Добавить", callback_data=f"add:{section}"))
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="manage_categories"))

        # Оптимальное расположение: кнопки редактирования и удаления по 2 в строке
        if items:
            # По 2 кнопки (редактировать/удалить) для каждой записи, затем добавить и назад
            builder.adjust(2, 2, 2, 2, 1, 1)
        else:
            builder.adjust(1, 1)  # Только добавить и назад

        await callback.message.edit_text(
            text=f"📁 **Управление: {section_name}**\n\n"
                 f"Текущие записи (✏️ - редактировать, ❌ - удалить):",
            reply_markup=builder.as_markup()
        )
        await callback.answer()