from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user
from messages_system import notify_admin_new_category, send_order_request_to_admin
from config import HOUSING_CATEGORIES


class ProductCardStates(StatesGroup):
    """Состояния для карточки товара"""
    waiting_operation = State()
    waiting_category = State()
    waiting_category_input = State()
    waiting_class = State()
    waiting_class_input = State()
    waiting_item_type = State()
    waiting_item_type_input = State()
    waiting_item_kind = State()
    waiting_item_kind_input = State()
    waiting_catalog_id = State()
    waiting_title = State()
    waiting_purpose = State()
    waiting_name = State()
    waiting_creation_date = State()
    waiting_condition = State()
    waiting_specifications = State()
    waiting_advantages = State()
    waiting_additional_info = State()
    waiting_images = State()
    waiting_main_photo = State()
    waiting_additional_photos = State()
    waiting_price = State()
    waiting_availability = State()
    waiting_detailed_specs = State()
    waiting_reviews = State()
    waiting_rating = State()
    waiting_delivery_info = State()
    waiting_supplier_info = State()
    waiting_statistics = State()
    waiting_deadline = State()
    waiting_tags = State()
    waiting_contact = State()


class ServiceCardStates(StatesGroup):
    """Состояния для карточки услуги"""
    waiting_operation = State()
    waiting_category = State()
    waiting_category_input = State()
    waiting_class = State()
    waiting_class_input = State()
    waiting_item_type = State()
    waiting_item_type_input = State()
    waiting_item_kind = State()
    waiting_item_kind_input = State()
    waiting_catalog_id = State()
    waiting_service_date = State()
    waiting_title = State()
    waiting_works = State()
    waiting_materials = State()
    waiting_main_photo = State()
    waiting_additional_photos = State()
    waiting_price = State()
    waiting_pricing = State()
    waiting_guarantees = State()
    waiting_conditions = State()
    waiting_supplier_info = State()
    waiting_reviews = State()
    waiting_rating = State()
    waiting_statistics = State()
    waiting_additional_info = State()
    waiting_deadline = State()
    waiting_tags = State()
    waiting_contact = State()


class OfferCardStates(StatesGroup):
    """Состояния для карточки предложения"""
    waiting_operation = State()
    waiting_category = State()
    waiting_category_input = State()
    waiting_class = State()
    waiting_class_input = State()
    waiting_item_type = State()
    waiting_item_type_input = State()
    waiting_item_kind = State()
    waiting_item_kind_input = State()
    waiting_catalog_id = State()
    waiting_title = State()
    waiting_purpose = State()
    waiting_name = State()
    waiting_creation_date = State()
    waiting_condition = State()
    waiting_specifications = State()
    waiting_advantages = State()
    waiting_additional_info = State()
    waiting_images = State()
    waiting_main_photo = State()
    waiting_additional_photos = State()
    waiting_price = State()
    waiting_availability = State()
    waiting_detailed_specs = State()
    waiting_reviews = State()
    waiting_rating = State()
    waiting_delivery_info = State()
    waiting_supplier_info = State()
    waiting_statistics = State()
    waiting_deadline = State()
    waiting_tags = State()
    waiting_contact = State()


@dp.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания заявки"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    if not await check_daily_limit(user_id):
        await callback.answer("❌ Превышен лимит: максимум 3 заявки в сутки", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📋 Карточка товара", callback_data="product_card_form"))
    builder.add(types.InlineKeyboardButton(text="🔧 Карточка услуги", callback_data="service_card_form"))
    builder.add(types.InlineKeyboardButton(text="💼 Карточка предложения/актива", callback_data="offer_card_form"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            "📋 **Создание заявки**\n\n"
            "Выберите тип карточки:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "📋 **Создание заявки**\n\n"
            "Выберите тип карточки:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


async def check_daily_limit(user_id: int) -> bool:
    """Проверка лимита 3 заявки в сутки"""
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        return True

    async with aiosqlite.connect("bot_database.db") as db:
        today = datetime.now().date()
        cursor = await db.execute("""
            SELECT COUNT(*) FROM order_requests 
            WHERE user_id = ? AND DATE(created_at) = ?
        """, (user_id, today))
        count = (await cursor.fetchone())[0]
        return count < 3


# ========== КАРТОЧКА ТОВАРА ==========

@dp.callback_query(F.data.startswith("product_card_form"))
async def product_card_form_start(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения карточки товара"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    if not await check_daily_limit(user_id):
        await callback.answer("❌ Превышен лимит: максимум 3 заявки в сутки", show_alert=True)
        return

    from utils import has_active_process
    if await has_active_process(user_id):
        # await callback.message.answer(
        #     "⚠️ **У вас уже есть активная заявка или заказ.**\n\n"
        #     "Вы не можете оформлять новые заявки/заказы, пока не будет завершен предыдущий процесс.\n"
        #     "Пожалуйста, дождитесь выполнения текущей задачи."
        # )
        await callback.answer("❌ Есть активная заявка", show_alert=True)
        return

    # Проверяем, передана ли категория
    preset_category = None
    if "|" in callback.data:
        try:
            val = callback.data.split("|")[1]
            # Пытаемся найти категорию по ID
            async with aiosqlite.connect("bot_database.db") as db:
                cursor = await db.execute("SELECT name FROM product_purposes WHERE id = ?", (val,))
                result = await cursor.fetchone()
                if result:
                    preset_category = result[0]
                else:
                    preset_category = val # Если не нашли по ID, считаем что это название
            
            await state.update_data(preset_category=preset_category)
        except IndexError:
            pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 Продать", callback_data="product_sell"))
    builder.add(types.InlineKeyboardButton(text="🛒 Купить", callback_data="product_buy"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="create_order"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Карточка товара**\n\n"
        "Выберите цель:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(item_type="product")
    await state.set_state(ProductCardStates.waiting_operation)
    try:
        await callback.answer()
    except Exception:
        pass


@dp.callback_query(F.data == "product_sell")
async def product_select_sell(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Продать"""
    await state.update_data(operation="sell")
    
    data = await state.get_data()
    preset_category = data.get("preset_category")
    
    if preset_category:
        await state.update_data(category=preset_category)
        # Пропускаем выбор категории, переходим к выбору класса/спецификации
        await show_product_class_selection(callback.message, state)
    else:
        await show_product_category_selection(callback.message, state)
    
    await callback.answer()


@dp.callback_query(F.data == "product_buy")
async def product_select_buy(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Купить"""
    await state.update_data(operation="buy")
    
    data = await state.get_data()
    preset_category = data.get("preset_category")
    
    if preset_category:
        await state.update_data(category=preset_category)
        await show_product_class_selection(callback.message, state)
    else:
        await show_product_category_selection(callback.message, state)
    
    await callback.answer()


async def show_product_category_selection(message: Message, state: FSMContext):
    """Показать выбор категории товара"""
    await state.set_state(ProductCardStates.waiting_category)
    builder = InlineKeyboardBuilder()

    # Получаем категории из базы данных
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_purposes ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            category_name = i[0]
            if category_name in HOUSING_CATEGORIES:
                continue
            builder.add(types.InlineKeyboardButton(
                text=category_name,
                callback_data=f"prod_cat_select:{category_name}"
            ))

    # Кнопка "Добавить"
    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="prod_cat_add"
    ))

    # Кнопка "Пропустить"
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="prod_cat_skip"
    ))

    # Кнопка "Назад"
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_op"
    ))

    builder.adjust(2)

    await message.edit_text(
        "📋 **1. Категория товара**\n\n"
        "Выберите категорию из списка или добавьте новую:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("prod_cat_select:"))
async def select_product_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории товара"""
    try:
        category = callback.data.split(":", 1)[1]
        print(f"✅ Выбрана категория товара: {category}")
        await state.update_data(category=category)
        await show_product_class_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе категории товара: {e}")
        await callback.answer("❌ Ошибка при выборе категории", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "prod_cat_add")
async def add_product_category(callback: CallbackQuery, state: FSMContext):
    """Добавление новой категории товара"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_cat_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новую категорию товара**\n\n"
        "Введите название новой категории:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_category_input)
    await callback.answer()


@dp.message(ProductCardStates.waiting_category)
async def process_product_category_direct_input(message: Message, state: FSMContext):
    """Прямой ввод категории без нажатия 'Добавить'"""
    await process_product_category_input(message, state)


@dp.message(ProductCardStates.waiting_category_input)
async def process_product_category_input(message: Message, state: FSMContext):
    """Обработка ввода новой категории товара"""
    category = message.text.strip()
    if not category:
        await message.answer("❌ Название категории не может быть пустым. Введите название:")
        return

    await state.update_data(category=category)

    user_id = message.from_user.id
    username = message.from_user.username
    
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM product_purposes WHERE name = ?", (category,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO product_purposes (name) VALUES (?)", (category,))
                    await db.commit()
                    await message.answer(f"✅ Категория '{category}' автоматически добавлена (права администратора).")
                else:
                    await message.answer(f"⚠️ Категория '{category}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
            # Fallback убран по просьбе: админу не нужно отправлять самому себе уведомление при ошибке
            # Просто просим повторить
    else:
        await notify_admin_new_category("category", category, user_id, username, "product")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_category"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_cat_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Категория '{category}' отправлена на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит её в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        # Для админа просто показываем кнопки продолжения
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_category")
async def continue_after_category(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления категории"""
    await show_product_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "prod_cat_skip")
async def skip_product_category(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора категории"""
    await state.update_data(category="")
    await show_product_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_op")
async def back_to_product_operation(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору операции"""
    await product_card_form_start(callback, state)


@dp.callback_query(F.data == "back_prod_cat_list")
async def back_to_product_category_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку категорий"""
    await show_product_category_selection(callback.message, state)
    await callback.answer()


async def show_product_class_selection(message: Message, state: FSMContext):
    """Показать выбор класса товара"""
    await state.set_state(ProductCardStates.waiting_class)
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_classes ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            class_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=class_name,
                callback_data=f"prod_cls_select:{class_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="prod_cls_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="prod_cls_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_cat"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **2. Класс товара**\n\n"
        "Выберите класс из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("prod_cls_select:"))
async def select_product_class(callback: CallbackQuery, state: FSMContext):
    """Выбор класса товара"""
    try:
        item_class = callback.data.split(":", 1)[1]
        print(f"✅ Выбран класс товара: {item_class}")
        await state.update_data(item_class=item_class)
        await show_product_type_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе класса товара: {e}")
        await callback.answer("❌ Ошибка при выборе класса", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "prod_cls_add")
async def add_product_class(callback: CallbackQuery, state: FSMContext):
    """Добавление нового класса товара"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_cls_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый класс товара**\n\n"
        "Введите название нового класса:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_class_input)
    await callback.answer()


@dp.message(ProductCardStates.waiting_class)
async def process_product_class_direct_input(message: Message, state: FSMContext):
    """Прямой ввод класса без нажатия 'Добавить'"""
    # Если введен текст, считаем что пользователь хочет добавить новый
    if message.text:
       await process_product_class_input(message, state)


@dp.message(ProductCardStates.waiting_class_input)
async def process_product_class_input(message: Message, state: FSMContext):
    """Обработка ввода нового класса товара"""
    item_class = message.text.strip()
    if not item_class:
        await message.answer("❌ Название класса не может быть пустым. Введите название:")
        return

    if len(item_class) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_class=item_class)

    user_id = message.from_user.id
    username = message.from_user.username
    
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM product_classes WHERE name = ?", (item_class,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO product_classes (name) VALUES (?)", (item_class,))
                    await db.commit()
                    await message.answer(f"✅ Класс '{item_class}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Класс '{item_class}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
            # Fallback убран
    else:
        await notify_admin_new_category("class", item_class, user_id, username, "product")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_class"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_cls_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Класс '{item_class}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_class")
async def continue_after_class(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления класса"""
    await show_product_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "prod_cls_skip")
async def skip_product_class(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора класса"""
    await state.update_data(item_class="")
    await show_product_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_cat")
async def back_to_product_category(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору категории"""
    await show_product_category_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_cls_list")
async def back_to_product_class_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку классов"""
    await show_product_class_selection(callback.message, state)
    await callback.answer()


async def show_product_type_selection(message: Message, state: FSMContext):
    """Показать выбор типа товара"""
    await state.set_state(ProductCardStates.waiting_item_type)
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_types ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            type_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=type_name,
                callback_data=f"prod_typ_select:{type_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="prod_typ_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="prod_typ_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_cls"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **3. Тип товара**\n\n"
        "Выберите тип из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("prod_typ_select:"))
async def select_product_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа товара"""
    try:
        item_type = callback.data.split(":", 1)[1]
        print(f"✅ Выбран тип товара: {item_type}")
        await state.update_data(item_type=item_type)
        await show_product_view_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе типа товара: {e}")
        await callback.answer("❌ Ошибка при выборе типа", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "prod_typ_add")
async def add_product_type(callback: CallbackQuery, state: FSMContext):
    """Добавление нового типа товара"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_typ_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый тип товара**\n\n"
        "Введите название нового типа:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_item_type_input)
    await callback.answer()


@dp.message(ProductCardStates.waiting_item_type)
async def process_product_type_direct_input(message: Message, state: FSMContext):
    """Прямой ввод типа без нажатия 'Добавить'"""
    if message.text:
        await process_product_type_input(message, state)


@dp.message(ProductCardStates.waiting_item_type_input)
async def process_product_type_input(message: Message, state: FSMContext):
    """Обработка ввода нового типа товара"""
    item_type = message.text.strip()
    if not item_type:
        await message.answer("❌ Название типа не может быть пустым. Введите название:")
        return

    if len(item_type) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_type=item_type)

    user_id = message.from_user.id
    username = message.from_user.username
    
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM product_types WHERE name = ?", (item_type,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO product_types (name) VALUES (?)", (item_type,))
                    await db.commit()
                    await message.answer(f"✅ Тип '{item_type}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Тип '{item_type}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
            # Fallback убран
    else:
        await notify_admin_new_category("type", item_type, user_id, username, "product")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_type"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_typ_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Тип '{item_type}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_type")
async def continue_after_type(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления типа"""
    await show_product_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "prod_typ_skip")
async def skip_product_type(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора типа"""
    await state.update_data(item_type="")
    await show_product_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_cls")
async def back_to_product_class(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору класса"""
    await show_product_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_typ_list")
async def back_to_product_type_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку типов"""
    await show_product_type_selection(callback.message, state)
    await callback.answer()


async def show_product_view_selection(message: Message, state: FSMContext):
    """Показать выбор вида товара"""
    await state.set_state(ProductCardStates.waiting_item_kind)
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_views ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            view_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=view_name,
                callback_data=f"prod_vw_select:{view_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="prod_vw_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="prod_vw_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_typ"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **4. Вид товара**\n\n"
        "Выберите вид из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("prod_vw_select:"))
async def select_product_view(callback: CallbackQuery, state: FSMContext):
    """Выбор вида товара"""
    try:
        item_kind = callback.data.split(":", 1)[1]
        print(f"✅ Выбран вид товара: {item_kind}")
        await state.update_data(item_kind=item_kind)
        await ask_product_catalog_id(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе вида товара: {e}")
        await callback.answer("❌ Ошибка при выборе вида", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "prod_vw_add")
async def add_product_view(callback: CallbackQuery, state: FSMContext):
    """Добавление нового вида товара"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_vw_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый вид товара**\n\n"
        "Введите название нового вида:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_item_kind_input)
    await callback.answer()


@dp.message(ProductCardStates.waiting_item_kind)
async def process_product_view_direct_input(message: Message, state: FSMContext):
    """Прямой ввод вида без нажатия 'Добавить'"""
    if message.text:
        await process_product_view_input(message, state)


@dp.message(ProductCardStates.waiting_item_kind_input)
async def process_product_view_input(message: Message, state: FSMContext):
    """Обработка ввода нового вида товара"""
    item_kind = message.text.strip()
    if not item_kind:
        await message.answer("❌ Название вида не может быть пустым. Введите название:")
        return

    await state.update_data(item_kind=item_kind)

    user_id = message.from_user.id
    username = message.from_user.username
    
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM product_views WHERE name = ?", (item_kind,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO product_views (name) VALUES (?)", (item_kind,))
                    await db.commit()
                    await message.answer(f"✅ Вид '{item_kind}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Вид '{item_kind}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
            # Fallback убран
    else:
        await notify_admin_new_category("kind", item_kind, user_id, username, "product")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_view"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_vw_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Вид '{item_kind}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_view")
async def continue_after_view(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления вида"""
    await ask_product_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "prod_vw_skip")
async def skip_product_view(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора вида"""
    await state.update_data(item_kind="")
    await ask_product_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_typ")
async def back_to_product_type(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору типа"""
    await show_product_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_vw_list")
async def back_to_product_view_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку видов"""
    await show_product_view_selection(callback.message, state)
    await callback.answer()


async def ask_product_catalog_id(message: Message, state: FSMContext):
    """Запрос ID в каталоге"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_prod_vw"
    ))
    builder.adjust(1)

    await message.edit_text(
        "📋 **5. ID в Каталоге**\n\n"
        "Введите ID товара в каталоге (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_catalog_id)


@dp.callback_query(F.data == "back_prod_vw")
async def back_to_product_view(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору вида"""
    await show_product_view_selection(callback.message, state)
    await callback.answer()


@dp.message(ProductCardStates.waiting_catalog_id)
async def product_process_catalog_id(message: Message, state: FSMContext):
    """Обработка ID в каталоге"""
    catalog_id = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(catalog_id=catalog_id)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_catalog_id"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **6. Название товара**\n\n"
        "Введите краткое и точное описание, соответствующее поисковым запросам (обязательно):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_title)


@dp.callback_query(F.data == "back_to_product_catalog_id")
async def back_to_product_catalog_id(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу ID каталога"""
    await ask_product_catalog_id(callback.message, state)
    await callback.answer()


@dp.message(ProductCardStates.waiting_title)
async def product_process_title(message: Message, state: FSMContext):
    """Обработка названия товара"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название товара не может быть пустым. Пожалуйста, введите название:")
        return

    if len(title) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(title=title)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_title"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **7. Назначение и способы использования**\n\n"
        "Для чего предназначен товар и как его использовать (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_purpose)


@dp.callback_query(F.data == "back_to_product_title")
async def back_to_product_title(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу названия товара"""
    await product_process_catalog_id(callback.message, state)
    await callback.answer()


@dp.message(ProductCardStates.waiting_purpose)
async def product_process_purpose(message: Message, state: FSMContext):
    """Обработка назначения товара"""
    purpose = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(purpose=purpose)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_purpose"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **8. Наименование**\n\n"
        "Полное наименование товара (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_name)


@dp.message(ProductCardStates.waiting_name)
async def product_process_name(message: Message, state: FSMContext):
    """Обработка наименования товара"""
    name = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(name=name)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_name"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **9. Дата создания/выпуска**\n\n"
        "Дата производства или создания товара (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_creation_date)


@dp.message(ProductCardStates.waiting_creation_date)
async def product_process_creation_date(message: Message, state: FSMContext):
    """Обработка даты создания"""
    creation_date = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(creation_date=creation_date)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_creation_date"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **10. Состояние**\n\n"
        "Новое, б/у, восстановленное и т.д. (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_condition)


@dp.message(ProductCardStates.waiting_condition)
async def product_process_condition(message: Message, state: FSMContext):
    """Обработка состояния товара"""
    condition = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(condition=condition)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_condition"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **11. Эксплуатационные характеристики**\n\n"
        "Ключевые характеристики товара (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_specifications)


@dp.message(ProductCardStates.waiting_specifications)
async def product_process_specifications(message: Message, state: FSMContext):
    """Обработка характеристик товара"""
    specifications = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(specifications=specifications)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_specifications"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **12. Преимущества в сравнении с аналогами**\n\n"
        "Почему стоит выбрать этот товар (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_advantages)


@dp.message(ProductCardStates.waiting_advantages)
async def product_process_advantages(message: Message, state: FSMContext):
    """Обработка преимуществ товара"""
    advantages = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(advantages=advantages)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_advantages"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **13. Другая важная и полезная информация**\n\n"
        "Любая дополнительная информация (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_additional_info)


@dp.message(ProductCardStates.waiting_additional_info)
async def product_process_additional_info(message: Message, state: FSMContext):
    """Обработка дополнительной информации"""
    additional_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(additional_info=additional_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_additional_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📸 **14. Изображения и/или видео**\n\n"
        "Отправьте **основное фото или видео** товара (обязательно).\n"
        "Оно будет отображаться на обложке.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_main_photo)


@dp.message(ProductCardStates.waiting_main_photo)
async def product_process_main_photo(message: Message, state: FSMContext):
    """Обработка основного фото"""
    if not (message.photo or message.video or message.document):
        await message.answer("❌ Пожалуйста, отправьте фото или видео.")
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

    if not file_id:
         await message.answer("❌ Не удалось распознать медиа.")
         return

    main_photo_data = {"type": file_type, "file_id": file_id, "unique_id": unique_id}
    await state.update_data(main_photo=main_photo_data, additional_photos=[])

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить дополнительные", callback_data="skip_prod_add_photos"))
    
    await message.answer(
        "✅ Основное фото сохранено!\n\n"
        "Теперь отправьте **до 3-х дополнительных фото/видео** (по одному или альбомом).\n"
        "Или нажмите кнопку «Пропустить».",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_additional_photos)

@dp.callback_query(F.data == "skip_prod_add_photos", ProductCardStates.waiting_additional_photos)
async def skip_product_additional_photos(callback: CallbackQuery, state: FSMContext):
    """Пропуск дополнительных фото"""
    await callback.message.edit_text("Дополнительные фото пропущены.")
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_additional_photos"
    )) # Need to handle this back button? Or reuse exiting logic? 
       # "back_to_product_images" was the old one. I should probably rename or reuse.
       # Reuse logic: if I use "back_to_product_images" I must insure it points to restart media upload.
    builder.adjust(1)
    
    await callback.message.answer(
        "📋 **15. Цена**\n\n"
        "Актуальная стоимость с учетом текущих скидок и акций (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_price)
    await callback.answer()

@dp.message(ProductCardStates.waiting_additional_photos)
async def product_process_additional_photos(message: Message, state: FSMContext):
    """Обработка дополнительных фото"""
    if message.text and message.text.lower() in ['готово', 'done', 'skip', '-', 'пропустить']:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_product_additional_photos"))
        builder.adjust(1)

        await message.answer("Ввод фото завершен.", reply_markup=builder.as_markup())
        await message.answer("📋 **15. Цена**\n\nАктуальная стоимость с учетом текущих скидок и акций (необязательно):\nИли напишите 'пропустить':")
        await state.set_state(ProductCardStates.waiting_price)
        return

    if not (message.photo or message.video or message.document):
        return

    data = await state.get_data()
    additional_photos = data.get("additional_photos", [])
    
    if len(additional_photos) >= 3:
        await message.answer("⚠️ Вы уже загрузили 3 дополнительных фото. Введите цену или нажмите 'Пропустить дополнительные'.")
        return

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
             builder = InlineKeyboardBuilder()
             builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_product_additional_photos")) 
             builder.adjust(1)
             
             await message.answer("✅ Загружено 3 фото.", reply_markup=builder.as_markup())
             await message.answer("📋 **15. Цена**\n\nАктуальная стоимость с учетом текущих скидок и акций (необязательно):\nИли напишите 'пропустить':")
             await state.set_state(ProductCardStates.waiting_price)


@dp.message(ProductCardStates.waiting_price)
async def product_process_price(message: Message, state: FSMContext):
    """Обработка цены"""
    price = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(price=price)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_price"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **16. Наличие**\n\n"
        "Информация о местонахождении и доступности (в наличии, под заказ, ожидается) (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_availability)


@dp.message(ProductCardStates.waiting_availability)
async def product_process_availability(message: Message, state: FSMContext):
    """Обработка информации о наличии"""
    availability = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(availability=availability)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_availability"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **17. Характеристики**\n\n"
        "Детальные технические характеристики, размеры, материалы и другие параметры (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_detailed_specs)


@dp.message(ProductCardStates.waiting_detailed_specs)
async def product_process_detailed_specs(message: Message, state: FSMContext):
    """Обработка подробных характеристик"""
    detailed_specs = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(detailed_specs=detailed_specs)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_detailed_specs"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **18. Отзывы покупателей и экспертов**\n\n"
        "Мнения и оценки, помогающие сформировать доверие (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_reviews)


@dp.message(ProductCardStates.waiting_reviews)
async def product_process_reviews(message: Message, state: FSMContext):
    """Обработка отзывов"""
    reviews = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(reviews=reviews)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_reviews"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **19. Рейтинг**\n\n"
        "Общая текущая оценка из 10 звезд (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_rating)


@dp.message(ProductCardStates.waiting_rating)
async def product_process_rating(message: Message, state: FSMContext):
    """Обработка рейтинга"""
    rating = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(rating=rating)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_rating"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **20. Информация о доставке и оплате**\n\n"
        "Условия поставки и передачи, способы оплаты, документальное оформление, гарантии (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_delivery_info)


@dp.message(ProductCardStates.waiting_delivery_info)
async def product_process_delivery_info(message: Message, state: FSMContext):
    """Обработка информации о доставке"""
    delivery_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(delivery_info=delivery_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_delivery_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **21. Поставщик-гарант товара**\n\n"
        "Реквизиты, данные руководителя и менеджера, лицензии, формы договоров (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_supplier_info)


@dp.message(ProductCardStates.waiting_supplier_info)
async def product_process_supplier_info(message: Message, state: FSMContext):
    """Обработка информации о поставщике"""
    supplier_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(supplier_info=supplier_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_supplier_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **22. Статистика реализации**\n\n"
        "Данные статистики и иная информация (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_statistics)


@dp.message(ProductCardStates.waiting_statistics)
async def product_process_statistics(message: Message, state: FSMContext):
    """Обработка статистики"""
    statistics = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(statistics=statistics)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_statistics"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **23. Сроки**\n\n"
        "Сроки поставки или выполнения (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_deadline)


@dp.message(ProductCardStates.waiting_deadline)
async def product_process_deadline(message: Message, state: FSMContext):
    """Обработка сроков"""
    deadline = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(deadline=deadline)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_deadline"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **24. Теги/ключевые слова**\n\n"
        "Ключевые слова для поиска (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_tags)


@dp.message(ProductCardStates.waiting_tags)
async def product_process_tags(message: Message, state: FSMContext):
    """Обработка тегов"""
    tags = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(tags=tags)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_product_tags"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **25. Контактная информация**\n\n"
        "Как с вами связаться (телефон, email, Telegram) (обязательно):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProductCardStates.waiting_contact)


@dp.message(ProductCardStates.waiting_contact)
async def product_process_contact(message: Message, state: FSMContext):
    """Обработка контактной информации и сохранение заявки товара"""
    contact = message.text.strip()
    if not contact:
        await message.answer("❌ Контактная информация не может быть пустой. Пожалуйста, введите контакты:")
        return

    if len(contact) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(contact=contact)

    # Получаем все данные
    data = await state.get_data()

    # Формируем JSON с изображениями
    images_data = {
        "main": data.get("main_photo"),
        "additional": data.get("additional_photos", [])
    }
    import json
    images_json = json.dumps(images_data, ensure_ascii=False)

    # Сохраняем заявку в базу данных
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                INSERT INTO order_requests 
                (user_id, operation, item_type, category, item_class, item_type_detail, item_kind,
                 title, purpose, name, creation_date, condition, specifications, 
                 advantages, additional_info, images, price, availability, detailed_specs, 
                 reviews, rating, delivery_info, supplier_info, statistics, deadline, tags, 
                 contact, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.from_user.id,
                data.get('operation', ''),
                'product',
                data.get('category', ''),
                data.get('item_class', ''),
                data.get('item_type', ''),
                data.get('item_kind', ''),
                data.get('title', ''),
                data.get('purpose', ''),
                data.get('name', ''),
                data.get('creation_date', ''),
                data.get('condition', ''),
                data.get('specifications', ''),
                data.get('advantages', ''),
                data.get('additional_info', ''),
                images_json,
                data.get('price', ''),
                data.get('availability', ''),
                data.get('detailed_specs', ''),
                data.get('reviews', ''),
                data.get('rating', ''),
                data.get('delivery_info', ''),
                data.get('supplier_info', ''),
                data.get('statistics', ''),
                data.get('deadline', ''),
                data.get('tags', ''),
                data.get('contact', ''),
                'active',
                datetime.now().isoformat()
            ))

            # Получаем ID созданной заявки
            new_request_id = cursor.lastrowid
            await db.commit()

            print(f"✅ Заявка создана с ID: {new_request_id} для пользователя {message.from_user.id}")

            # Добавляем заявку в корзину пользователя
            await db.execute("""
                INSERT OR IGNORE INTO cart_order 
                (user_id, item_type, item_id, quantity, price, added_at, source_table)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.from_user.id,
                'товар',
                new_request_id,
                1,
                data.get('price', '0'),
                datetime.now().isoformat(),
                'order_requests'
            ))
            await db.commit()
            print(f"✅ Заявка {new_request_id} добавлена в корзину пользователя {message.from_user.id}")

            # Синхронизация с Google Sheets
            try:
                from google_sheets import sync_order_requests_to_sheets
                result = await sync_order_requests_to_sheets()
                if result:
                    print(f"✅ Заявка {new_request_id} синхронизирована с Google Sheets")
                else:
                    print(f"⚠️ Заявка {new_request_id} сохранена, но произошла ошибка синхронизации с Google Sheets")
            except Exception as e:
                print(f"❌ Ошибка импорта модуля Google Sheets: {e}")

            await send_order_request_to_admin(message.chat.id, new_request_id, data)

            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="🏠 В личный кабинет", callback_data="personal_account"))
            builder.add(types.InlineKeyboardButton(text="🛒 К заявкам", callback_data="cart_order"))
            builder.adjust(1)

            await message.answer(
                "✅ **Заявка успешно создана!**\n\n"
                f"Заявка №{new_request_id} сохранена и добавлена в вашу корзину.",
                reply_markup=builder.as_markup()
            )

            # Очищаем состояние
            await state.clear()

    except Exception as e:
        print(f"❌ Ошибка при сохранении заявки: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Произошла ошибка при сохранении заявки. Попробуйте еще раз.")


# ========== КАРТОЧКА УСЛУГИ ==========

@dp.callback_query(F.data.startswith("service_card_form"))
async def service_card_form_start(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения карточки услуги"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    if not await check_daily_limit(user_id):
        await callback.answer("❌ Превышен лимит: максимум 3 заявки в сутки", show_alert=True)
        return

    from utils import has_active_process
    if await has_active_process(user_id):
        # await callback.message.answer(
        #     "⚠️ **У вас уже есть активная заявка или заказ.**\n\n"
        #     "Вы не можете оформлять новые заявки/заказы, пока не будет завершен предыдущий процесс.\n"
        #     "Пожалуйста, дождитесь выполнения текущей задачи."
        # )
        await callback.answer("❌ Есть активная заявка", show_alert=True)
        return

    # Проверяем, передана ли категория
    preset_category = None
    if "|" in callback.data:
        try:
            val = callback.data.split("|")[1]
            # Пытаемся найти категорию по ID
            async with aiosqlite.connect("bot_database.db") as db:
                cursor = await db.execute("SELECT name FROM service_purposes WHERE id = ?", (val,))
                result = await cursor.fetchone()
                if result:
                    preset_category = result[0]
                else:
                    preset_category = val
            
            await state.update_data(preset_category=preset_category)
        except IndexError:
            pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🛠 Предложить услугу", callback_data="service_offer"))
    builder.add(types.InlineKeyboardButton(text="🔧 Заказать услугу", callback_data="service_order"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="create_order"))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            "📋 **Карточка услуги**\n\n"
            "Выберите цель:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "📋 **Карточка услуги**\n\n"
            "Выберите цель:",
            reply_markup=builder.as_markup()
        )
    await state.update_data(item_type="service")
    await state.set_state(ServiceCardStates.waiting_operation)
    try:
        await callback.answer()
    except Exception:
        pass


@dp.callback_query(F.data == "service_offer")
async def service_select_offer(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Предложить услугу"""
    await state.update_data(operation="sell")
    
    data = await state.get_data()
    preset_category = data.get("preset_category")
    
    if preset_category:
        await state.update_data(category=preset_category)
        await show_service_class_selection(callback.message, state)
    else:
        await show_service_category_selection(callback.message, state)
        
    await callback.answer()


@dp.callback_query(F.data == "service_order")
async def service_select_order(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Заказать услугу"""
    await state.update_data(operation="buy")
    
    data = await state.get_data()
    preset_category = data.get("preset_category")
    
    if preset_category:
        await state.update_data(category=preset_category)
        await show_service_class_selection(callback.message, state)
    else:
        await show_service_category_selection(callback.message, state)
    
    await callback.answer()


async def show_service_category_selection(message: Message, state: FSMContext):
    """Показать выбор категории услуги"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_purposes ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            category_name = i[0]
            if category_name in HOUSING_CATEGORIES:
                continue
            builder.add(types.InlineKeyboardButton(
                text=category_name,
                callback_data=f"serv_cat_select:{category_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="serv_cat_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="serv_cat_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_op"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **1. Категория услуги**\n\n"
        "Выберите категорию из списка или добавьте новую:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_category)


@dp.callback_query(F.data.startswith("serv_cat_select:"))
async def select_service_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории услуги"""
    try:
        category = callback.data.split(":", 1)[1]
        print(f"✅ Выбрана категория услуги: {category}")
        await state.update_data(category=category)
        await show_service_class_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе категории услуги: {e}")
        await callback.answer("❌ Ошибка при выборе категории", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "serv_cat_skip")
async def skip_service_category(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора категории услуги"""
    await state.update_data(category="")
    await show_service_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_op")
async def back_to_service_operation(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору операции услуги"""
    await service_card_form_start(callback, state)


async def show_service_class_selection(message: Message, state: FSMContext):
    """Показать выбор класса услуги"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_classes ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            class_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=class_name,
                callback_data=f"serv_cls_select:{class_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="serv_cls_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="serv_cls_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_cat"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **2. Класс услуги**\n\n"
        "Выберите класс из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_class)

# ... существующий код до обработки предложения ...

@dp.callback_query(F.data == "serv_cat_add")
async def add_service_category(callback: CallbackQuery, state: FSMContext):
    """Добавление новой категории услуги"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_cat_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новую категорию услуги**\n\n"
        "Введите название новой категории:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_category_input)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_category)
async def service_category_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода категории, если пользователь написал текст вместо кнопки"""
    # Если это текстовое сообщение, считаем что пользователь хочет добавить новую категорию
    if message.text:
        await state.set_state(ServiceCardStates.waiting_category_input)
        await process_service_category_input(message, state)


@dp.message(ServiceCardStates.waiting_category_input)
async def process_service_category_input(message: Message, state: FSMContext):
    """Обработка ввода новой категории услуги"""
    category = message.text.strip()
    if not category:
        await message.answer("❌ Название категории не может быть пустым. Введите название:")
        return

    await state.update_data(category=category)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM service_purposes WHERE name = ?", (category,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO service_purposes (name) VALUES (?)", (category,))
                    await db.commit()
                    await message.answer(f"✅ Категория '{category}' автоматически добавлена (права администратора).")
                else:
                    await message.answer(f"⚠️ Категория '{category}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
            # Fallback убран
    else:
        await notify_admin_new_category("услуги", category, user_id, username, "service")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_service_category"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_cat_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Категория '{category}' отправлена на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит её в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_service_category")
async def continue_after_service_category(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления категории услуги"""
    await show_service_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data.startswith("serv_cls_select:"))
async def select_service_class(callback: CallbackQuery, state: FSMContext):
    """Выбор класса услуги"""
    try:
        item_class = callback.data.split(":", 1)[1]
        print(f"✅ Выбран класс услуги: {item_class}")
        await state.update_data(item_class=item_class)
        await show_service_type_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе класса услуги: {e}")
        await callback.answer("❌ Ошибка при выборе класса", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "serv_cls_add")
async def add_service_class(callback: CallbackQuery, state: FSMContext):
    """Добавление нового класса услуги"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_cls_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый класс услуги**\n\n"
        "Введите название нового класса:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_class_input)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_class)
async def service_class_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода класса, если пользователь написал текст вместо кнопки"""
    if message.text:
        await state.set_state(ServiceCardStates.waiting_class_input)
        await process_service_class_input(message, state)


@dp.message(ServiceCardStates.waiting_class_input)
async def process_service_class_input(message: Message, state: FSMContext):
    """Обработка ввода нового класса услуги"""
    item_class = message.text.strip()
    if not item_class:
        await message.answer("❌ Название класса не может быть пустым. Введите название:")
        return

    await state.update_data(item_class=item_class)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM service_classes WHERE name = ?", (item_class,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO service_classes (name) VALUES (?)", (item_class,))
                    await db.commit()
                    await message.answer(f"✅ Класс '{item_class}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Класс '{item_class}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
            # Fallback убран
    else:
        await notify_admin_new_category("class", item_class, user_id, username, "service")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_service_class"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_cls_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Класс '{item_class}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_service_class")
async def continue_after_service_class(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления класса услуги"""
    await show_service_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "serv_cls_skip")
async def skip_service_class(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора класса услуги"""
    await state.update_data(item_class="")
    await show_service_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_cat")
async def back_to_service_category(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору категории услуги"""
    await show_service_category_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_cat_list")
async def back_to_service_category_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку категорий услуг"""
    await show_service_category_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_cls_list")
async def back_to_service_class_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку классов услуг"""
    await show_service_class_selection(callback.message, state)
    await callback.answer()


async def show_service_type_selection(message: Message, state: FSMContext):
    """Показать выбор типа услуги"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_types ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            type_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=type_name,
                callback_data=f"serv_typ_select:{type_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="serv_typ_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="serv_typ_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_cls"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **3. Тип услуги**\n\n"
        "Выберите тип из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_item_type)


@dp.callback_query(F.data.startswith("serv_typ_select:"))
async def select_service_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа услуги"""
    try:
        item_type = callback.data.split(":", 1)[1]
        print(f"✅ Выбран тип услуги: {item_type}")
        await state.update_data(item_type=item_type)
        await show_service_view_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе типа услуги: {e}")
        await callback.answer("❌ Ошибка при выборе типа", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "serv_typ_add")
async def add_service_type(callback: CallbackQuery, state: FSMContext):
    """Добавление нового типа услуги"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_typ_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый тип услуги**\n\n"
        "Введите название нового типа:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_item_type_input)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_item_type)
async def service_type_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода типа, если пользователь написал текст вместо кнопки"""
    if message.text:
        await state.set_state(ServiceCardStates.waiting_item_type_input)
        await process_service_type_input(message, state)


@dp.message(ServiceCardStates.waiting_item_type_input)
async def process_service_type_input(message: Message, state: FSMContext):
    """Обработка ввода нового типа услуги"""
    item_type = message.text.strip()
    if not item_type:
        await message.answer("❌ Название типа не может быть пустым. Введите название:")
        return

    if len(item_type) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_type=item_type)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM service_types WHERE name = ?", (item_type,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO service_types (name) VALUES (?)", (item_type,))
                    await db.commit()
                    await message.answer(f"✅ Тип '{item_type}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Тип '{item_type}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
    else:
        await notify_admin_new_category("type", item_type, user_id, username, "service")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_service_type"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_typ_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Тип '{item_type}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_service_type")
async def continue_after_service_type(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления типа услуги"""
    await show_service_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "serv_typ_skip")
async def skip_service_type(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора типа услуги"""
    await state.update_data(item_type="")
    await show_service_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_cls")
async def back_to_service_class(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору класса услуги"""
    await show_service_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_typ_list")
async def back_to_service_type_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку типов услуг"""
    await show_service_type_selection(callback.message, state)
    await callback.answer()


async def show_service_view_selection(message: Message, state: FSMContext):
    """Показать выбор вида услуги"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_views ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            view_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=view_name,
                callback_data=f"serv_vw_select:{view_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="serv_vw_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="serv_vw_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_typ"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **4. Вид услуги**\n\n"
        "Выберите вид из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_item_kind)


@dp.callback_query(F.data.startswith("serv_vw_select:"))
async def select_service_view(callback: CallbackQuery, state: FSMContext):
    """Выбор вида услуги"""
    try:
        item_kind = callback.data.split(":", 1)[1]
        print(f"✅ Выбран вид услуги: {item_kind}")
        await state.update_data(item_kind=item_kind)
        await ask_service_catalog_id(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе вида услуги: {e}")
        await callback.answer("❌ Ошибка при выборе вида", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data == "serv_vw_add")
async def add_service_view(callback: CallbackQuery, state: FSMContext):
    """Добавление нового вида услуги"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_vw_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый вид услуги**\n\n"
        "Введите название нового вида:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_item_kind_input)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_item_kind)
async def service_view_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода вида, если пользователь написал текст вместо кнопки"""
    if message.text:
        await state.set_state(ServiceCardStates.waiting_item_kind_input)
        await process_service_view_input(message, state)
    

@dp.message(ServiceCardStates.waiting_item_kind_input)
async def process_service_view_input(message: Message, state: FSMContext):
    """Обработка ввода нового вида услуги"""
    item_kind = message.text.strip()
    if not item_kind:
        await message.answer("❌ Название вида не может быть пустым. Введите название:")
        return

    if len(item_kind) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_kind=item_kind)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        # Автоматическое добавление для администратора
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                # Проверяем существование
                cursor = await db.execute("SELECT 1 FROM service_views WHERE name = ?", (item_kind,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO service_views (name) VALUES (?)", (item_kind,))
                    await db.commit()
                    await message.answer(f"✅ Вид '{item_kind}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Вид '{item_kind}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
    else:
        await notify_admin_new_category("kind", item_kind, user_id, username, "service")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_service_view"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_vw_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Вид '{item_kind}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_service_view")
async def continue_after_service_view(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления вида услуги"""
    await ask_service_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "serv_vw_skip")
async def skip_service_view(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора вида услуги"""
    await state.update_data(item_kind="")
    await ask_service_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_typ")
async def back_to_service_type(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору типа услуги"""
    await show_service_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_vw_list")
async def back_to_service_view_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку видов услуг"""
    await show_service_view_selection(callback.message, state)
    await callback.answer()


async def ask_service_catalog_id(message: Message, state: FSMContext):
    """Запрос ID в каталоге услуг"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_serv_vw"
    ))
    builder.adjust(1)

    await message.edit_text(
        "📋 **5. ID в Каталоге услуг**\n\n"
        "Введите ID услуги в каталоге (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_catalog_id)


@dp.callback_query(F.data == "back_serv_vw")
async def back_to_service_view(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору вида услуги"""
    await show_service_view_selection(callback.message, state)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_catalog_id)
async def service_process_catalog_id(message: Message, state: FSMContext):
    """Обработка ID в каталоге услуг"""
    catalog_id = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(catalog_id=catalog_id)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_catalog_id"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **6. Дата заявки/заказа/выполнения услуги**\n\n"
        "Введите дату (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_service_date)


@dp.callback_query(F.data == "back_to_service_catalog_id")
async def back_to_service_catalog_id(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу ID каталога услуг"""
    await ask_service_catalog_id(callback.message, state)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_service_date)
async def service_process_service_date(message: Message, state: FSMContext):
    """Обработка даты услуги"""
    service_date = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(service_date=service_date)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_service_date"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **7. Наименование и объем услуги**\n\n"
        "Введите наименование и объем услуги (обязательно):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_title)


@dp.callback_query(F.data == "back_to_service_service_date")
async def back_to_service_service_date(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу даты услуги"""
    await service_process_catalog_id(callback.message, state)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_title)
async def service_process_title(message: Message, state: FSMContext):
    """Обработка наименования услуги"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Наименование услуги не может быть пустым. Пожалуйста, введите наименование:")
        return

    if len(title) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(title=title)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_title"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **8. Перечень выполняемых работ**\n\n"
        "Введите перечень работ (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_works)


@dp.callback_query(F.data == "back_to_service_title")
async def back_to_service_title(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу наименования услуги"""
    await service_process_service_date(callback.message, state)
    await callback.answer()


@dp.message(ServiceCardStates.waiting_works)
async def service_process_works(message: Message, state: FSMContext):
    """Обработка перечня работ"""
    works = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(works=works)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_works"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **9. Марки, типы, особенности материалов/деталей**\n\n"
        "Введите информацию о материалах (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_materials)


@dp.message(ServiceCardStates.waiting_materials)
async def service_process_materials(message: Message, state: FSMContext):
    """Обработка информации о материалах"""
    materials = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(materials=materials)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_materials"
    ))
    builder.adjust(1)

    await message.answer(
        "📸 **10. Информационные фото/видео услуги**\n\n"
        "Отправьте **основное фото или видео** услуги (обязательно).\n"
        "Оно будет отображаться на обложке.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_main_photo)


@dp.message(ServiceCardStates.waiting_main_photo)
async def service_process_main_photo(message: Message, state: FSMContext):
    """Обработка основного фото услуги"""
    if not (message.photo or message.video or message.document):
        await message.answer("❌ Пожалуйста, отправьте фото или видео.")
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

    if not file_id:
         await message.answer("❌ Не удалось распознать медиа.")
         return

    main_photo_data = {"type": file_type, "file_id": file_id, "unique_id": unique_id}
    await state.update_data(main_photo=main_photo_data, additional_photos=[])

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить дополнительные", callback_data="skip_svc_add_photos"))
    
    await message.answer(
        "✅ Основное фото сохранено!\n\n"
        "Теперь отправьте **до 3-х дополнительных фото/видео** (по одному или альбомом).\n"
        "Или нажмите кнопку «Пропустить».",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_additional_photos)

@dp.callback_query(F.data == "skip_svc_add_photos", ServiceCardStates.waiting_additional_photos)
async def skip_service_additional_photos(callback: CallbackQuery, state: FSMContext):
    """Пропуск дополнительных фото услуги"""
    await callback.message.edit_text("Дополнительные фото пропущены.")
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_additional_photos"
    ))
    builder.adjust(1)
    
    await callback.message.answer(
        "📋 **11. Стоимость и срок выполнения услуги**\n\n"
        "Введите стоимость и сроки (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_price)
    await callback.answer()

@dp.message(ServiceCardStates.waiting_additional_photos)
async def service_process_additional_photos(message: Message, state: FSMContext):
    """Обработка дополнительных фото услуги"""
    if message.text and message.text.lower() in ['готово', 'done', 'skip', '-', 'пропустить']:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_service_additional_photos"))
        builder.adjust(1)

        await message.answer("Ввод фото завершен.", reply_markup=builder.as_markup())
        await message.answer("📋 **11. Стоимость и срок выполнения услуги**\n\nВведите стоимость и сроки (необязательно):\nИли напишите 'пропустить':")
        await state.set_state(ServiceCardStates.waiting_price)
        return

    if not (message.photo or message.video or message.document):
        return

    data = await state.get_data()
    additional_photos = data.get("additional_photos", [])
    
    if len(additional_photos) >= 3:
        await message.answer("⚠️ Вы уже загрузили 3 дополнительных фото. Введите стоимость или нажмите 'Пропустить дополнительные'.")
        return

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
             builder = InlineKeyboardBuilder()
             builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_service_additional_photos")) 
             builder.adjust(1)
             
             await message.answer("✅ Загружено 3 фото.", reply_markup=builder.as_markup())
             await message.answer("📋 **11. Стоимость и срок выполнения услуги**\n\nВведите стоимость и сроки (необязательно):\nИли напишите 'пропустить':")
             await state.set_state(ServiceCardStates.waiting_price)


@dp.message(ServiceCardStates.waiting_price)
async def service_process_price(message: Message, state: FSMContext):
    """Обработка стоимости и сроков"""
    price = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(price=price)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_price"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **12. Прайс работ и материалов по услуге**\n\n"
        "Введите прайс в табличном виде (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_pricing)


@dp.message(ServiceCardStates.waiting_pricing)
async def service_process_pricing(message: Message, state: FSMContext):
    """Обработка прайса"""
    pricing = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(pricing=pricing)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_pricing"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **13. Гарантии сервиса, скидки**\n\n"
        "Введите информацию о гарантиях и скидках (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_guarantees)


@dp.message(ServiceCardStates.waiting_guarantees)
async def service_process_guarantees(message: Message, state: FSMContext):
    """Обработка гарантий и скидок"""
    guarantees = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(guarantees=guarantees)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_guarantees"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **14. Особые условия**\n\n"
        "Введите особые условия (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_conditions)


@dp.message(ServiceCardStates.waiting_conditions)
async def service_process_conditions(message: Message, state: FSMContext):
    """Обработка условий"""
    conditions = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(conditions=conditions)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_conditions"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **15. Реквизиты, лицензии, формы договоров**\n\n"
        "Введите информацию о поставщике услуги (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_supplier_info)


@dp.message(ServiceCardStates.waiting_supplier_info)
async def service_process_supplier_info(message: Message, state: FSMContext):
    """Обработка информации о поставщике"""
    supplier_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(supplier_info=supplier_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_supplier_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **16. Отзывы и рейтинг услуги**\n\n"
        "Введите отзывы и рейтинг из 10 звезд (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_reviews)


@dp.message(ServiceCardStates.waiting_reviews)
async def service_process_reviews(message: Message, state: FSMContext):
    """Обработка отзывов и рейтинга"""
    reviews = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(reviews=reviews)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_reviews"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **17. Рейтинг**\n\n"
        "Введите рейтинг из 10 звезд (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_rating)


@dp.message(ServiceCardStates.waiting_rating)
async def service_process_rating(message: Message, state: FSMContext):
    """Обработка рейтинга"""
    rating = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(rating=rating)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_rating"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **18. Статистика реализации**\n\n"
        "Введите статистику реализации (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_statistics)


@dp.message(ServiceCardStates.waiting_statistics)
async def service_process_statistics(message: Message, state: FSMContext):
    """Обработка статистики"""
    statistics = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(statistics=statistics)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_statistics"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **19. Иная информация**\n\n"
        "Введите дополнительную информацию (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_additional_info)


@dp.message(ServiceCardStates.waiting_additional_info)
async def service_process_additional_info(message: Message, state: FSMContext):
    """Обработка дополнительной информации"""
    additional_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(additional_info=additional_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_additional_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **20. Сроки**\n\n"
        "Введите сроки выполнения услуги (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_deadline)


@dp.message(ServiceCardStates.waiting_deadline)
async def service_process_deadline(message: Message, state: FSMContext):
    """Обработка сроков"""
    deadline = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(deadline=deadline)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_deadline"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **21. Теги/ключевые слова**\n\n"
        "Введите ключевые слова для поиска (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_tags)


@dp.message(ServiceCardStates.waiting_tags)
async def service_process_tags(message: Message, state: FSMContext):
    """Обработка тегов"""
    tags = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(tags=tags)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_service_tags"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **22. Контактная информация**\n\n"
        "Как с вами связаться (телефон, email, Telegram) (обязательно):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ServiceCardStates.waiting_contact)


@dp.message(ServiceCardStates.waiting_contact)
async def service_process_contact(message: Message, state: FSMContext):
    """Обработка контактной информации и сохранение заявки услуги"""
    contact = message.text.strip()
    if not contact:
        await message.answer("❌ Контактная информация не может быть пустой. Пожалуйста, введите контакты:")
        return

    if len(contact) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(contact=contact)

    # Получаем все данные
    data = await state.get_data()

    # Формируем JSON с изображениями
    images_data = {
        "main": data.get("main_photo"),
        "additional": data.get("additional_photos", [])
    }
    import json
    images_json = json.dumps(images_data, ensure_ascii=False)

    # Сохраняем заявку в базу данных
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
            INSERT INTO order_requests 
                (user_id, operation, category, item_class, item_type, item_kind,
                         catalog_id, service_date, title, works, materials, images, price, pricing,
                         guarantees, conditions, supplier_info, reviews, rating, statistics, 
                         additional_info, deadline, tags, contact, status, created_at, item_type_detail)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            message.from_user.id,
                            data.get('operation', ''),
                            data.get('category', ''),
                            data.get('item_class', ''),
                            'service', # item_type fixed as 'service'
                            data.get('item_kind', ''),
                            data.get('catalog_id', ''),
                            data.get('service_date', ''),
                            data.get('title', ''),
                            data.get('works', ''),
                            data.get('materials', ''),
                            images_json,
                            data.get('price', ''),
                            data.get('pricing', ''),
                            data.get('guarantees', ''),
                            data.get('conditions', ''),
                            data.get('supplier_info', ''),
                            data.get('reviews', ''),
                            data.get('rating', ''),
                            data.get('statistics', ''),
                            data.get('additional_info', ''),
                            data.get('deadline', ''),
                            data.get('tags', ''),
                            data.get('contact', ''),
                            'active',
                            datetime.now().isoformat(),
                            data.get('item_type', '') # item_type_detail stores the user input type
                        ))

            # Получаем ID созданной заявки
            new_request_id = cursor.lastrowid
            await db.commit()

            print(f"✅ Заявка услуги создана с ID: {new_request_id} для пользователя {message.from_user.id}")

            # Добавляем заявку в корзину пользователя
            await db.execute("""
                INSERT OR IGNORE INTO cart_order 
                (user_id, item_type, item_id, quantity, price, added_at, source_table)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.from_user.id,
                'услуга',
                new_request_id,
                1,
                data.get('price', '0'),
                datetime.now().isoformat(),
                'order_requests'
            ))
            await db.commit()
            print(f"✅ Заявка услуги {new_request_id} добавлена в корзину пользователя {message.from_user.id}")

            # Синхронизация с Google Sheets
            try:
                from google_sheets import sync_order_requests_to_sheets
                result = await sync_order_requests_to_sheets()
                if result:
                    print(f"✅ Заявка услуги {new_request_id} синхронизирована с Google Sheets")
                else:
                    print(f"⚠️ Заявка услуги {new_request_id} сохранена, но произошла ошибка синхронизации с Google Sheets")
            except Exception as e:
                print(f"❌ Ошибка импорта модуля Google Sheets: {e}")

            await send_order_request_to_admin(message.chat.id, new_request_id, data)

            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="🏠 В личный кабинет", callback_data="personal_account"))
            builder.add(types.InlineKeyboardButton(text="🛒 К заявкам", callback_data="cart_order"))
            builder.adjust(1)

            await message.answer(
                "✅ **Заявка услуги успешно создана!**\n\n"
                f"Заявка №{new_request_id} сохранена и добавлена в вашу корзину.",
                reply_markup=builder.as_markup()
            )

            # Очищаем состояние
            await state.clear()

    except Exception as e:
        print(f"❌ Ошибка при сохранении заявки услуги: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Произошла ошибка при сохранении заявки. Попробуйте еще раз.")


# ========== КАРТОЧКА ПРЕДЛОЖЕНИЯ/АКТИВА (ПОЛНАЯ РЕАЛИЗАЦИЯ) ==========


# ========== КАРТОЧКА ПРЕДЛОЖЕНИЯ/АКТИВА ==========

@dp.callback_query(F.data.startswith("offer_card_form"))
async def offer_card_form_start(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения карточки предложения/актива"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    if not await check_daily_limit(user_id):
        await callback.answer("❌ Превышен лимит: максимум 3 заявки в сутки", show_alert=True)
        return

    from utils import has_active_process
    if await has_active_process(user_id):
        # await callback.message.answer(
        #     "⚠️ **У вас уже есть активная заявка или заказ.**\n\n"
        #     "Вы не можете оформлять новые заявки/заказы, пока не будет завершен предыдущий процесс.\n"
        #     "Пожалуйста, дождитесь выполнения текущей задачи."
        # )
        await callback.answer("❌ Есть активная заявка", show_alert=True)
        return

    # Проверяем, передана ли категория
    preset_category = None
    if "|" in callback.data:
        try:
            preset_category = callback.data.split("|")[1]
            await state.update_data(preset_category=preset_category)
        except IndexError:
            pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 Продать", callback_data="offer_sell"))
    builder.add(types.InlineKeyboardButton(text="🛒 Купить", callback_data="offer_buy"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="create_order"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Карточка предложения (Property)**\n\n"
        "Выберите цель:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(item_type="offer")
    await state.set_state(OfferCardStates.waiting_operation)
    await callback.answer()


@dp.callback_query(F.data == "offer_sell")
async def offer_select_sell(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Продать для предложения"""
    await state.update_data(operation="sell")
    
    data = await state.get_data()
    preset_category = data.get("preset_category")
    
    if preset_category:
        await state.update_data(category=preset_category)
        await show_offer_class_selection(callback.message, state)
    else:
        await show_offer_category_selection(callback.message, state)
    
    await callback.answer()


@dp.callback_query(F.data == "offer_buy")
async def offer_select_buy(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Купить для предложения"""
    await state.update_data(operation="buy")
    
    data = await state.get_data()
    preset_category = data.get("preset_category")
    
    if preset_category:
        await state.update_data(category=preset_category)
        await show_offer_class_selection(callback.message, state)
    else:
        await show_offer_category_selection(callback.message, state)
    
    try:
        await callback.answer()
    except Exception:
        pass


async def show_offer_category_selection(message: Message, state: FSMContext):
    """Показать выбор категории предложения"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM categories WHERE catalog_type = 'offer' ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            category_name = i[0]
            # Truncate to ensure callback data < 64 bytes (ocs: + name)
            safe_name = category_name[:50]
            builder.add(types.InlineKeyboardButton(
                text=category_name,
                callback_data=f"ocs:{safe_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="off_cat_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="off_cat_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_op"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **1. Категория предложения**\n\n"
        "Выберите категорию из списка или добавьте новую:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_category)


@dp.callback_query(F.data.startswith("ocs:"))
async def select_offer_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории предложения"""
    try:
        category = callback.data.split(":", 1)[1]
        print(f"✅ Выбрана категория предложения: {category}")
        await state.update_data(category=category)
        await show_offer_class_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе категории предложения: {e}")
        await callback.answer("❌ Ошибка при выборе категории", show_alert=True)
    try:
        await callback.answer()
    except Exception:
        pass


@dp.message(OfferCardStates.waiting_category)
async def offer_category_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода категории предложения"""
    if message.text:
        await state.set_state(OfferCardStates.waiting_category_input)
        await process_offer_category_input(message, state)


@dp.callback_query(F.data == "off_cat_skip")
async def skip_offer_category(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора категории предложения"""
    await state.update_data(category="")
    await show_offer_class_selection(callback.message, state)
    try:
        await callback.answer()
    except Exception:
        pass


@dp.callback_query(F.data == "back_off_op")
async def back_to_offer_operation(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору операции предложения"""
    await offer_card_form_start(callback, state)


async def show_offer_class_selection(message: Message, state: FSMContext):
    """Показать выбор класса предложения"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM offer_classes ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            class_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=class_name,
                callback_data=f"off_cls_select:{class_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="off_cls_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="off_cls_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_cat"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **2. Класс предложения**\n\n"
        "Выберите класс из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_class)

@dp.callback_query(F.data == "off_cat_add")
async def add_offer_category(callback: CallbackQuery, state: FSMContext):
    """Добавление новой категории предложения"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_cat_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новую категорию предложения**\n\n"
        "Введите название новой категории:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_category_input)
    await callback.answer()


@dp.message(OfferCardStates.waiting_category_input)
async def process_offer_category_input(message: Message, state: FSMContext):
    """Обработка ввода новой категории предложения"""
    category = message.text.strip()
    if not category:
        await message.answer("❌ Название категории не может быть пустым. Введите название:")
        return

    await state.update_data(category=category)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                cursor = await db.execute("SELECT 1 FROM categories WHERE name = ? AND catalog_type = 'offer'", (category,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO categories (catalog_type, name) VALUES ('offer', ?)", (category,))
                    await db.commit()
                    await message.answer(f"✅ Категория '{category}' автоматически добавлена (права администратора).")
                else:
                    await message.answer(f"⚠️ Категория '{category}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
    else:
        await notify_admin_new_category("предложения", category, user_id, username, "offer")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_offer_category"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_cat_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Категория '{category}' отправлена на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит её в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_offer_category")
async def continue_after_offer_category(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления категории предложения"""
    await show_offer_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data.startswith("off_cls_select:"))
async def select_offer_class(callback: CallbackQuery, state: FSMContext):
    """Выбор класса предложения"""
    try:
        item_class = callback.data.split(":", 1)[1]
        print(f"✅ Выбран класс предложения: {item_class}")
        await state.update_data(item_class=item_class)
        await show_offer_type_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе класса предложения: {e}")
        await callback.answer("❌ Ошибка при выборе класса", show_alert=True)
    await callback.answer()


@dp.message(OfferCardStates.waiting_class)
async def offer_class_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода класса предложения"""
    if message.text:
        await state.set_state(OfferCardStates.waiting_class_input)
        await process_offer_class_input(message, state)


@dp.callback_query(F.data == "off_cls_add")
async def add_offer_class(callback: CallbackQuery, state: FSMContext):
    """Добавление нового класса предложения"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_cls_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый класс предложения**\n\n"
        "Введите название нового класса:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_class_input)
    await callback.answer()


@dp.message(OfferCardStates.waiting_class_input)
async def process_offer_class_input(message: Message, state: FSMContext):
    """Обработка ввода нового класса предложения"""
    item_class = message.text.strip()
    if not item_class:
        await message.answer("❌ Название класса не может быть пустым. Введите название:")
        return

    if len(item_class) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_class=item_class)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                cursor = await db.execute("SELECT 1 FROM offer_classes WHERE name = ?", (item_class,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO offer_classes (name) VALUES (?)", (item_class,))
                    await db.commit()
                    await message.answer(f"✅ Класс '{item_class}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Класс '{item_class}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
    else:
        await notify_admin_new_category("class", item_class, user_id, username, "offer")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_offer_class"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_cls_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Класс '{item_class}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_offer_class")
async def continue_after_offer_class(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления класса предложения"""
    await show_offer_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "off_cls_skip")
async def skip_offer_class(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора класса предложения"""
    await state.update_data(item_class="")
    await show_offer_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_cat")
async def back_to_offer_category(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору категории предложения"""
    await show_offer_category_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_cat_list")
async def back_to_offer_category_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку категорий предложений"""
    await show_offer_category_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_cls_list")
async def back_to_offer_class_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку классов предложений"""
    await show_offer_class_selection(callback.message, state)
    await callback.answer()


async def show_offer_type_selection(message: Message, state: FSMContext):
    """Показать выбор типа предложения"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM offer_types ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            type_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=type_name,
                callback_data=f"off_typ_select:{type_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="off_typ_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="off_typ_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_cls"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **3. Тип предложения**\n\n"
        "Выберите тип из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_item_type)


@dp.callback_query(F.data.startswith("off_typ_select:"))
async def select_offer_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа предложения"""
    try:
        item_type = callback.data.split(":", 1)[1]
        print(f"✅ Выбран тип предложения: {item_type}")
        await state.update_data(item_type=item_type)
        await show_offer_view_selection(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе типа предложения: {e}")
        await callback.answer("❌ Ошибка при выборе типа", show_alert=True)
    await callback.answer()


@dp.message(OfferCardStates.waiting_item_type)
async def offer_type_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода типа предложения"""
    if message.text:
        await state.set_state(OfferCardStates.waiting_item_type_input)
        await process_offer_type_input(message, state)


@dp.callback_query(F.data == "off_typ_add")
async def add_offer_type(callback: CallbackQuery, state: FSMContext):
    """Добавление нового типа предложения"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_typ_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый тип предложения**\n\n"
        "Введите название нового типа:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_item_type_input)
    await callback.answer()


@dp.message(OfferCardStates.waiting_item_type_input)
async def process_offer_type_input(message: Message, state: FSMContext):
    """Обработка ввода нового типа предложения"""
    item_type = message.text.strip()
    if not item_type:
        await message.answer("❌ Название типа не может быть пустым. Введите название:")
        return

    if len(item_type) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_type=item_type)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                cursor = await db.execute("SELECT 1 FROM offer_types WHERE name = ?", (item_type,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO offer_types (name) VALUES (?)", (item_type,))
                    await db.commit()
                    await message.answer(f"✅ Тип '{item_type}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Тип '{item_type}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
    else:
        await notify_admin_new_category("type", item_type, user_id, username, "offer")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_offer_type"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_typ_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Тип '{item_type}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_offer_type")
async def continue_after_offer_type(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления типа предложения"""
    await show_offer_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "off_typ_skip")
async def skip_offer_type(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора типа предложения"""
    await state.update_data(item_type="")
    await show_offer_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_cls")
async def back_to_offer_class(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору класса предложения"""
    await show_offer_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_typ_list")
async def back_to_offer_type_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку типов предложений"""
    await show_offer_type_selection(callback.message, state)
    await callback.answer()


async def show_offer_view_selection(message: Message, state: FSMContext):
    """Показать выбор вида предложения"""
    builder = InlineKeyboardBuilder()

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM offer_views ORDER BY name")
        items = await cursor.fetchall()

        for i in items:
            view_name = i[0]
            builder.add(types.InlineKeyboardButton(
                text=view_name,
                callback_data=f"off_vw_select:{view_name}"
            ))

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить",
        callback_data="off_vw_add"
    ))
    builder.add(types.InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data="off_vw_skip"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_typ"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 **4. Вид предложения**\n\n"
        "Выберите вид из списка или добавьте новый:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_item_kind)


@dp.callback_query(F.data.startswith("off_vw_select:"))
async def select_offer_view(callback: CallbackQuery, state: FSMContext):
    """Выбор вида предложения"""
    try:
        item_kind = callback.data.split(":", 1)[1]
        print(f"✅ Выбран вид предложения: {item_kind}")
        await state.update_data(item_kind=item_kind)
        await ask_offer_catalog_id(callback.message, state)
    except Exception as e:
        print(f"❌ Ошибка при выборе вида предложения: {e}")
        await callback.answer("❌ Ошибка при выборе вида", show_alert=True)
    await callback.answer()


@dp.message(OfferCardStates.waiting_item_kind)
async def offer_view_redirect(message: Message, state: FSMContext):
    """Перенаправление ввода вида предложения"""
    if message.text:
        await state.set_state(OfferCardStates.waiting_item_kind_input)
        await process_offer_view_input(message, state)


@dp.callback_query(F.data == "off_vw_add")
async def add_offer_view(callback: CallbackQuery, state: FSMContext):
    """Добавление нового вида предложения"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_vw_list"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "➕ **Добавить новый вид предложения**\n\n"
        "Введите название нового вида:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_item_kind_input)
    await callback.answer()


@dp.message(OfferCardStates.waiting_item_kind_input)
async def process_offer_view_input(message: Message, state: FSMContext):
    """Обработка ввода нового вида предложения"""
    item_kind = message.text.strip()
    if not item_kind:
        await message.answer("❌ Название вида не может быть пустым. Введите название:")
        return

    if len(item_kind) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(item_kind=item_kind)

    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = False
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        is_admin = True
        try:
             async with aiosqlite.connect("bot_database.db", timeout=20.0) as db:
                cursor = await db.execute("SELECT 1 FROM offer_views WHERE name = ?", (item_kind,))
                exists = await cursor.fetchone()
                if not exists:
                    await db.execute("INSERT INTO offer_views (name) VALUES (?)", (item_kind,))
                    await db.commit()
                    await message.answer(f"✅ Вид '{item_kind}' автоматически добавлен (права администратора).")
                else:
                    await message.answer(f"⚠️ Вид '{item_kind}' уже существует.")
        except Exception as e:
            await message.answer(f"❌ Ошибка автоматического добавления: {e}")
    else:
        await notify_admin_new_category("kind", item_kind, user_id, username, "offer")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data="continue_after_offer_view"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_vw_list"
    ))
    builder.adjust(1)

    if not is_admin:
        await message.answer(
            f"✅ **Вид '{item_kind}' отправлен на рассмотрение администратору.**\n\n"
            "Администратор проверит и добавит его в систему.\n"
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            "Вы можете продолжить создание заявки.",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "continue_after_offer_view")
async def continue_after_offer_view(callback: CallbackQuery, state: FSMContext):
    """Продолжить после добавления вида предложения"""
    await ask_offer_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "off_vw_skip")
async def skip_offer_view(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора вида предложения"""
    await state.update_data(item_kind="")
    await ask_offer_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_typ")
async def back_to_offer_type(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору типа предложения"""
    await show_offer_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_vw_list")
async def back_to_offer_view_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку видов предложений"""
    await show_offer_view_selection(callback.message, state)
    await callback.answer()


async def ask_offer_catalog_id(message: Message, state: FSMContext):
    """Запрос ID в каталоге предложений"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_off_vw"
    ))
    builder.adjust(1)

    await message.edit_text(
        "📋 **5. ID в Каталоге**\n\n"
        "Введите ID предложения в каталоге (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_catalog_id)


@dp.callback_query(F.data == "back_off_vw")
async def back_to_offer_view(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору вида предложения"""
    await show_offer_view_selection(callback.message, state)
    await callback.answer()


# Далее для предложения используются те же обработчики, что и для товара,
# так как структура карточки предложения идентична товару
# Просто меняем состояние на OfferCardStates

@dp.message(OfferCardStates.waiting_catalog_id)
async def offer_process_catalog_id(message: Message, state: FSMContext):
    """Обработка ID в каталоге предложения (аналогично товару)"""
    catalog_id = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(catalog_id=catalog_id)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_catalog_id"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **6. Название предложения**\n\n"
        "Введите краткое и точное описание (обязательно):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_title)


# Для предложения используем те же самые обработчики, что и для товара,
# но с состояниями OfferCardStates
# Здесь я добавлю только недостающие обработчики для навигации

@dp.callback_query(F.data == "back_to_offer_catalog_id")
async def back_to_offer_catalog_id(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу ID каталога предложения"""
    await ask_offer_catalog_id(callback.message, state)
    await callback.answer()


# Создаем алиасы для обработчиков предложения, использующих те же функции что и товар
# с соответствующими состояниями

@dp.message(OfferCardStates.waiting_title)
async def offer_process_title(message: Message, state: FSMContext):
    """Обработка названия предложения (аналогично товару)"""
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название предложения не может быть пустым. Пожалуйста, введите название:")
        return

    if len(title) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(title=title)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_title"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **7. Назначение и способы использования**\n\n"
        "Для чего предназначено предложение (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_purpose)
@dp.callback_query(F.data == "back_to_offer_title")
async def back_to_offer_title(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу ID каталога предложения"""
    await offer_process_catalog_id(callback.message, state)
    await callback.answer()

# Дальнейшие обработчики для предложения аналогичны товару
# Здесь я просто перечислю основные состояния с комментариями



# Финальный обработчик для сохранения заявки предложения
@dp.message(OfferCardStates.waiting_contact)
async def offer_process_contact(message: Message, state: FSMContext):
    """Обработка контактной информации и сохранение заявки предложения"""
    contact = message.text.strip()
    if not contact:
        await message.answer("❌ Контактная информация не может быть пустой. Пожалуйста, введите контакты:")
        return

    if len(contact) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return

    await state.update_data(contact=contact)

    # Получаем все данные
    data = await state.get_data()

    # Формируем JSON с изображениями
    images_data = {
        "main": data.get("main_photo"),
        "additional": data.get("additional_photos", [])
    }
    import json
    images_json = json.dumps(images_data, ensure_ascii=False)

    # Сохраняем заявку в базу данных (аналогично товару)
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("""
                INSERT INTO order_requests 
                (user_id, operation, item_type, category, item_class, item_type_detail, item_kind,
                 title, purpose, name, creation_date, condition, specifications, 
                 advantages, additional_info, images, price, availability, detailed_specs, 
                 reviews, rating, delivery_info, supplier_info, statistics, deadline, tags, 
                 contact, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.from_user.id,
                data.get('operation', ''),
                'offer',
                data.get('category', ''),
                data.get('item_class', ''),
                data.get('item_type', ''),
                data.get('item_kind', ''),
                data.get('title', ''),
                data.get('purpose', ''),
                data.get('name', ''),
                data.get('creation_date', ''),
                data.get('condition', ''),
                data.get('specifications', ''),
                data.get('advantages', ''),
                data.get('additional_info', ''),
                images_json,
                data.get('price', ''),
                data.get('availability', ''),
                data.get('detailed_specs', ''),
                data.get('reviews', ''),
                data.get('rating', ''),
                data.get('delivery_info', ''),
                data.get('supplier_info', ''),
                data.get('statistics', ''),
                data.get('deadline', ''),
                data.get('tags', ''),
                data.get('contact', ''),
                'active',
                datetime.now().isoformat()
            ))

            # Получаем ID созданной заявки
            new_request_id = cursor.lastrowid
            await db.commit()

            print(f"✅ Заявка предложения создана с ID: {new_request_id} для пользователя {message.from_user.id}")

            # Добавляем заявку в корзину пользователя
            await db.execute("""
                INSERT OR IGNORE INTO cart_order 
                (user_id, item_type, item_id, quantity, price, added_at, source_table)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.from_user.id,
                'предложение',
                new_request_id,
                1,
                data.get('price', '0'),
                datetime.now().isoformat(),
                'order_requests'
            ))
            await db.commit()
            print(f"✅ Заявка предложения {new_request_id} добавлена в корзину пользователя {message.from_user.id}")

            # Синхронизация с Google Sheets
            try:
                from google_sheets import sync_order_requests_to_sheets
                result = await sync_order_requests_to_sheets()
                if result:
                    print(f"✅ Заявка предложения {new_request_id} синхронизирована с Google Sheets")
                else:
                    print(f"⚠️ Заявка предложения {new_request_id} сохранена, но произошла ошибка синхронизации с Google Sheets")
            except Exception as e:
                print(f"❌ Ошибка импорта модуля Google Sheets: {e}")

            await send_order_request_to_admin(message.chat.id, new_request_id, data)

            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="🏠 В личный кабинет", callback_data="personal_account"))
            builder.add(types.InlineKeyboardButton(text="🛒 К заявкам", callback_data="cart_order"))
            builder.adjust(1)

            await message.answer(
                "✅ **Заявка предложения успешно создана!**\n\n"
                f"Заявка №{new_request_id} сохранена и добавлена в вашу корзину.",
                reply_markup=builder.as_markup()
            )

            # Очищаем состояние
            await state.clear()

    except Exception as e:
        print(f"❌ Ошибка при сохранении заявки предложения: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Произошла ошибка при сохранении заявки. Попробуйте еще раз.")

# ========== ОБРАБОТЧИКИ ДЛЯ ПРЕДЛОЖЕНИЯ ==========

@dp.message(OfferCardStates.waiting_purpose)
async def offer_process_purpose(message: Message, state: FSMContext):
    """Обработка назначения предложения"""
    purpose = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(purpose=purpose)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_purpose"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **8. Наименование**\n\n"
        "Полное наименование предложения (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_name)


@dp.callback_query(F.data == "back_to_offer_purpose")
async def back_to_offer_purpose(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу назначения предложения"""
    await ask_offer_catalog_id(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_name)
async def offer_process_name(message: Message, state: FSMContext):
    """Обработка наименования предложения"""
    name = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(name=name)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_name"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **9. Дата создания/выпуска**\n\n"
        "Дата производства или создания предложения (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_creation_date)


@dp.callback_query(F.data == "back_to_offer_name")
async def back_to_offer_name(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу наименования предложения"""
    await offer_process_purpose(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_creation_date)
async def offer_process_creation_date(message: Message, state: FSMContext):
    """Обработка даты создания предложения"""
    creation_date = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(creation_date=creation_date)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_creation_date"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **10. Состояние**\n\n"
        "Новое, б/у, восстановленное и т.д. (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_condition)


@dp.callback_query(F.data == "back_to_offer_creation_date")
async def back_to_offer_creation_date(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу даты создания предложения"""
    await offer_process_name(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_condition)
async def offer_process_condition(message: Message, state: FSMContext):
    """Обработка состояния предложения"""
    condition = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(condition=condition)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_condition"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **11. Эксплуатационные характеристики**\n\n"
        "Ключевые характеристики предложения (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_specifications)


@dp.callback_query(F.data == "back_to_offer_condition")
async def back_to_offer_condition(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу состояния предложения"""
    await offer_process_creation_date(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_specifications)
async def offer_process_specifications(message: Message, state: FSMContext):
    """Обработка характеристик предложения"""
    specifications = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(specifications=specifications)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_specifications"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **12. Преимущества в сравнении с аналогами**\n\n"
        "Почему стоит выбрать это предложение (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_advantages)


@dp.callback_query(F.data == "back_to_offer_specifications")
async def back_to_offer_specifications(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу характеристик предложения"""
    await offer_process_condition(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_advantages)
async def offer_process_advantages(message: Message, state: FSMContext):
    """Обработка преимуществ предложения"""
    advantages = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(advantages=advantages)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_advantages"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **13. Другая важная и полезная информация**\n\n"
        "Любая дополнительная информация (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_additional_info)


@dp.callback_query(F.data == "back_to_offer_advantages")
async def back_to_offer_advantages(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу преимуществ предложения"""
    await offer_process_specifications(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_additional_info)
async def offer_process_additional_info(message: Message, state: FSMContext):
    """Обработка дополнительной информации предложения"""
    additional_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(additional_info=additional_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_additional_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📸 **14. Изображения и/или видео**\n\n"
        "Отправьте **основное фото или видео** предложения (обязательно).\n"
        "Оно будет отображаться на обложке.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_main_photo)


@dp.callback_query(F.data == "back_to_offer_additional_info")
async def back_to_offer_additional_info(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу дополнительной информации предложения"""
    await offer_process_advantages(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_main_photo)
async def offer_process_main_photo(message: Message, state: FSMContext):
    """Обработка основного фото предложения"""
    if not (message.photo or message.video or message.document):
        await message.answer("❌ Пожалуйста, отправьте фото или видео.")
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

    if not file_id:
         await message.answer("❌ Не удалось распознать медиа.")
         return

    main_photo_data = {"type": file_type, "file_id": file_id, "unique_id": unique_id}
    await state.update_data(main_photo=main_photo_data, additional_photos=[])

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить дополнительные", callback_data="skip_offer_add_photos"))
    
    await message.answer(
        "✅ Основное фото сохранено!\n\n"
        "Теперь отправьте **до 3-х дополнительных фото/видео** (по одному или альбомом).\n"
        "Или нажмите кнопку «Пропустить».",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_additional_photos)

@dp.callback_query(F.data == "skip_offer_add_photos", OfferCardStates.waiting_additional_photos)
async def skip_offer_additional_photos(callback: CallbackQuery, state: FSMContext):
    """Пропуск дополнительных фото предложения"""
    await callback.message.edit_text("Дополнительные фото пропущены.")
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_additional_photos"
    ))
    builder.adjust(1)
    
    await callback.message.answer(
        "📋 **15. Цена**\n\n"
        "Актуальная стоимость с учетом текущих скидок и акций (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_price)
    await callback.answer()

@dp.message(OfferCardStates.waiting_additional_photos)
async def offer_process_additional_photos(message: Message, state: FSMContext):
    """Обработка дополнительных фото предложения"""
    if message.text and message.text.lower() in ['готово', 'done', 'skip', '-', 'пропустить']:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_offer_additional_photos"))
        builder.adjust(1)

        await message.answer("Ввод фото завершен.", reply_markup=builder.as_markup())
        await message.answer("📋 **15. Цена**\n\nАктуальная стоимость с учетом текущих скидок и акций (необязательно):\nИли напишите 'пропустить':")
        await state.set_state(OfferCardStates.waiting_price)
        return

    if not (message.photo or message.video or message.document):
        return

    data = await state.get_data()
    additional_photos = data.get("additional_photos", [])
    
    if len(additional_photos) >= 3:
        await message.answer("⚠️ Вы уже загрузили 3 дополнительных фото. Введите стоимость или нажмите 'Пропустить дополнительные'.")
        return

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
             builder = InlineKeyboardBuilder()
             builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_offer_additional_photos")) 
             builder.adjust(1)
             
             await message.answer("✅ Загружено 3 фото.", reply_markup=builder.as_markup())
             await message.answer("📋 **15. Цена**\n\nАктуальная стоимость с учетом текущих скидок и акций (необязательно):\nИли напишите 'пропустить':")
             await state.set_state(OfferCardStates.waiting_price)


@dp.callback_query(F.data == "back_to_offer_images")
async def back_to_offer_images(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу изображений предложения"""
    await offer_process_additional_info(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_price)
async def offer_process_price(message: Message, state: FSMContext):
    """Обработка цены предложения"""
    price = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(price=price)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_price"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **16. Наличие**\n\n"
        "Информация о местонахождении и доступности (в наличии, под заказ, ожидается) (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_availability)


@dp.callback_query(F.data == "back_to_offer_price")
async def back_to_offer_price(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу цены предложения"""
    await offer_process_images(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_availability)
async def offer_process_availability(message: Message, state: FSMContext):
    """Обработка информации о наличии предложения"""
    availability = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(availability=availability)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_availability"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **17. Характеристики**\n\n"
        "Детальные технические характеристики, размеры, материалы и другие параметры (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_detailed_specs)


@dp.callback_query(F.data == "back_to_offer_availability")
async def back_to_offer_availability(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу информации о наличии предложения"""
    await offer_process_price(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_detailed_specs)
async def offer_process_detailed_specs(message: Message, state: FSMContext):
    """Обработка подробных характеристик предложения"""
    detailed_specs = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(detailed_specs=detailed_specs)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_detailed_specs"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **18. Отзывы покупателей и экспертов**\n\n"
        "Мнения и оценки, помогающие сформировать доверие (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_reviews)


@dp.callback_query(F.data == "back_to_offer_detailed_specs")
async def back_to_offer_detailed_specs(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу подробных характеристик предложения"""
    await offer_process_availability(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_reviews)
async def offer_process_reviews(message: Message, state: FSMContext):
    """Обработка отзывов предложения"""
    reviews = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(reviews=reviews)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_reviews"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **19. Рейтинг**\n\n"
        "Общая текущая оценка из 10 звезд (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_rating)


@dp.callback_query(F.data == "back_to_offer_reviews")
async def back_to_offer_reviews(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу отзывов предложения"""
    await offer_process_detailed_specs(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_rating)
async def offer_process_rating(message: Message, state: FSMContext):
    """Обработка рейтинга предложения"""
    rating = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(rating=rating)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_rating"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **20. Информация о доставке и оплате**\n\n"
        "Условия поставки и передачи, способы оплаты, документальное оформление, гарантии (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_delivery_info)


@dp.callback_query(F.data == "back_to_offer_rating")
async def back_to_offer_rating(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу рейтинга предложения"""
    await offer_process_reviews(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_delivery_info)
async def offer_process_delivery_info(message: Message, state: FSMContext):
    """Обработка информации о доставке предложения"""
    delivery_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(delivery_info=delivery_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_delivery_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **21. Поставщик-гарант предложения**\n\n"
        "Реквизиты, данные руководителя и менеджера, лицензии, формы договоров (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_supplier_info)


@dp.callback_query(F.data == "back_to_offer_delivery_info")
async def back_to_offer_delivery_info(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу информации о доставке предложения"""
    await offer_process_rating(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_supplier_info)
async def offer_process_supplier_info(message: Message, state: FSMContext):
    """Обработка информации о поставщике предложения"""
    supplier_info = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(supplier_info=supplier_info)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_supplier_info"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **22. Статистика реализации**\n\n"
        "Данные статистики и иная информация (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_statistics)


@dp.callback_query(F.data == "back_to_offer_supplier_info")
async def back_to_offer_supplier_info(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу информации о поставщике предложения"""
    await offer_process_delivery_info(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_statistics)
async def offer_process_statistics(message: Message, state: FSMContext):
    """Обработка статистики предложения"""
    statistics = "" if message.text.lower() == "пропустить" else message.text
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(statistics=statistics)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_statistics"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **23. Сроки**\n\n"
        "Сроки поставки или выполнения (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_deadline)


@dp.callback_query(F.data == "back_to_offer_statistics")
async def back_to_offer_statistics(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу статистики предложения"""
    await offer_process_supplier_info(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_deadline)
async def offer_process_deadline(message: Message, state: FSMContext):
    """Обработка сроков предложения"""
    deadline = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(deadline=deadline)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_deadline"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **24. Теги/ключевые слова**\n\n"
        "Ключевые слова для поиска (необязательно):\n"
        "Или напишите 'пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_tags)


@dp.callback_query(F.data == "back_to_offer_deadline")
async def back_to_offer_deadline(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу сроков предложения"""
    await offer_process_statistics(callback.message, state)
    await callback.answer()


@dp.message(OfferCardStates.waiting_tags)
async def offer_process_tags(message: Message, state: FSMContext):
    """Обработка тегов предложения"""
    tags = "" if message.text.lower() == "пропустить" else message.text.strip()
    if message.text.lower() != "пропустить" and len(message.text) > 200:
        await message.answer("⚠️ Текст слишком длинный (более 200 символов). Пожалуйста, сократите его.")
        return
    await state.update_data(tags=tags)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_offer_tags"
    ))
    builder.adjust(1)

    await message.answer(
        "📋 **25. Контактная информация**\n\n"
        "Как с вами связаться (телефон, email, Telegram) (обязательно):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OfferCardStates.waiting_contact)


@dp.callback_query(F.data == "back_to_offer_tags")
async def back_to_offer_tags(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу тегов предложения"""
    await offer_process_deadline(callback.message, state)
    await callback.answer()


# ========== КНОПКИ НАЗАД ДЛЯ УСЛУГ ==========

@dp.callback_query(F.data == "back_to_service_works")
async def back_to_service_works(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу перечня работ услуги"""
    await service_process_title(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_materials")
async def back_to_service_materials(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу материалов услуги"""
    await service_process_works(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_images")
async def back_to_service_images(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу изображений услуги"""
    await service_process_materials(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_price")
async def back_to_service_price(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу стоимости услуги"""
    await service_process_images(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_pricing")
async def back_to_service_pricing(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу прайса услуги"""
    await service_process_price(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_guarantees")
async def back_to_service_guarantees(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу гарантий услуги"""
    await service_process_pricing(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_conditions")
async def back_to_service_conditions(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу условий услуги"""
    await service_process_guarantees(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_supplier_info")
async def back_to_service_supplier_info(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу информации о поставщике услуги"""
    await service_process_conditions(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_reviews")
async def back_to_service_reviews(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу отзывов услуги"""
    await service_process_supplier_info(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_rating")
async def back_to_service_rating(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу рейтинга услуги"""
    await service_process_reviews(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_statistics")
async def back_to_service_statistics(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу статистики услуги"""
    await service_process_rating(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_additional_info")
async def back_to_service_additional_info(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу дополнительной информации услуги"""
    await service_process_statistics(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_deadline")
async def back_to_service_deadline(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу сроков услуги"""
    await service_process_additional_info(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_service_tags")
async def back_to_service_tags(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу тегов услуги"""
    await service_process_deadline(callback.message, state)
    await callback.answer()


# ========== ДОПОЛНИТЕЛЬНЫЕ КОЛБЭКИ ДЛЯ ВОЗВРАТА ==========

@dp.callback_query(F.data == "back_serv_cls")
async def back_to_service_class_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку классов услуг"""
    await show_service_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_typ")
async def back_to_service_type_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку типов услуг"""
    await show_service_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_serv_vw")
async def back_to_service_view_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку видов услуг"""
    await show_service_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_cls")
async def back_to_offer_class_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку классов предложений"""
    await show_offer_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_off_typ")
async def back_to_offer_type_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку типов предложений"""
    await show_offer_type_selection(callback.message, state)
    await callback.answer()



# ========== КОЛБЭКИ ДЛЯ ВОЗВРАТА ==========

# Карточка товара
@dp.callback_query(F.data == "back_prod_category")
async def back_prod_category(callback: CallbackQuery, state: FSMContext):
    await show_product_category_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_class")
async def back_prod_class(callback: CallbackQuery, state: FSMContext):
    await show_product_class_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_item_type")
async def back_prod_item_type(callback: CallbackQuery, state: FSMContext):
    await show_product_type_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_prod_item_kind")
async def back_prod_item_kind(callback: CallbackQuery, state: FSMContext):
    await show_product_view_selection(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_catalog_id")
async def back_to_product_catalog_id(callback: CallbackQuery, state: FSMContext):
    await ask_product_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_title")
async def back_to_product_title(callback: CallbackQuery, state: FSMContext):
    await product_process_catalog_id(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_purpose")
async def back_to_product_purpose(callback: CallbackQuery, state: FSMContext):
    await product_process_title(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_name")
async def back_to_product_name(callback: CallbackQuery, state: FSMContext):
    await product_process_purpose(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_creation_date")
async def back_to_product_creation_date(callback: CallbackQuery, state: FSMContext):
    await product_process_name(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_condition")
async def back_to_product_condition(callback: CallbackQuery, state: FSMContext):
    await product_process_creation_date(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_specifications")
async def back_to_product_specifications(callback: CallbackQuery, state: FSMContext):
    await product_process_condition(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_advantages")
async def back_to_product_advantages(callback: CallbackQuery, state: FSMContext):
    await product_process_specifications(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_additional_info")
async def back_to_product_additional_info(callback: CallbackQuery, state: FSMContext):
    await product_process_advantages(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_images")
async def back_to_product_images(callback: CallbackQuery, state: FSMContext):
    await product_process_additional_info(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_price")
async def back_to_product_price(callback: CallbackQuery, state: FSMContext):
    await product_process_images(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_availability")
async def back_to_product_availability(callback: CallbackQuery, state: FSMContext):
    await product_process_price(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_detailed_specs")
async def back_to_product_detailed_specs(callback: CallbackQuery, state: FSMContext):
    await product_process_availability(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_reviews")
async def back_to_product_reviews(callback: CallbackQuery, state: FSMContext):
    await product_process_detailed_specs(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_rating")
async def back_to_product_rating(callback: CallbackQuery, state: FSMContext):
    await product_process_reviews(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_delivery_info")
async def back_to_product_delivery_info(callback: CallbackQuery, state: FSMContext):
    await product_process_rating(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_supplier_info")
async def back_to_product_supplier_info(callback: CallbackQuery, state: FSMContext):
    await product_process_delivery_info(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_statistics")
async def back_to_product_statistics(callback: CallbackQuery, state: FSMContext):
    await product_process_supplier_info(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_deadline")
async def back_to_product_deadline(callback: CallbackQuery, state: FSMContext):
    await product_process_statistics(callback.message, state)
    await callback.answer()


@dp.callback_query(F.data == "back_to_product_tags")
async def back_to_product_tags(callback: CallbackQuery, state: FSMContext):
    await product_process_deadline(callback.message, state)
    await callback.answer()


# Карточка услуги
@dp.callback_query(F.data == "back_serv_cat")
async def back_serv_cat(callback: CallbackQuery, state: FSMContext):
    await show_service_category_selection(callback.message, state)
    await callback.answer()


# Карточка предложения
@dp.callback_query(F.data == "back_off_cat")
async def back_off_cat(callback: CallbackQuery, state: FSMContext):
    await show_offer_category_selection(callback.message, state)
    await callback.answer()