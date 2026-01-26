from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from config import ADMIN_ID, HOUSING_CATEGORIES
from db import check_channel_subscription, DB_FILE
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
    async with aiosqlite.connect(DB_FILE) as db:
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

    # await sync_from_sheets_to_db() # Disabled to prevent lag/crashing

    user_id = callback.from_user.id
    is_admin = user_id == ADMIN_ID

    builder = InlineKeyboardBuilder()

    # Основные разделы магазина
    builder.add(types.InlineKeyboardButton(text="📦 Каталоги", callback_data="all_catalogs"))
    builder.add(types.InlineKeyboardButton(text="🏷️ Акции", callback_data="promotions_menu"))
    builder.add(types.InlineKeyboardButton(text="📰 Новости", callback_data="news_menu"))
    builder.add(types.InlineKeyboardButton(text="⭐ Популярное", callback_data="popular_menu"))
    builder.add(types.InlineKeyboardButton(text="🆕 Новинки", callback_data="new_items"))
    builder.add(types.InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_account"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="exit_shop_menu"))
    builder.adjust(2, 2, 2, 1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(
            text="ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН СООБЩЕСТВА!",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН СООБЩЕСТВА!",
            reply_markup=builder.as_markup()
        )
    try:
        await callback.answer()
    except Exception:
        pass


# --- Dynamic Content Handlers ---

async def show_dynamic_root(callback: CallbackQuery, catalog_type: str):
    """Show root categories for a dynamic section"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Get root items (parent_id is NULL)
        cursor = await db.execute(
            "SELECT id, name FROM categories WHERE catalog_type = ? AND parent_id IS NULL", 
            (catalog_type,)
        )
        root = await cursor.fetchone()
        
        if not root:
             await callback.answer("Раздел пуст 🤷‍♂️", show_alert=True)
             return
             
        root_id, root_name = root
        await show_dynamic_category(callback, root_id, catalog_type)

async def show_dynamic_category(callback: CallbackQuery, category_id: int, catalog_type: str):
    """Show contents of a category (subcategories and posts)"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Get category name and parent
        cursor = await db.execute("SELECT name, parent_id FROM categories WHERE id = ?", (category_id,))
        cat_info = await cursor.fetchone()
        if not cat_info:
             await callback.answer("Категория не найдена", show_alert=True)
             return
        cat_name, parent_id = cat_info

        # Get subcategories
        cursor = await db.execute("SELECT id, name FROM categories WHERE parent_id = ? ORDER BY name", (category_id,))
        subcats = await cursor.fetchall()
        
        # Get posts
        cursor = await db.execute("SELECT id, title FROM shop_posts WHERE category_id = ? AND is_active = 1", (category_id,))
        posts = await cursor.fetchall()
    
    builder = InlineKeyboardBuilder()
    
    # Icon Mapping
    ICONS = {
        # Promotions
        "Покупки/Продажи": "📈",
        "Мероприятия": "🎉",
        "Прогнозы/Советы": "🔮",
        "Аналитика": "📊",
        "Образовательные материалы": "📚",
        
        # News
        "Тематические новости": "📰",
        "Факты/Ситуации": "💡",
        "Объявления": "📢",
        "Новости партнеров": "🤝",
        "Новости инвесторов": "💼",
        "Анонсы товаров/услуг": "📣",
        "Успехи": "🏆",
        "Отчеты": "📊",
        "Отзывы": "💬",
        "Оценки": "⭐",
        
        # Popular
        "Хиты контента": "🔥",
        "Тренды заявок": "📈",
        "Плейлисты": "🎵",
        "Познавательное": "🧠",
        "Развлекательное": "🎭",
        "Юмор-шоу": "😂",
        "Реакции": "😲",
        "Обзоры": "📝",
        "Уроки": "🎓",
        "Истории успехов": "📖"
    }

    # Subcategories
    for sid, sname in subcats:
        icon = ICONS.get(sname, "📁")
        builder.add(types.InlineKeyboardButton(text=f"{icon} {sname}", callback_data=f"shop_cat:{sid}"))
    
    # Posts
    for pid, ptitle in posts:
        builder.add(types.InlineKeyboardButton(text=f"📄 {ptitle}", callback_data=f"shop_post:{pid}"))

    # Back Button
    if parent_id:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"shop_cat:{parent_id}"))
    else:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))

    builder.adjust(1)
    
    txt = f"📂 **{cat_name}**\n\nВыберите раздел или материал:"
    if not subcats and not posts:
        txt = f"📂 **{cat_name}**\n\n_(В этом разделе пока пусто)_"
        
    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(txt, reply_markup=builder.as_markup())
    else:
         await callback.message.edit_caption(caption=txt, reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data.startswith("shop_cat:"))
async def shop_cat_handler(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    # Need to know type? We can fetch it, but show_dynamic_category just needs ID
    await show_dynamic_category(callback, cat_id, "unknown")

@dp.callback_query(F.data.startswith("shop_post:"))
async def shop_post_handler(callback: CallbackQuery):
    pid = int(callback.data.split(":")[1])
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT title, content_text, media_file_id, media_type, category_id FROM shop_posts WHERE id = ?", (pid,))
        row = await cursor.fetchone()
        if not row:
            await callback.answer("Пост не найден", show_alert=True)
            return
        
        title, content, mid, mtype, cat_id = row
        
        txt = f"**{title}**\n\n{content}"
        
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"shop_cat:{cat_id}"))
        
        # If sending new media, we delete old message and send new one? 
        # Or edit if possible? We can't edit media type easily causing mess.
        # Best to send new message if media present, or edit if text only.
        
        if mid:
            await callback.message.delete()
            if mtype == 'photo':
                await callback.message.answer_photo(mid, caption=txt, reply_markup=builder.as_markup())
            elif mtype == 'video':
                await callback.message.answer_video(mid, caption=txt, reply_markup=builder.as_markup())
            else:
                await callback.message.answer_document(mid, caption=txt, reply_markup=builder.as_markup())
        else:
            if callback.message.content_type == types.ContentType.TEXT:
                 await callback.message.edit_text(txt, reply_markup=builder.as_markup())
            else:
                 # If previous was photo, we can't edit to text only easily without leaving photo?
                 # Actually edit_caption works. But if we want to remove photo?
                 # Standard practice: text menus use edit_text. 
                 # If showing content, we might want to delete and send fresh to show media properly.
                 await callback.message.delete()
                 await callback.message.answer(txt, reply_markup=builder.as_markup())
                 
    await callback.answer()

@dp.callback_query(F.data == "promotions_menu")
async def promotions_menu(callback: CallbackQuery):
    """Меню Акции (Динамическое)"""
    await show_dynamic_root(callback, "promotions")

@dp.callback_query(F.data == "news_menu")
async def news_menu(callback: CallbackQuery):
    """Меню Новости (Динамическое)"""
    await show_dynamic_root(callback, "news")

@dp.callback_query(F.data == "popular_menu")
async def popular_menu(callback: CallbackQuery):
    """Меню Популярное (Динамическое)"""
    await show_dynamic_root(callback, "popular")

# Stub for legacy buttons to avoid crashes if users click old buttons
@dp.callback_query(F.data.in_({"promo_buy_sell", "promo_events", "promo_forecasts", "promo_analytics", "promo_education",
                               "news_thematic", "news_facts", "news_ads", "news_partners", "news_investors",
                               "news_announcements", "news_success", "news_reports", "news_reviews", "news_ratings",
                               "pop_hits", "pop_trends", "pop_playlists", "pop_cognitive", "pop_entertainment",
                               "pop_humor", "pop_reactions", "pop_reviews", "pop_lessons", "pop_stories"}))
async def section_stub(callback: CallbackQuery):
    await callback.answer("Этот раздел был обновлен. Пожалуйста, вернитесь в главное меню.", show_alert=True)

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
    try:
        await callback.answer()
    except Exception:
        pass


@dp.callback_query(F.data == "exit_shop_menu")
async def exit_shop_menu_handler(callback: CallbackQuery):
    print(f"DEBUG: exit_shop_menu_handler triggered by {callback.from_user.id}")
    """Назад из магазина на главный экран (опрос/магазин) без проверок"""
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
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "soon")
async def soon(callback: CallbackQuery):
    await callback.answer("будет скоро", show_alert=False)

@dp.callback_query(F.data == "personal_account")
async def personal_account(callback: CallbackQuery):
    """Личный кабинет - доступен из главной страницы магазина"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    # Проверяем, прошел ли пользователь опрос (на случай прямого вызова или обхода)
    if not await check_survey_completed(user_id):
        await callback.answer("Для доступа к личному кабинету необходимо пройти опрос.", show_alert=True)
        return
    
    is_admin = user_id == ADMIN_ID

    builder = InlineKeyboardBuilder()

    # Основные кнопки личного кабинета
    builder.add(types.InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"))
    builder.add(types.InlineKeyboardButton(text="📋 Создать заявку", callback_data="create_order"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_from_account"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина заявок", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders"))
    builder.add(types.InlineKeyboardButton(text="📦 Заказы на мои товары", callback_data="seller_orders"))

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
    try:
        await callback.answer()
    except Exception:
        pass


@dp.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT username, first_name, last_name, created_at, full_name, user_status FROM users WHERE user_id = ?",
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

    if not user_data:
        await callback.answer("Профиль не найден. Пожалуйста, пройдите опрос.", show_alert=True)
        return

    full_name_answer = answers[0][1] if answers and answers[0][1] else 'Не указано'

    profile_text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Никнейм: {user_data[0] or 'Не указано'}\n"
        f"📝 ФИО: {full_name_answer or 'Не указано'}\n"
        f"📅 Дата регистрации: {(datetime.fromisoformat(user_data[3]).strftime('%d.%m.%Y %H:%M') if isinstance(user_data[3], str) else 'Не указано')}\n"
        f"💰 Текущий баланс бонусов: {balance[0] if balance else 0} монет\n"
        f"🔰 Статус: {user_data[5] or 'Не указан'}\n\n"
        f"📊 **Ваши ответы на опрос:**\n"
    )

    if answers:
        profile_text += f"\n📅 Дата прохождения\n{answers[0][0] or 'Не указано'}\n"
        profile_text += f"\n👤 {SURVEY_QUESTIONS[3]}\n{user_data[0] or 'Не указано'}\n"
        profile_text += f"\n📝 {SURVEY_QUESTIONS[4]}\n{answers[0][1] or 'Не указано'}\n"
        profile_text += f"\n📍 {SURVEY_QUESTIONS[6]}\n{answers[0][3] or 'Не указано'}\n"
        profile_text += f"\n📧 {SURVEY_QUESTIONS[7]}\n{answers[0][4] or 'Не указано'}\n"
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
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_from_account"))
    builder.add(types.InlineKeyboardButton(text="🛒 Корзина заявок", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders"))
    builder.add(types.InlineKeyboardButton(text="📦 Заказы на мои товары", callback_data="seller_orders"))

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
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT name FROM product_purposes
        """)
        categories = await cursor.fetchall()

    if categories:
        for cat_name in categories:
            if cat_name[0] in HOUSING_CATEGORIES:
                continue
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
    # if callback.message.chat.id == ADMIN_ID:
    #     builder.add(types.InlineKeyboardButton(text="📦 Изменить каталог товаров", callback_data="manage_product_cats"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))

    # Оптимальное расположение: категории по 2 в строке, затем одиночные кнопки
    if categories:
        builder.adjust(2, 2, 2, 1, 1)  # Категории по 2, затем 2 одиночные кнопки
    else:
        builder.adjust(1, 1, 1)  # Все кнопки по одной

    text = "📦 **Каталог товаров**\n\nВыберите категорию:"
    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_caption(
            caption=text,
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
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT name FROM service_purposes
        """)
        categories = await cursor.fetchall()

    if categories:
        for cat_name in categories:
            if cat_name[0] in HOUSING_CATEGORIES:
                continue
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
    # if callback.message.chat.id == ADMIN_ID:
    #     builder.add(types.InlineKeyboardButton(text="🛠 Изменить каталог услуг", callback_data="manage_service_cats"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))

    # Оптимальное расположение
    if categories:
        builder.adjust(2, 2, 2, 1, 1)  # Категории по 2, затем 2 одиночные кнопки
    else:
        builder.adjust(1, 1, 1)  # Все кнопки по одной

    text = "🛠 **Каталог услуг**\n\nВыберите категорию:"
    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "property_catalog")
async def property_catalog(callback: CallbackQuery):
    """Каталог предложений/активов - публичный доступ"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()

    # Получаем категории предложений из БД
    async with aiosqlite.connect(DB_FILE) as db:
        # Получаем категории из таблицы categories
        cursor = await db.execute("""
            SELECT name FROM categories 
            WHERE catalog_type = 'offer'
            ORDER BY name
        """)
        categories = await cursor.fetchall()

    if categories:
        for cat_name in categories:
            builder.add(types.InlineKeyboardButton(
                text=f"🤝 {cat_name[0]}",
                callback_data=f"pc_{cat_name[0]}"
            ))
    else:
        builder.add(types.InlineKeyboardButton(
            text="🤝 Пока нет категорий",
            callback_data="empty"
        ))

    # Новое меню согласно ТЗ: 3 кнопки
    builder.add(types.InlineKeyboardButton(text="🔍 Поиск в Каталоге предложений", callback_data="search_in_offers"))
    builder.add(types.InlineKeyboardButton(text="📋 Карточка предложений/Заявка", callback_data="offer_card_form"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="all_catalogs"))

    # Оптимальное расположение: категории по 2, затем функциональные кнопки
    if categories:
        builder.adjust(2, 2, 2, 1, 1, 1) # Примерно, если категорий много
        # Более точная настройка: сначала категории по 2, потом 3 кнопки по 1
        sizes = [2] * ((len(categories) + 1) // 2) + [1, 1, 1]
        builder.adjust(*sizes)
    else:
        builder.adjust(1, 1, 1, 1)

    text = "🤝 **Каталог предложений/активов**\n\nВыберите категорию или действие:"
    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_caption(
            caption=text,
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
    async with aiosqlite.connect(DB_FILE) as db:
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

            # Добавляем кнопки: Просмотр и В корзину
            builder.add(types.InlineKeyboardButton(
                text=f"👁 {title[:15]}",
                callback_data=f"item_req_product_{item_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text="➕ В корзину",
                callback_data=f"add_to_cart_product_{item_id}"
            ))
    else:
        response = f"📦 **Товары в категории: {category_name}**\n\n"
        response += "В этой категории пока нет товаров.\n"
        builder.add(types.InlineKeyboardButton(
            text="📋 Создать заявку на товар",
            callback_data=f"product_card_form|{category_name}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="product_catalog"))

    # Оптимальное расположение: (Просмотр, В корзину) - по 2 в строке, затем назад
    if items:
        # Создаем массив размеров строк: [2, 2, 2...] для каждой пары кнопок
        row_sizes = [2] * len(items)
        row_sizes.append(1) # Кнопка назад
        builder.adjust(*row_sizes)
    else:
        builder.adjust(1, 1)  # Обе кнопки по одной

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_caption(
            caption=response,
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
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT id, title, price, additional_info 
            FROM order_requests 
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

            # Добавляем кнопки: Просмотр и В корзину
            builder.add(types.InlineKeyboardButton(
                text=f"👁 {title[:15]}",
                callback_data=f"item_req_service_{item_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text="➕ В корзину",
                callback_data=f"add_to_cart_service_{item_id}"
            ))
    else:
        response = f"🛠 **Услуги в категории: {category_name}**\n\n"
        response += "В этой категории пока нет услуг.\n"
        builder.add(types.InlineKeyboardButton(
            text="📋 Создать заявку на услугу",
            callback_data=f"service_card_form|{category_name}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="service_catalog"))

    # Оптимальное расположение: (Просмотр, В корзину)
    if items:
        row_sizes = [2] * len(items)
        row_sizes.append(1)
        builder.adjust(*row_sizes)
    else:
        builder.adjust(1, 1)  # Обе кнопки по одной

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_caption(
            caption=response,
            reply_markup=builder.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("pc_"))
async def show_property_category_items(callback: CallbackQuery):
    """Показать предложения в выбранной категории"""
    if await check_blocked_user(callback):
        return

    category_name = callback.data.replace("pc_", "")

    # Получаем предложения из этой категории из таблицы order_requests
    async with aiosqlite.connect(DB_FILE) as db:
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
                text="👁 Просмотр",
                callback_data=f"view_item_offer_{item_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text=f"➕ {title[:15]}",
                callback_data=f"add_to_cart_offer_{item_id}"
            ))
    else:
        response = f"🤝 **Предложения в категории: {category_name}**\n\n"
        response += "В этой категории пока нет предложений.\n"
        builder.add(types.InlineKeyboardButton(
            text="📋 Создать карточку предложения",
            callback_data=f"offer_card_form|{category_name}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="property_catalog"))

    # Оптимальное расположение
    if items:
        builder.adjust(2)  # По 2 кнопки в ряд (Просмотр + Добавить)
    else:
        builder.adjust(1, 1)  # Обе кнопки по одной

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=builder.as_markup())
    else:
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

@dp.callback_query(F.data == "new_items")
async def new_items_menu(callback: CallbackQuery):
    """Меню раздела Новинки"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📦 Новые товары", callback_data="new_products"))
    builder.add(types.InlineKeyboardButton(text="🛠 Новые услуги", callback_data="new_services"))
    builder.add(types.InlineKeyboardButton(text="🤝 Новые предложения", callback_data="new_offers"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
    builder.adjust(1) # Все кнопки в один столбик

    await callback.message.edit_text(
        "🆕 **Раздел «Новинки»**\n\n"
        "Выберите интересующий раздел:",
        reply_markup=builder.as_markup()
    )
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "new_products")
async def show_new_products(callback: CallbackQuery):
    """Показать 10 последних добавленных товаров"""
    if await check_blocked_user(callback):
        return

    async with aiosqlite.connect(DB_FILE) as db:
        # Берем из order_requests
        cursor = await db.execute("""
            SELECT id, title, price 
            FROM order_requests 
            WHERE item_type = 'product' AND status IN ('active', 'approved')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if items:
        response = "🆕 **Новые товары**\n\nПоследние поступления:\n\n"
        for item_id, title, price in items:
            price_text = f"{price}₽" if price else "Цена не указана"
            builder.add(types.InlineKeyboardButton(
                text=f"{title[:20]}.. - {price_text}",
                callback_data=f"item_req_product_{item_id}_new"
            ))
    else:
        response = "🆕 **Новые товары**\n\nТоваров пока нет."
        builder.add(types.InlineKeyboardButton(text="Пока пусто", callback_data="empty"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="new_items"))
    builder.adjust(1)

    try:
        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            response,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "new_services")
async def show_new_services(callback: CallbackQuery):
    """Показать 10 последних добавленных услуг"""
    if await check_blocked_user(callback):
        return

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT id, title, price 
            FROM order_requests 
            WHERE item_type = 'service' AND status IN ('active', 'approved')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if items:
        response = "🆕 **Новые услуги**\n\nПоследние добавленные услуги:\n\n"
        for item_id, title, price in items:
            price_text = f"{price}₽" if price else "Цена не указана"
            builder.add(types.InlineKeyboardButton(
                text=f"{title[:20]}.. - {price_text}",
                callback_data=f"item_req_service_{item_id}_new"
            ))
    else:
        response = "🆕 **Новые услуги**\n\nУслуг пока нет."
        builder.add(types.InlineKeyboardButton(text="Пока пусто", callback_data="empty"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="new_items"))
    builder.adjust(1)

    try:
        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            response,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "new_offers")
async def show_new_offers(callback: CallbackQuery):
    """Показать 10 последних предложений"""
    if await check_blocked_user(callback):
        return

    async with aiosqlite.connect(DB_FILE) as db:
        # Для предложений используем order_requests
        cursor = await db.execute("""
            SELECT id, title, price 
            FROM order_requests 
            WHERE item_type = 'offer' AND status IN ('active', 'approved')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        items = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if items:
        response = "🆕 **Новые предложения**\n\nПоследние добавленные предложения:\n\n"
        for item_id, title, price in items:
            price_text = f"{price}₽" if price else "?"
            builder.add(types.InlineKeyboardButton(
                text=f"{title[:20]}.. - {price_text}",
                callback_data=f"item_offer_{item_id}"
            ))
    else:
        response = "🆕 **Новые предложения**\n\nПредложений пока нет."
        builder.add(types.InlineKeyboardButton(text="Пока пусто", callback_data="empty"))

    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="new_items"))
    builder.adjust(1)

    try:
        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            response,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data.startswith("item_req_product_"))
async def show_req_product_details(callback: CallbackQuery):
    """Показать детали товара (из order_requests)"""
    if await check_blocked_user(callback):
        return

    parts = callback.data.split("_")
    # Format: item_req_product_{id}_new
    # parts: ['item', 'req', 'product', '123', 'new']
    try:
        item_id = int(parts[3])
    except:
        item_id = int(parts[2]) # Fallback

    is_new = "new" in parts

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT title, additional_info, price, category, contact, user_id, images
            FROM order_requests 
            WHERE id = ?
        """, (item_id,))
        item = await cursor.fetchone()

    if not item:
        await callback.answer("Товар не найден", show_alert=True)
        return

    title, description, price, category, contact, user_id, images_json = item
    
    username = None
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        user_row = await cursor.fetchone()
        if user_row:
            username = user_row[0]

    text = f"📦 **{title}**\n\n"
    text += f"Категория: {category or 'Общее'}\n"
    text += f"Цена: {price if price else 'Цена не указана'}\n\n"
    text += f"{description}\n\n"
    
    if contact:
        text += f"📞 Контакт: {contact}\n"
    if username:
        text += f"👤 Продавец: @{username}\n"

    # Images
    import json
    images = []
    try:
        if images_json:
            images_list = json.loads(images_json)
            if isinstance(images_list, list) and images_list:
               images = images_list
            elif isinstance(images_list, dict):
               if images_list.get('main'):
                   images.append(images_list['main'].get('file_id'))
    except:
        pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_to_cart_product_{item_id}"))
    
    if is_new:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад к новинкам", callback_data="new_products"))
    else:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
        
    builder.adjust(1)
    
    try:
        await callback.message.delete()
    except:
        pass
        
    if images and isinstance(images[0], str):
        try:
             await callback.message.answer_photo(
                 photo=images[0],
                 caption=text[:1024],
                 reply_markup=builder.as_markup()
             )
        except Exception as e:
             await callback.message.answer(text, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(text, reply_markup=builder.as_markup())
        
    await callback.answer()

@dp.callback_query(F.data.startswith("item_req_service_"))
async def show_req_service_details(callback: CallbackQuery):
    """Показать детали услуги (из order_requests)"""
    if await check_blocked_user(callback):
        return

    parts = callback.data.split("_")
    try:
        item_id = int(parts[3])
    except:
        item_id = int(parts[2]) 

    is_new = "new" in parts

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT title, additional_info, price, category, contact, user_id, images
            FROM order_requests 
            WHERE id = ?
        """, (item_id,))
        item = await cursor.fetchone()

    if not item:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    title, description, price, category, contact, user_id, images_json = item
    
    username = None
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        user_row = await cursor.fetchone()
        if user_row:
            username = user_row[0]

    text = f"🛠 **{title}**\n\n"
    text += f"Категория: {category or 'Общее'}\n"
    text += f"Цена: {price if price else 'Цена не указана'}\n\n"
    text += f"{description}\n\n"
    
    if contact:
        text += f"📞 Контакт: {contact}\n"
    if username:
        text += f"👤 Исполнитель: @{username}\n"

    import json
    images = []
    try:
        if images_json:
            images_list = json.loads(images_json)
            if isinstance(images_list, list) and images_list:
               images = images_list
            elif isinstance(images_list, dict):
               if images_list.get('main'):
                   images.append(images_list['main'].get('file_id'))
    except:
        pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_to_cart_service_{item_id}"))
    
    if is_new:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад к новинкам", callback_data="new_services"))
    else:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_shop_page"))
        
    builder.adjust(1)
    
    try:
        await callback.message.delete()
    except:
        pass
        
    if images and isinstance(images[0], str):
        try:
             await callback.message.answer_photo(
                 photo=images[0],
                 caption=text[:1024],
                 reply_markup=builder.as_markup()
             )
        except Exception as e:
             await callback.message.answer(text, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(text, reply_markup=builder.as_markup())
        
    await callback.answer()

@dp.callback_query(F.data.startswith("item_offer_"))
async def show_offer_details(callback: CallbackQuery):
    """Показать детали предложения (из order_requests)"""
    if await check_blocked_user(callback):
        return

    item_id = int(callback.data.split("_")[-1])

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT title, additional_info, price, category, contact, user_id, images
            FROM order_requests 
            WHERE id = ?
        """, (item_id,))
        item = await cursor.fetchone()

    if not item:
        await callback.answer("Предложение не найдено", show_alert=True)
        return

    title, description, price, category, contact, user_id, images_json = item
    
    # Пытаемся получить username
    username = None
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        user_row = await cursor.fetchone()
        if user_row:
            username = user_row[0]

    text = f"🤝 **{title}**\n\n"
    text += f"Категория: {category or 'Общее'}\n"
    text += f"Цена: {price if price else 'Договорная'}\n\n"
    text += f"{description}\n\n"
    
    if contact:
        text += f"📞 Контакт: {contact}\n"
    if username:
        text += f"👤 Пользователь: @{username}\n"

    # Обработка изображений (если есть)
    import json
    images = []
    try:
        if images_json:
            images_list = json.loads(images_json)
            # Формат может быть разный, допустим это список file_id или dict
            # В admin_order_processing сохраняется как JSON, но структура зависит от source
            # В order_requests images часто сохранялись как list of strings
            if isinstance(images_list, list) and images_list:
               images = images_list
            elif isinstance(images_list, dict):
               # Если формат {main: ..., additional: ...}
               if images_list.get('main'):
                   images.append(images_list['main'].get('file_id'))
    except:
        pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_to_cart_offer_{item_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к списку", callback_data="new_offers"))
    builder.adjust(1)
    
    # Удаляем старое сообщение чтобы прислать новое с фото если есть
    try:
        await callback.message.delete()
    except:
        pass
        
    if images and isinstance(images[0], str):
        # Отправляем с фото
        try:
             await callback.message.answer_photo(
                 photo=images[0],
                 caption=text[:1024], # Ограничение caption
                 reply_markup=builder.as_markup()
             )
        except Exception as e:
             # Если ошибка (например не тот file_id), шлем текст
             print(f"Error sending photo for offer: {e}")
             await callback.message.answer(text, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(text, reply_markup=builder.as_markup())
        
    await callback.answer()