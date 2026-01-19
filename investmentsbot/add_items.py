from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from dispatcher import dp
from datetime import datetime

class AddItemStates(StatesGroup):
    choosing_type = State()
    choosing_purpose = State()
    choosing_ptype = State()
    choosing_class = State()
    choosing_view = State()
    choosing_other = State()
    waiting_title = State()
    waiting_description = State()
    waiting_price = State()
    waiting_contact = State()

@dp.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_type="product")
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM product_purposes ORDER BY id")
        purposes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if purposes:
        for purpose_id, purpose_name in purposes:
            builder.add(types.InlineKeyboardButton(text=purpose_name, callback_data=f"addp_purpose_{purpose_id}"))
        builder.adjust(1)
    else:
        await callback.answer("Нет доступных категорий", show_alert=True)
        return
    builder.add(types.InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_personal_account"))
    await callback.message.edit_text("📦 **Добавление товара**\n\nВыберите категорию по назначению:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_purpose)
    await callback.answer()

@dp.callback_query(F.data.startswith("addp_purpose_"), AddItemStates.choosing_purpose)
async def add_product_purpose(callback: CallbackQuery, state: FSMContext):
    purpose_id = int(callback.data.split("_")[-1])
    await state.update_data(purpose_id=purpose_id)
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM product_types ORDER BY id")
        types_list = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if types_list:
        for type_id, type_name in types_list:
            builder.add(types.InlineKeyboardButton(text=type_name, callback_data=f"addp_type_{type_id}"))
        builder.adjust(1)
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="add_product"))
    await callback.message.edit_text("📦 **Добавление товара**\n\nВыберите подкатегорию по типу:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_ptype)
    await callback.answer()

@dp.callback_query(F.data.startswith("addp_type_"), AddItemStates.choosing_ptype)
async def add_product_type(callback: CallbackQuery, state: FSMContext):
    type_id = int(callback.data.split("_")[-1])
    await state.update_data(type_id=type_id)
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM product_classes ORDER BY id")
        classes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if classes:
        for class_id, class_name in classes:
            builder.add(types.InlineKeyboardButton(text=class_name, callback_data=f"addp_class_{class_id}"))
        builder.adjust(1)
    data = await state.get_data()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"addp_purpose_{data['purpose_id']}"))
    await callback.message.edit_text("📦 **Добавление товара**\n\nВыберите класс:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_class)
    await callback.answer()

@dp.callback_query(F.data.startswith("addp_class_"), AddItemStates.choosing_class)
async def add_product_class(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split("_")[-1])
    await state.update_data(class_id=class_id)
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM product_views ORDER BY id")
        views = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if views:
        for view_id, view_name in views:
            builder.add(types.InlineKeyboardButton(text=view_name, callback_data=f"addp_view_{view_id}"))
        builder.adjust(1)
    data = await state.get_data()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"addp_type_{data['type_id']}"))
    await callback.message.edit_text("📦 **Добавление товара**\n\nВыберите вид:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_view)
    await callback.answer()

@dp.callback_query(F.data.startswith("addp_view_"), AddItemStates.choosing_view)
async def add_product_view(callback: CallbackQuery, state: FSMContext):
    view_id = int(callback.data.split("_")[-1])
    await state.update_data(view_id=view_id)
    await callback.message.edit_text("📦 **Добавление товара**\n\nВведите название товара:")
    await state.set_state(AddItemStates.waiting_title)
    await callback.answer()

@dp.message(AddItemStates.waiting_title)
async def add_product_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание товара (или отправьте '-' чтобы пропустить):")
    await state.set_state(AddItemStates.waiting_description)

@dp.message(AddItemStates.waiting_description)
async def add_product_description(message: types.Message, state: FSMContext):
    description = None if message.text == "-" else message.text
    await state.update_data(description=description)
    await message.answer("Введите цену товара в рублях (или отправьте '-' чтобы пропустить):")
    await state.set_state(AddItemStates.waiting_price)

@dp.message(AddItemStates.waiting_price)
async def add_product_price(message: types.Message, state: FSMContext):
    price = None
    if message.text != "-":
        try:
            price = float(message.text)
        except:
            await message.answer("Неверный формат цены. Введите число или '-':")
            return
    await state.update_data(price=price)
    await message.answer("Введите контактную информацию (или отправьте '-' чтобы пропустить):")
    await state.set_state(AddItemStates.waiting_contact)

@dp.message(AddItemStates.waiting_contact)
async def add_product_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('item_type') != 'product':
        return
    contact = None if message.text == "-" else message.text
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""
            INSERT INTO auto_products (user_id, category_id, title, description, price, contact_info, status, created_at, purpose_id, type_id, class_id, view_id)
            VALUES (?, 1, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
        """, (message.from_user.id, data['title'], data.get('description'), data.get('price'), contact, datetime.now().isoformat(), data['purpose_id'], data['type_id'], data['class_id'], data['view_id']))
        await db.commit()
    await message.answer("✅ Товар успешно добавлен!")
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ В личный кабинет", callback_data="personal_account"))
    await message.answer("Выберите действие:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_type="service")
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM service_purposes ORDER BY id")
        purposes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if purposes:
        for purpose_id, purpose_name in purposes:
            builder.add(types.InlineKeyboardButton(text=purpose_name, callback_data=f"adds_purpose_{purpose_id}"))
        builder.adjust(1)
    else:
        await callback.answer("Нет доступных категорий", show_alert=True)
        return
    builder.add(types.InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_personal_account"))
    await callback.message.edit_text("🛠 **Добавление услуги**\n\nВыберите категорию по назначению:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_purpose)
    await callback.answer()

@dp.callback_query(F.data.startswith("adds_purpose_"), AddItemStates.choosing_purpose)
async def add_service_purpose(callback: CallbackQuery, state: FSMContext):
    purpose_id = int(callback.data.split("_")[-1])
    await state.update_data(purpose_id=purpose_id)
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM service_types ORDER BY id")
        types_list = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if types_list:
        for type_id, type_name in types_list:
            builder.add(types.InlineKeyboardButton(text=type_name, callback_data=f"adds_type_{type_id}"))
        builder.adjust(1)
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="add_service"))
    await callback.message.edit_text("🛠 **Добавление услуги**\n\nВыберите подкатегорию по типу:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_ptype)
    await callback.answer()

@dp.callback_query(F.data.startswith("adds_type_"), AddItemStates.choosing_ptype)
async def add_service_type(callback: CallbackQuery, state: FSMContext):
    type_id = int(callback.data.split("_")[-1])
    await state.update_data(type_id=type_id)
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM service_classes ORDER BY id")
        classes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if classes:
        for class_id, class_name in classes:
            builder.add(types.InlineKeyboardButton(text=class_name, callback_data=f"adds_class_{class_id}"))
        builder.adjust(1)
    data = await state.get_data()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"adds_purpose_{data['purpose_id']}"))
    await callback.message.edit_text("🛠 **Добавление услуги**\n\nВыберите класс:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_class)
    await callback.answer()

@dp.callback_query(F.data.startswith("adds_class_"), AddItemStates.choosing_class)
async def add_service_class(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split("_")[-1])
    await state.update_data(class_id=class_id)
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM service_views ORDER BY id")
        views = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if views:
        for view_id, view_name in views:
            builder.add(types.InlineKeyboardButton(text=view_name, callback_data=f"adds_view_{view_id}"))
        builder.adjust(1)
    data = await state.get_data()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"adds_type_{data['type_id']}"))
    await callback.message.edit_text("🛠 **Добавление услуги**\n\nВыберите вид:", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.choosing_view)
    await callback.answer()

@dp.callback_query(F.data.startswith("adds_view_"), AddItemStates.choosing_view)
async def add_service_view(callback: CallbackQuery, state: FSMContext):
    view_id = int(callback.data.split("_")[-1])
    await state.update_data(view_id=view_id)
    await callback.message.edit_text("🛠 **Добавление услуги**\n\nВведите название услуги:")
    await state.set_state(AddItemStates.waiting_title)
    await callback.answer()

@dp.message(AddItemStates.waiting_title)
async def add_service_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('item_type') == 'service':
        await state.update_data(title=message.text)
        await message.answer("Введите описание услуги (или отправьте '-' чтобы пропустить):")
        await state.set_state(AddItemStates.waiting_description)

@dp.message(AddItemStates.waiting_description)
async def add_service_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('item_type') == 'service':
        description = None if message.text == "-" else message.text
        await state.update_data(description=description)
        await message.answer("Введите цену услуги в рублях (или отправьте '-' чтобы пропустить):")
        await state.set_state(AddItemStates.waiting_price)

@dp.message(AddItemStates.waiting_price)
async def add_service_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('item_type') == 'service':
        price = None
        if message.text != "-":
            try:
                price = float(message.text)
            except:
                await message.answer("Неверный формат цены. Введите число или '-':")
                return
        await state.update_data(price=price)
        await message.answer("Введите контактную информацию (или отправьте '-' чтобы пропустить):")
        await state.set_state(AddItemStates.waiting_contact)

@dp.message(AddItemStates.waiting_contact)
async def add_service_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('item_type') == 'service':
        contact = None if message.text == "-" else message.text
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("""
                INSERT INTO auto_services (user_id, category_id, title, description, price, contact_info, status, created_at, purpose_id, type_id, class_id, view_id)
                VALUES (?, 2, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """, (message.from_user.id, data['title'], data.get('description'), data.get('price'), contact, datetime.now().isoformat(), data['purpose_id'], data['type_id'], data['class_id'], data['view_id']))
            await db.commit()
        await message.answer("✅ Услуга успешно добавлена!")
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ В личный кабинет", callback_data="personal_account"))
        await message.answer("Выберите действие:", reply_markup=builder.as_markup())
