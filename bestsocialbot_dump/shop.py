from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from config import ADMIN_ID
from db import check_channel_subscription
from dispatcher import dp
from datetime import *
from survey import SURVEY_QUESTIONS
from utils import check_blocked_user
from captcha import send_captcha, CaptchaStates, process_captcha_selection
from aiogram.fsm.context import FSMContext
from cart import cart_order_start
from google_sheets import sync_from_sheets_to_db

SHOWCASE_TEXT = "ДОБРО ПОЖАЛОВАТЬ В ЧАТ-БОТ СООБЩЕСТВА!"


async def check_survey_completed(user_id: int) -> bool:
    """Проверка, прошел ли пользователь опрос"""
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(
            "SELECT has_completed_survey FROM users WHERE user_id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        return user and user[0]

@dp.callback_query(F.data == "shop")
async def shop_access(callback: CallbackQuery, state: FSMContext):
    """Обработка входа в магазин с капчей"""
    if await check_blocked_user(callback):
        return
    await sync_from_sheets_to_db()

    user_id = callback.from_user.id

    # Проверяем, прошел ли пользователь опрос
    if not await check_survey_completed(user_id):
        await callback.answer("Для доступа к магазину необходимо пройти опрос.", show_alert=True)
        return

    # Проверяем, прошла ли уже капча
    data = await state.get_data()
    if not data.get("shop_captcha_passed"):
        await send_captcha(callback.message, state)
        await state.update_data(shop_captcha_pending=True, shop_captcha_callback_id=callback.id)
        return

    # После успешной капчи показываем главную страницу магазина
    await main_shop_page(callback)


@dp.callback_query(F.data == "main_shop_page")
async def main_shop_page(callback: CallbackQuery):
    """Главная страница магазина (первый экран после входа)"""
    if await check_blocked_user(callback):
        return
    await sync_from_sheets_to_db()
    user_id = callback.from_user.id
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(
            "SELECT has_completed_survey FROM users WHERE user_id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        if not user or not user[0]:
            await callback.answer("Для доступа к магазину необходимо пройти опрос.", show_alert=True)
            return


    builder = InlineKeyboardBuilder()

    # Основные разделы магазина
    builder.add(types.InlineKeyboardButton(text="📦 Каталоги", callback_data="all_catalogs"))
    builder.add(types.InlineKeyboardButton(text="🏷️ Акции", callback_data="soon"))
    builder.add(types.InlineKeyboardButton(text="⭐ Популярное", callback_data="soon"))
    builder.add(types.InlineKeyboardButton(text="🆕 Новинки", callback_data="soon"))
    builder.add(types.InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_account"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="shop_back_to_showcase"))
    builder.adjust(2,1,1,1,2,1,1)

    await callback.message.edit_text(

        "ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН СООБЩЕСТВА!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "all_catalogs")
async def all_catalogs(callback: CallbackQuery):
    """Назад из магазина на главный экран (опрос/магазин) без проверок"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📦 Каталог товаров", callback_data="product_catalog"))
    builder.add(types.InlineKeyboardButton(text="🛠 Каталог услуг", callback_data="service_catalog"))
    builder.add(types.InlineKeyboardButton(text="🤝 Каталог предложений", callback_data="property_catalog"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
    builder.adjust(2, 1, 1)

    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=SHOWCASE_TEXT,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=SHOWCASE_TEXT,
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "shop_back_to_showcase")
async def shop_back_to_showcase(callback: CallbackQuery):
    """Назад из магазина на главный экран (опрос/магазин) без проверок"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📝 Опрос", callback_data="survey"))
    builder.add(types.InlineKeyboardButton(text="🏪 Магазин", callback_data="shop"))
    builder.adjust(2)

    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=SHOWCASE_TEXT,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=SHOWCASE_TEXT,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "soon")
async def soon(callback: CallbackQuery):
    await callback.answer("будет скоро", show_alert=False)

@dp.callback_query(F.data == "personal_account")
async def personal_account(callback: CallbackQuery):
    """Личный кабинет - доступен из главной страницы магазина"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    is_admin = user_id == ADMIN_ID

    builder = InlineKeyboardBuilder()

    # Основные кнопки личного кабинета
    builder.add(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"))
    builder.add(types.InlineKeyboardButton(text="📋 Создать заявку", callback_data="create_order"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина заявок", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders"))
    builder.add(types.InlineKeyboardButton(text="📦 Заказы на мои товары", callback_data="seller_orders"))
    builder.add(types.InlineKeyboardButton(text="🔗 Рефералы", callback_data="referral_system"))
    builder.add(types.InlineKeyboardButton(text="💳 Оплата", callback_data="payment"))
    builder.add(types.InlineKeyboardButton(text="💬 Сообщения", callback_data="messages"))

    if is_admin:
        builder.add(types.InlineKeyboardButton(text="🔧 Админ-панель", callback_data="admin_panel"))



    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))


    if is_admin:
        builder.adjust(1, 1, 2, 2, 1, 1, 1)
    else:
        builder.adjust(1, 1, 2, 2, 1, 1)

    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption="👤 **Личный кабинет**\n\n"
                    "Выберите действие:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="👤 **Личный кабинет**\n\n"
                 "Выберите действие:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    await sync_from_sheets_to_db()


    user_id = callback.from_user.id

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(
            "SELECT username, first_name, last_name, created_at, full_name FROM users WHERE user_id = ?",
            (user_id,)
        )
        user_data = await cursor.fetchone()

        cursor = await db.execute(
            """
            SELECT 
                survey_date, full_name, birth_date, location, email, phone, employment,
                financial_problem, social_problem, ecological_problem, passive_subscriber,
                active_partner, investor_trader, business_proposal
            FROM users 
            WHERE user_id = ?
            """,
            (user_id,)
        )
        answers = await cursor.fetchall()

        cursor = await db.execute(
            "SELECT current_balance FROM user_bonuses WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id,)
        )
        balance = await cursor.fetchone()

    full_name_answer = answers[0][1] if answers and answers[0][1] else 'Не указано'

    profile_text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Никнейм: {user_data[0] or 'Не указано'}\n"
        f"📝 ФИО: {full_name_answer or 'Не указано'}\n"
        f"📅 Дата регистрации: {(datetime.fromisoformat(user_data[3]).strftime('%d.%m.%Y %H:%M') if isinstance(user_data[3], str) else 'Не указано')}\n"
        f"💰 Текущий баланс бонусов: {balance[0] if balance else 0} монет\n\n"
        f"📊 **Ваши ответы на опрос:**\n"
    )

    if answers:
        profile_text += f"\n📅 {SURVEY_QUESTIONS[1]}\n{answers[0][0] or 'Не указано'}\n"
        profile_text += f"\n👤 {SURVEY_QUESTIONS[3]}\n{user_data[0] or 'Не указано'}\n"
        profile_text += f"\n📝 {SURVEY_QUESTIONS[4]}\n{answers[0][1] or 'Не указано'}\n"
        profile_text += f"\n🎂 {SURVEY_QUESTIONS[5]}\n{answers[0][2] or 'Не указано'}\n"
        profile_text += f"\n📍 {SURVEY_QUESTIONS[6]}\n{answers[0][3] or 'Не указано'}\n"
        profile_text += f"\n📧 {SURVEY_QUESTIONS[7]}\n{answers[0][4] or 'Не указано'}\n"
        profile_text += f"\n📱 {SURVEY_QUESTIONS[8]}\n{answers[0][5] or 'Не указано'}\n"
        profile_text += f"\n💼 {SURVEY_QUESTIONS[9]}\n{answers[0][6] or 'Не указано'}\n"
        profile_text += f"\n💰 {SURVEY_QUESTIONS[10]}\n{answers[0][7] or 'Не указано'}\n"
        profile_text += f"\n👥 {SURVEY_QUESTIONS[11]}\n{answers[0][8] or 'Не указано'}\n"
        profile_text += f"\n🌱 {SURVEY_QUESTIONS[12]}\n{answers[0][9] or 'Не указано'}\n"
        profile_text += f"\n👀 {SURVEY_QUESTIONS[13]}\n{answers[0][10] or 'Не указано'}\n"
        profile_text += f"\n🤝 {SURVEY_QUESTIONS[14]}\n{answers[0][11] or 'Не указано'}\n"
        profile_text += f"\n📈 {SURVEY_QUESTIONS[15]}\n{answers[0][12] or 'Не указано'}\n"
        profile_text += f"\n💼 {SURVEY_QUESTIONS[16]}\n{answers[0][13] or 'Не указано'}\n"

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)

    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=profile_text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=profile_text,
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "back_to_personal_account")
async def back_to_personal_account(callback: CallbackQuery):
    """Назад из профиля в личный кабинет"""
    user_id = callback.from_user.id
    is_admin = user_id == ADMIN_ID

    builder = InlineKeyboardBuilder()

    # Основные кнопки личного кабинета
    builder.add(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"))
    builder.add(types.InlineKeyboardButton(text="📋 Создать заявку", callback_data="create_order"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина заявок", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders"))
    builder.add(types.InlineKeyboardButton(text="📦 Заказы на мои товары", callback_data="seller_orders"))
    builder.add(types.InlineKeyboardButton(text="🔗 Рефералы", callback_data="referral_system"))
    builder.add(types.InlineKeyboardButton(text="💳 Оплата", callback_data="payment"))
    builder.add(types.InlineKeyboardButton(text="💬 Сообщения", callback_data="messages"))

    if is_admin:
        builder.add(types.InlineKeyboardButton(text="🔧 Админ-панель", callback_data="admin_panel"))

    # Кнопка НАЗАД ведет в главную страницу магазина
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))

    # Оптимальное расположение кнопок
    if is_admin:
        builder.adjust(1, 1, 2, 2, 1, 1, 1)
    else:
        builder.adjust(1, 1, 2, 2, 1, 1)

    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption="👤 **Личный кабинет**\n\n"
                    "Выберите действие:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="👤 **Личный кабинет**\n\n"
                 "Выберите действие:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "product_catalog")
async def product_catalog(callback: CallbackQuery):
    """Каталог товаров с подразделами - публичный доступ"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()

    # Получаем категории товаров из БД из таблицы product_purposes
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT name FROM product_purposes
        """)
        categories = await cursor.fetchall()

    if categories:
        for cat_name in categories:
            builder.add(types.InlineKeyboardButton(
                text=f"📦 {cat_name[0]}",
                callback_data=f"product_cat_{cat_name[0]}"
            ))
    else:
        builder.add(types.InlineKeyboardButton(
            text="📦 Пока нет категорий",
            callback_data="empty"
        ))

    builder.add(types.InlineKeyboardButton(text="📋 Карточка товара", callback_data="product_card_form"))
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data="search_in_products"))
    if callback.message.chat.id == ADMIN_ID:
        builder.add(types.InlineKeyboardButton(text="📦 Изменить каталог товаров", callback_data="product_catalog_change"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="all_catalogs"))

    # Оптимальное расположение: категории по 2 в строке, затем одиночные кнопки
    if categories:
        builder.adjust(2, 2, 2, 1, 1)  # Категории по 2, затем 2 одиночные кнопки
    else:
        builder.adjust(1, 1, 1)  # Все кнопки по одной

    await callback.message.edit_text(
        "📦 **Каталог товаров**\n\n"
        "Выберите категорию:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "service_catalog")
async def service_catalog(callback: CallbackQuery):
    """Каталог услуг - публичный доступ"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()

    # Получаем категории услуг из таблицы service_purposes
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT name FROM service_purposes
        """)
        categories = await cursor.fetchall()

    if categories:
        for cat_name in categories:
            builder.add(types.InlineKeyboardButton(
                text=f"🛠 {cat_name[0]}",
                callback_data=f"service_cat_{cat_name[0]}"
            ))
    else:
        builder.add(types.InlineKeyboardButton(
            text="🛠 Пока нет категорий",
            callback_data="empty"
        ))

    builder.add(types.InlineKeyboardButton(text="📋 Карточка услуги", callback_data="service_card_form"))
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data="search_in_services"))
    if callback.message.chat.id == ADMIN_ID:
        builder.add(types.InlineKeyboardButton(text="🛠 Изменить каталог услуг", callback_data="service_catalog_change"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="all_catalogs"))

    # Оптимальное расположение
    if categories:
        builder.adjust(2, 2, 2, 1, 1)  # Категории по 2, затем 2 одиночные кнопки
    else:
        builder.adjust(1, 1, 1)  # Все кнопки по одной

    await callback.message.edit_text(
        "🛠 **Каталог услуг**\n\n"
        "Выберите категориу:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "property_catalog")
async def property_catalog(callback: CallbackQuery):
    """Каталог предложений/активов - публичный доступ"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()

    # Получаем категории предложений из таблицы property_purposes
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT name FROM property_purposes
        """)
        categories = await cursor.fetchall()

    if categories:
        for cat_name in categories:
            builder.add(types.InlineKeyboardButton(
                text=f"🤝 {cat_name[0]}",
                callback_data=f"property_cat_{cat_name[0]}"
            ))
    else:
        builder.add(types.InlineKeyboardButton(
            text="🤝 Пока нет категорий",
            callback_data="empty"
        ))

    builder.add(types.InlineKeyboardButton(text="📋 Карточка предложения", callback_data="offer_card_form"))
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data="search_in_offers"))
    if callback.message.chat.id == ADMIN_ID:
        builder.add(types.InlineKeyboardButton(text="📋 Изменить каталог предложений/активов", callback_data="property_catalog_change"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="all_catalogs"))

    # Оптимальное расположение
    if categories:
        builder.adjust(2, 2, 2, 1, 1)  # Категории по 2, затем 2 одиночные кнопки
    else:
        builder.adjust(1, 1, 1)  # Все кнопки по одной

    await callback.message.edit_text(
        "🤝 **Каталог предложений/активов**\n\n"
        "Выберите категорию:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# Обработчики для просмотра товаров в категории
@dp.callback_query(F.data.startswith("product_cat_"))
async def show_product_category_items(callback: CallbackQuery):
    """Показать товары в выбранной категории"""
    if await check_blocked_user(callback):
        return

    category_name = callback.data.replace("product_cat_", "")

    # Получаем товары из этой категории из таблицы order_requests
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, additional_info 
            FROM order_requests 
            WHERE item_type = 'product' AND category = ?
            AND status IN ('active', 'approved')
            ORDER BY created_at DESC
        """, (category_name,))
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if items:
        response = f"📦 **Товары в категории: {category_name}**\n\n"
        for item_id, title, price, additional_info in items:
            # Используем additional_info как описание (вместо description)
            description = additional_info
            short_desc = description[:100] + "..." if description and len(description) > 100 else description or ""
            response += f"🆔 {item_id}: {title}\n"
            if price:
                response += f"💰 Цена: {price}\n"
            if short_desc:
                response += f"📝 {short_desc}\n"
            response += "────\n"

            # Добавляем кнопку для добавления в корзину
            builder.add(types.InlineKeyboardButton(
                text=f"➕ {title[:15]}",
                callback_data=f"add_to_cart_product_{item_id}"
            ))
    else:
        response = f"📦 **Товары в категории: {category_name}**\n\n"
        response += "В этой категории пока нет товаров.\n"
        builder.add(types.InlineKeyboardButton(
            text="📋 Создать заявку на товар",
            callback_data="product_card_form"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="product_catalog"))

    # Оптимальное расположение: товары по 2 в строке, затем кнопка назад
    if items:
        builder.adjust(2, 2, 2, 1)  # Товары по 2, затем кнопка назад
    else:
        builder.adjust(1, 1)  # Обе кнопки по одной

    await callback.message.edit_text(
        response,
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("service_cat_"))
async def show_service_category_items(callback: CallbackQuery):
    """Показать услуги в выбранной категории"""
    if await check_blocked_user(callback):
        return

    category_name = callback.data.replace("service_cat_", "")

    # Получаем услуги из этой категории из таблицы order_requests
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, additional_info 
            FROM service_orders 
            WHERE item_type = 'service' AND category = ?
            AND status IN ('active', 'approved')
            ORDER BY created_at DESC
        """, (category_name,))
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if items:
        response = f"🛠 **Услуги в категории: {category_name}**\n\n"
        for item_id, title, price, additional_info in items:
            # Используем additional_info как описание
            description = additional_info
            short_desc = description[:100] + "..." if description and len(description) > 100 else description or ""
            response += f"🆔 {item_id}: {title}\n"
            if price:
                response += f"💰 Цена: {price}\n"
            if short_desc:
                response += f"📝 {short_desc}\n"
            response += "────\n"

            builder.add(types.InlineKeyboardButton(
                text=f"➕ {title[:15]}",
                callback_data=f"add_to_cart_service_{item_id}"
            ))
    else:
        response = f"🛠 **Услуги в категории: {category_name}**\n\n"
        response += "В этой категории пока нет услуг.\n"
        builder.add(types.InlineKeyboardButton(
            text="📋 Создать заявку на услугу",
            callback_data="service_card_form"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="service_catalog"))

    # Оптимальное расположение
    if items:
        builder.adjust(2, 2, 2, 1)  # Услуги по 2, затем кнопка назад
    else:
        builder.adjust(1, 1)  # Обе кнопки по одной

    await callback.message.edit_text(
        response,
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("property_cat_"))
async def show_property_category_items(callback: CallbackQuery):
    """Показать предложения в выбранной категории"""
    if await check_blocked_user(callback):
        return

    category_name = callback.data.replace("property_cat_", "")

    # Получаем предложения из этой категории из таблицы order_requests
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title, price, additional_info 
            FROM order_requests 
            WHERE item_type = 'offer' AND category = ?
            AND status IN ('active', 'approved')
            ORDER BY created_at DESC
        """, (category_name,))
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if items:
        response = f"🤝 **Предложения в категории: {category_name}**\n\n"
        for item_id, title, price, additional_info in items:
            # Используем additional_info как описание
            description = additional_info
            short_desc = description[:100] + "..." if description and len(description) > 100 else description or ""
            response += f"🆔 {item_id}: {title}\n"
            if price:
                response += f"💰 Цена: {price}\n"
            if short_desc:
                response += f"📝 {short_desc}\n"
            response += "────\n"

            builder.add(types.InlineKeyboardButton(
                text=f"➕ {title[:15]}",
                callback_data=f"add_to_cart_offer_{item_id}"
            ))
    else:
        response = f"🤝 **Предложения в категории: {category_name}**\n\n"
        response += "В этой категории пока нет предложений.\n"
        builder.add(types.InlineKeyboardButton(
            text="📋 Создать заявку на предложение",
            callback_data="offer_card_form"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="property_catalog"))

    # Оптимальное расположение
    if items:
        builder.adjust(2, 2, 2, 1)  # Предложения по 2, затем кнопка назад
    else:
        builder.adjust(1, 1)  # Обе кнопки по одной

    await callback.message.edit_text(
        response,
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_showcase")
async def back_to_showcase(callback: CallbackQuery):
    """Назад на главный экран (опрос/магазин)"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📝 Опрос", callback_data="survey"))
    builder.add(types.InlineKeyboardButton(text="🏪 Магазин", callback_data="main_shop_page"))
    builder.adjust(2)

    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=SHOWCASE_TEXT,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=SHOWCASE_TEXT,
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "empty")
async def empty_category(callback: CallbackQuery):
    await callback.answer("В данной категории пока нет товаров/услуг.", show_alert=True)