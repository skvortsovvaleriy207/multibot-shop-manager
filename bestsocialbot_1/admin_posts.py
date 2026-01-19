from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import aiosqlite
from config import ADMIN_ID
from dispatcher import dp

router = Router()

class PostStates(StatesGroup):
    waiting_title = State()
    waiting_content = State()
    waiting_image = State()

# --- Admin Menu ---

@dp.message(Command("admin_content"))
async def admin_content_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await admin_content_menu(message)

@dp.callback_query(F.data == "admin_content")
async def admin_content_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    await admin_content_menu(callback)

async def admin_content_menu(message_or_callback):
    """Главное меню управления контентом"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🏷️ Акции", callback_data="admin_section_promotion"))
    builder.add(types.InlineKeyboardButton(text="📰 Новости", callback_data="admin_section_news"))
    builder.add(types.InlineKeyboardButton(text="⭐ Популярное", callback_data="admin_section_popular"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")) # Assumes admin_panel exists
    builder.adjust(1)
    
    text = "📢 **Управление контентом**\n\nВыберите раздел:"
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=builder.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup())
        await message_or_callback.answer()

@dp.callback_query(F.data.startswith("admin_section_"))
async def admin_section_select(callback: types.CallbackQuery, state: FSMContext):
    """Выбор раздела (Акции/Новости/Популярное)"""
    section_type = callback.data.split("_")[2] # promotion, news, popular
    await state.update_data(current_section_type=section_type)
    
    # Показываем подкатегории (как в магазине)
    builder = InlineKeyboardBuilder()
    
    if section_type == "promotion":
        buttons = [
            ("📈 Покупки/Продажи", "promo_buy_sell"),
            ("🎉 Мероприятия", "promo_events"),
            ("🔮 Прогнозы/Советы", "promo_forecasts"),
            ("📊 Аналитика", "promo_analytics"),
            ("📚 Образовательные", "promo_education")
        ]
    elif section_type == "news":
        buttons = [
            ("📰 Тематические", "news_thematic"),
            ("💡 Факты/Ситуации", "news_facts"),
            ("📢 Объявления", "news_ads"),
            ("🤝 Новости партнеров", "news_partners"),
            ("💼 Инвесторы", "news_investors"),
            ("📣 Анонсы", "news_announcements"),
            ("🏆 Успехи", "news_success"),
            ("📊 Отчеты", "news_reports"),
            ("💬 Отзывы", "news_reviews"),
            ("⭐ Оценки", "news_ratings")
        ]
    elif section_type == "popular":
        buttons = [
            ("🔥 Хиты", "pop_hits"),
            ("📈 Тренды", "pop_trends"),
            ("🎵 Плейлисты", "pop_playlists"),
            ("🧠 Познавательное", "pop_cognitive"),
            ("🎭 Развлекательное", "pop_entertainment"),
            ("😂 Юмор", "pop_humor"),
            ("😲 Реакции", "pop_reactions"),
            ("📝 Обзоры", "pop_reviews"),
            ("🎓 Уроки", "pop_lessons"),
            ("📖 Истории", "pop_stories")
        ]
    else:
        buttons = []

    for text, code in buttons:
        builder.add(types.InlineKeyboardButton(text=text, callback_data=f"admin_sub_{code}"))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_content_menu"))
    builder.adjust(2)
    
    section_names = {"promotion": "Акции", "news": "Новости", "popular": "Популярное"}
    await callback.message.edit_text(
        f"📂 Раздел: **{section_names.get(section_type, section_type)}**\nВыберите категорию:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("admin_sub_"))
async def admin_subcategory_view(callback: types.CallbackQuery, state: FSMContext):
    """Список постов в подкатегории"""
    sub_category = callback.data.replace("admin_sub_", "")
    await state.update_data(current_sub_category=sub_category)
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT id, title FROM shop_sections 
            WHERE sub_category = ? AND is_active = 1
            ORDER BY id DESC LIMIT 10
        """, (sub_category,))
        posts = await cursor.fetchall()
    
    builder = InlineKeyboardBuilder()
    for pid, title in posts:
        builder.add(types.InlineKeyboardButton(text=f"📝 {title}", callback_data=f"admin_post_view_{pid}"))
    
    builder.add(types.InlineKeyboardButton(text="➕ Создать пост", callback_data="admin_post_create"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад (к разделам)", callback_data=f"admin_content_menu")) # Simplified back for now
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📑 Посты в категории **{sub_category}**:",
        reply_markup=builder.as_markup()
    )

# --- Post Creation ---

@dp.callback_query(F.data == "admin_post_create")
async def admin_post_create_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PostStates.waiting_title)
    await callback.message.answer("✍️ Введите **заголовок** поста:")
    await callback.answer()

@dp.message(PostStates.waiting_title)
async def admin_post_title(message: types.Message, state: FSMContext):
    await state.update_data(post_title=message.text)
    await state.set_state(PostStates.waiting_content)
    await message.answer("📝 Введите **текст** поста:")

@dp.message(PostStates.waiting_content)
async def admin_post_content(message: types.Message, state: FSMContext):
    await state.update_data(post_content=message.text)
    await state.set_state(PostStates.waiting_image)
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Без картинки", callback_data="skip_image"))
    
    await message.answer("🖼️ Отправьте **картинку** для поста (или нажмите кнопку):", reply_markup=builder.as_markup())

@dp.message(PostStates.waiting_image, F.photo)
async def admin_post_image(message: types.Message, state: FSMContext):
    image_id = message.photo[-1].file_id
    await finalize_post_creation(message, state, image_id)

@dp.callback_query(PostStates.waiting_image, F.data == "skip_image")
async def admin_post_skip_image(callback: types.CallbackQuery, state: FSMContext):
    await finalize_post_creation(callback.message, state, None)
    await callback.answer()

async def finalize_post_creation(message: types.Message, state: FSMContext, image_id: str | None):
    data = await state.get_data()
    title = data['post_title']
    content = data['post_content']
    sub_category = data['current_sub_category']
    section_type = data['current_section_type']
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""
            INSERT INTO shop_sections (section_type, sub_category, title, content, image_url, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (section_type, sub_category, title, content, image_id))
        await db.commit()
    
    await state.clear()
    await message.answer(f"✅ Пост **{title}** успешно создан!")
    # Optionally return to menu? For now just stop.

# --- Post Viewing/Deletion ---

@dp.callback_query(F.data.startswith("admin_post_view_"))
async def admin_post_view(callback: types.CallbackQuery):
    post_id = int(callback.data.split("_")[3])
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT title, content, image_url FROM shop_sections WHERE id = ?", (post_id,))
        post = await cursor.fetchone()
        
    if not post:
        await callback.answer("❌ Пост не найден", show_alert=True)
        return
        
    title, content, image_id = post
    text = f"**{title}**\n\n{content}"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_post_delete_{post_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Скрыть", callback_data="delete_message"))
    
    if image_id:
        await callback.message.answer_photo(image_id, caption=text, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_post_delete_"))
async def admin_post_delete(callback: types.CallbackQuery):
    post_id = int(callback.data.split("_")[3])
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("UPDATE shop_sections SET is_active = 0 WHERE id = ?", (post_id,))
        await db.commit()
        
    await callback.answer("🗑️ Пост удален", show_alert=True)
    await callback.message.delete()
