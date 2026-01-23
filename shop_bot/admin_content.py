
from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp
from utils import check_blocked_user
from config import ADMIN_ID
import logging

class ContentStates(StatesGroup):
    waiting_category_name = State()
    waiting_post_title = State()
    waiting_post_text = State()
    waiting_post_media = State()
    confirm_delete = State()

@dp.callback_query(F.data == "manage_content")
async def manage_content_menu(callback: CallbackQuery):
    """Admin Menu: Content Management"""
    if await check_blocked_user(callback):
        return
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access Denied", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📰 Новости", callback_data="content_root:news"))
    builder.add(types.InlineKeyboardButton(text="🏷️ Акции", callback_data="content_root:promotions"))
    builder.add(types.InlineKeyboardButton(text="⭐ Популярное", callback_data="content_root:popular"))
    builder.add(types.InlineKeyboardButton(text="🆕 Новинки", callback_data="content_root:new_items"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel_menu"))
    builder.adjust(2, 2, 1)

    await callback.message.edit_text(
        "📝 **Управление контентом**\n\nВыберите раздел для редактирования:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("content_root:"))
async def content_root_view(callback: CallbackQuery):
    """View Categories in a Root Section"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    c_type = callback.data.split(":")[1]
    
    cat_names = {
        'news': 'Новости',
        'promotions': 'Акции',
        'popular': 'Популярное',
        'new_items': 'Новинки'
    }

    async with aiosqlite.connect("bot_database.db") as db:
        # Get root categories for this type (or the root category itself if it exists?)
        # My seeding created a Root Category for each type with parent_id=NULL
        # So I should find that root ID first to list its children?
        # OR just list children of that root ID.
        
        cursor = await db.execute("SELECT id FROM categories WHERE catalog_type = ? AND parent_id IS NULL LIMIT 1", (c_type,))
        row = await cursor.fetchone()
        
        if not row:
            await callback.answer("Root category not found!", show_alert=True)
            return
        
        root_id = row[0]
        await show_category_contents(callback, root_id, c_type)

async def show_category_contents(callback: CallbackQuery, category_id: int, catalog_type: str):
    """Show subcategories and posts within a category"""
    async with aiosqlite.connect("bot_database.db") as db:
        # Get subcategories
        cursor = await db.execute("SELECT id, name FROM categories WHERE parent_id = ? ORDER BY name", (category_id,))
        subcats = await cursor.fetchall()
        
        # Get posts
        cursor = await db.execute("SELECT id, title FROM shop_posts WHERE category_id = ? AND is_active = 1", (category_id,))
        posts = await cursor.fetchall()

        # Get parent info for generic "Back" button
        cursor = await db.execute("SELECT parent_id, name FROM categories WHERE id = ?", (category_id,))
        cat_info = await cursor.fetchone()
        parent_id = cat_info[0] if cat_info else None
        cat_name = cat_info[1] if cat_info else "Section"
        
    builder = InlineKeyboardBuilder()

    # Subcategories
    for sid, sname in subcats:
        builder.add(types.InlineKeyboardButton(text=f"📁 {sname}", callback_data=f"view_cat:{sid}:{catalog_type}"))
        builder.add(types.InlineKeyboardButton(text="✏️", callback_data=f"edit_cat:{sid}"))
        builder.add(types.InlineKeyboardButton(text="❌", callback_data=f"del_cat:{sid}"))

    # Posts (if any)
    for pid, ptitle in posts:
        builder.add(types.InlineKeyboardButton(text=f"📄 {ptitle}", callback_data=f"view_post:{pid}"))
        builder.add(types.InlineKeyboardButton(text="✏️", callback_data=f"edit_post:{pid}"))
        builder.add(types.InlineKeyboardButton(text="❌", callback_data=f"del_post:{pid}"))

    # Action Buttons
    builder.add(types.InlineKeyboardButton(text="➕ Папку", callback_data=f"add_cat:{category_id}"))
    builder.add(types.InlineKeyboardButton(text="➕ Пост", callback_data=f"add_post:{category_id}"))
    
    # Back Button
    if parent_id:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"view_cat:{parent_id}:{catalog_type}"))
    else:
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="manage_content"))

    # Layout: 3 columns for items (View, Edit, Delete), 2 for actions, 1 for back
    # Adjust logic based on item counts...
    # Generic simple adjust:
    # Subcats: [Name] [Edit] [Del]
    # Posts: [Name] [Edit] [Del]
    
    current_adjust = [3] * (len(subcats) + len(posts))
    current_adjust.extend([2, 1]) # Add buttons + Back
    
    builder.adjust(*current_adjust)

    txt = f"📂 **{cat_name}**\n\nРазделы и материалы:"
    if not subcats and not posts:
        txt += "\n_(Пусто)_"

    await callback.message.edit_text(txt, reply_markup=builder.as_markup())
    
# Handler for viewing a category
@dp.callback_query(F.data.startswith("view_cat:"))
async def view_category_handler(callback: CallbackQuery):
    _, cat_id, c_type = callback.data.split(":")
    await show_category_contents(callback, int(cat_id), c_type)

# ---- Category Management Handlers ----

@dp.callback_query(F.data.startswith("add_cat:"))
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    parent_id = int(callback.data.split(":")[1])
    await state.update_data(parent_id=parent_id, action="add_cat")
    await callback.message.answer("Введите название новой категории/папки/раздела:")
    await state.set_state(ContentStates.waiting_category_name)
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_cat:"))
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id, action="edit_cat")
    await callback.message.answer("Введите новое название категории:")
    await state.set_state(ContentStates.waiting_category_name)
    await callback.answer()

@dp.callback_query(F.data.startswith("del_cat:"))
async def delete_category_start(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    async with aiosqlite.connect("bot_database.db") as db:
        # Check for children
        cursor = await db.execute("SELECT COUNT(*) FROM categories WHERE parent_id = ?", (cat_id,))
        count_c = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM shop_posts WHERE category_id = ?", (cat_id,))
        count_p = (await cursor.fetchone())[0]
    
    if count_c > 0 or count_p > 0:
        await callback.answer("Нельзя удалить: категория не пуста!", show_alert=True)
        return

    # Delete
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        await db.commit()
    
    await callback.answer("Удалено!", show_alert=True)
    # Refresh logic similar to investmentsbot
    pass

@dp.message(ContentStates.waiting_category_name)
async def category_name_submitted(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    name = message.text
    
    async with aiosqlite.connect("bot_database.db") as db:
        if action == "add_cat":
            parent_id = data.get("parent_id")
            # Get catalog_type from parent
            cursor = await db.execute("SELECT catalog_type FROM categories WHERE id = ?", (parent_id,))
            res = await cursor.fetchone()
            if not res:
                await message.answer("Ошибка: родительская категория не найдена.")
                await state.clear()
                return
            c_type = res[0]
            
            await db.execute("INSERT INTO categories (catalog_type, name, parent_id, created_at) VALUES (?, ?, ?, datetime('now'))", 
                             (c_type, name, parent_id))
            await db.commit()
            await message.answer(f"Категория '{name}' создана.")
            
        elif action == "edit_cat":
            cat_id = data.get("cat_id")
            await db.execute("UPDATE categories SET name = ? WHERE id = ?", (name, cat_id))
            await db.commit()
            await message.answer(f"Категория переименована в '{name}'.")

    await state.clear()

# ---- Post Management Handlers ----

@dp.callback_query(F.data.startswith("add_post:"))
async def add_post_start(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id, action="add_post")
    await callback.message.answer("Введите заголовок поста:")
    await state.set_state(ContentStates.waiting_post_title)
    await callback.answer()

@dp.message(ContentStates.waiting_post_title)
async def post_title_submitted(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите текст поста:")
    await state.set_state(ContentStates.waiting_post_text)

@dp.message(ContentStates.waiting_post_text)
async def post_text_submitted(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Отправьте фото/видео (или напишите 'нет'/'skip' чтобы пропустить):")
    await state.set_state(ContentStates.waiting_post_media)

@dp.message(ContentStates.waiting_post_media)
async def post_media_submitted(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("cat_id")
    title = data.get("title")
    text = data.get("text")
    
    media_id = None
    media_type = None

    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.video:
        media_id = message.video.file_id
        media_type = "video"
    elif message.document:
        media_id = message.document.file_id
        media_type = "document"
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""
            INSERT INTO shop_posts (category_id, title, content_text, media_file_id, media_type)
            VALUES (?, ?, ?, ?, ?)
        """, (cat_id, title, text, media_id, media_type))
        await db.commit()
    
    
    # Get catalog_type for the back button
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT catalog_type FROM categories WHERE id = ?", (cat_id,))
        row = await cursor.fetchone()
        c_type = row[0] if row else "news" # Fallback
        
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Вернуться в категорию", callback_data=f"view_cat:{cat_id}:{c_type}"))
    
    await message.answer("Пост сохранен!", reply_markup=builder.as_markup())
    await state.clear()

@dp.callback_query(F.data.startswith("del_post:"))
async def delete_post_handler(callback: CallbackQuery):
    pid = int(callback.data.split(":")[1])
    async with aiosqlite.connect("bot_database.db") as db:
        # Get parent id first
        cursor = await db.execute("SELECT category_id, media_type FROM shop_posts WHERE id = ?", (pid,))
        row = await cursor.fetchone()
        if not row:
            await callback.answer("Пост не найден", show_alert=True)
            return
        cat_id = row[0]
        
        await db.execute("DELETE FROM shop_posts WHERE id = ?", (pid,))
        await db.commit()
    
    await callback.answer("Пост удален")
    async with aiosqlite.connect("bot_database.db") as db:
         cursor = await db.execute("SELECT catalog_type FROM categories WHERE id = ?", (cat_id,))
         row = await cursor.fetchone()
         c_type = row[0]
    
    await show_category_contents(callback, cat_id, c_type)

@dp.callback_query(F.data.startswith("view_post:"))
async def view_post_handler(callback: CallbackQuery):
    pid = int(callback.data.split(":")[1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT title, content_text, media_file_id, media_type FROM shop_posts WHERE id = ?", (pid,))
        row = await cursor.fetchone()
        if not row:
            await callback.answer("Пост не найден", show_alert=True)
            return
        
        title, content, mid, mtype = row
        
        txt = f"**{title}**\n\n{content}"
        
        if mid:
            if mtype == 'photo':
                await callback.message.answer_photo(mid, caption=txt)
            elif mtype == 'video':
                await callback.message.answer_video(mid, caption=txt)
            else:
                await callback.message.answer_document(mid, caption=txt)
        else:
            await callback.message.answer(txt)
            
    await callback.answer()
