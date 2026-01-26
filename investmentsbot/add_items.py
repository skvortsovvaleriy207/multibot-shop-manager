import json
from datetime import datetime
from aiogram import types, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp

class AddItemStates(StatesGroup):
    choosing_purpose = State()
    choosing_ptype = State()
    choosing_class = State()
    choosing_view = State()
    waiting_title = State()
    waiting_description = State()
    waiting_main_photo = State()
    waiting_additional_photos = State()
    waiting_price = State()
    waiting_contact = State()

@dp.message(AddItemStates.waiting_description)
async def add_service_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('item_type') == 'service':
        description = None if message.text == "-" else message.text
        await state.update_data(description=description)
        await message.answer("📸 **Отправьте основное фото или видео услуги.**\nОно будет отображаться на обложке.")
        await state.set_state(AddItemStates.waiting_main_photo)

# Reuse the same handlers for photos as they are generic enough if we handle context correctly?
# No, better to duplicate or make generic to avoid state confusion if flow differs slightly.
# Since the state machine is shared (AddItemStates), we can reuse the SAME handlers if they check item_type?
# Actually, the previous handlers I added for PRODUCT attached to specific states: waiting_main_photo, waiting_additional_photos.
# So if I transition service to THE SAME states, it will reuse the same logic!
# I just need to make sure the "finish" handlers (contact/price) can distinguish or if the flow is identical.
# The flow is: Description -> Main Photo -> Add Photos -> Price -> Contact -> Finish.
# The handlers I added in previous step for photos are attached to `AddItemStates.waiting_main_photo` etc.
# So they will work for services too! 
# I only need to ensure `skip_additional_photos_handler` and `add_product_additional_photos` (which I named poorly as 'product') 
# transition to `waiting_price` which is generic.
# EXCEPT `add_product_price` handles price input.
# `add_service_price` handles price input separately in the original code? 
# Yes, lines 243-256 is `add_service_price`.
# So I need to ensure the photo handlers transition to `waiting_price` and that `waiting_price` is handled correctly.
# The `add_product_price` and `add_service_price` handlers both listen to `AddItemStates.waiting_price`.
# Wait, if two handlers listen to the same state, which one triggers?
# Aiogram filters will trigger the first matching one.
# In `add_items.py`, both `add_product_price` and `add_service_price` are decorated with `@dp.message(AddItemStates.waiting_price)`.
# This is a potential bug or existing ambiguity in the code unless they have additional filters?
# Checking the original code...
# `add_product_price` is lines 115-124. `add_service_price` is lines 243-256.
# They both just invoke `state.get_data()` to check item_type?
# `add_service_price` checks `if data.get('item_type') == 'service':`.
# `add_product_price` DOES NOT CHECK `item_type` explicitly in the snippet I saw! 
# Let's check `add_product_price` again.
# Original line 116: `async def add_product_price...`
# It sets price. Then transitions to `waiting_contact`.
# It does NOT check `item_type`. This means `add_product_price` might catch service prices if it's defined first!
# I should fix this by adding filters or checks.

# Also, I need to update `add_service_contact` to save images.

@dp.message(AddItemStates.waiting_price)
async def generic_price_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    item_type = data.get('item_type')
    
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
async def generic_contact_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    item_type = data.get('item_type')
    contact = None if message.text == "-" else message.text

    # Формируем JSON с изображениями
    images_data = {
        "main": data.get("main_photo"),
        "additional": data.get("additional_photos", [])
    }
    images_json = json.dumps(images_data, ensure_ascii=False)

    if item_type == 'product':
        async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
            await db.execute("""
                INSERT INTO auto_products (user_id, category_id, title, description, price, contact_info, status, created_at, purpose_id, type_id, class_id, view_id, images)
                VALUES (?, 1, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
            """, (message.from_user.id, data['title'], data.get('description'), data.get('price'), contact, datetime.now().isoformat(), data['purpose_id'], data['type_id'], data['class_id'], data['view_id'], images_json))
            await db.commit()
        await message.answer("✅ Товар успешно добавлен!")
        
    elif item_type == 'service':
        async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
            await db.execute("""
                INSERT INTO auto_services (user_id, category_id, title, description, price, contact_info, status, created_at, purpose_id, type_id, class_id, view_id, images)
                VALUES (?, 2, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
            """, (message.from_user.id, data['title'], data.get('description'), data.get('price'), contact, datetime.now().isoformat(), data['purpose_id'], data['type_id'], data['class_id'], data['view_id'], images_json))
            await db.commit()
        await message.answer("✅ Услуга успешно добавлена!")

    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ В личный кабинет", callback_data="personal_account"))
    await message.answer("Выберите действие:", reply_markup=builder.as_markup())


@dp.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_type="product")
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    await message.answer("📸 **Отправьте основное фото или видео товара.**\nОно будет отображаться на обложке.")
    await state.set_state(AddItemStates.waiting_main_photo)

@dp.message(AddItemStates.waiting_main_photo)
async def add_product_main_photo(message: types.Message, state: FSMContext):
    if not (message.photo or message.video or message.document):
        await message.answer("❌ Пожалуйста, отправьте фото или видео (или документ с изображением).")
        return

    # Определяем тип и file_id
    file_id = None
    file_type = "photo"
    unique_id = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        unique_id = message.photo[-1].file_unique_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        unique_id = message.video.file_unique_id
        file_type = "video"
    elif message.document and message.document.mime_type.startswith('image'):
         file_id = message.document.file_id
         unique_id = message.document.file_unique_id
         file_type = "photo"
    else:
        await message.answer("❌ Поддерживаются только фото и видео.")
        return

    main_photo_data = {"type": file_type, "file_id": file_id, "unique_id": unique_id}
    await state.update_data(main_photo=main_photo_data, additional_photos=[])
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить дополнительные фото", callback_data="skip_additional_photos"))
    await message.answer("✅ Основное фото сохранено!\n\nТеперь отправьте **до 3-х дополнительных фото/видео** (по одному или альбомом).\nИли нажмите кнопку «Пропустить».", reply_markup=builder.as_markup())
    await state.set_state(AddItemStates.waiting_additional_photos)

@dp.callback_query(F.data == "skip_additional_photos", AddItemStates.waiting_additional_photos)
async def skip_additional_photos_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Дополнительные фото пропущены.")
    await callback.message.answer("Введите цену товара в рублях (или отправьте '-' чтобы пропустить):")
    await state.set_state(AddItemStates.waiting_price)
    await callback.answer()

@dp.message(AddItemStates.waiting_additional_photos)
async def add_product_additional_photos(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() in ['готово', 'done', 'skip', '-']:
        await message.answer("Ввод фото завершен. Введите цену товара в рублях (или отправьте '-' чтобы пропустить):")
        await state.set_state(AddItemStates.waiting_price)
        return

    if not (message.photo or message.video or message.document):
        return # Игнорируем текст, если это не команды выхода

    data = await state.get_data()
    additional_photos = data.get("additional_photos", [])
    
    if len(additional_photos) >= 3:
        await message.answer("⚠️ Вы уже загрузили 3 дополнительных фото. Введите цену товара:")
        await state.set_state(AddItemStates.waiting_price)
        return

    # Обработка файла
    file_id = None
    file_type = "photo"
    unique_id = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        unique_id = message.photo[-1].file_unique_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        unique_id = message.video.file_unique_id
        file_type = "video"
    elif message.document and message.document.mime_type.startswith('image'):
         file_id = message.document.file_id
         unique_id = message.document.file_unique_id
         file_type = "photo"

    if file_id:
        additional_photos.append({"type": file_type, "file_id": file_id, "unique_id": unique_id})
        await state.update_data(additional_photos=additional_photos)
        
        remaining = 3 - len(additional_photos)
        if remaining > 0:
            await message.answer(f"✅ Фото добавлено! Можно добавить еще {remaining}.\nНапишите 'Готово', если хотите закончить.")
        else:
             await message.answer("✅ Загружено 3 фото. Введите цену товара в рублях (или отправьте '-' чтобы пропустить):")
             await state.set_state(AddItemStates.waiting_price)


@dp.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_type="service")
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
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

