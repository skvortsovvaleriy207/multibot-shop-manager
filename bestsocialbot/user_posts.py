from aiogram import F, types, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp
from db import DB_FILE


router = Router()

# List of all sub-category codes from shop.py to intercept
SUB_CATEGORIES = [
    # Promotions
    "promo_buy_sell", "promo_events", "promo_forecasts", "promo_analytics", "promo_education",
    # News
    "news_thematic", "news_facts", "news_ads", "news_partners", "news_investors",
    "news_announcements", "news_success", "news_reports", "news_reviews", "news_ratings",
    # Popular
    "pop_hits", "pop_trends", "pop_playlists", "pop_cognitive", "pop_entertainment",
    "pop_humor", "pop_reactions", "pop_reviews", "pop_lessons", "pop_stories"
]

@dp.callback_query(lambda c: c.data in SUB_CATEGORIES or c.data.startswith("view_section_"))
async def user_view_section_posts(callback: types.CallbackQuery):
    """Просмотр постов в категории (для пользователей)"""
    
    # Parse data
    if callback.data.startswith("view_section_"):
        # view_section_{sub_category}_{page}
        parts = callback.data.split("_")
        sub_category = "_".join(parts[2:-1])
        page = int(parts[-1])
    else:
        # Direct click from menu
        sub_category = callback.data
        page = 1
        
    async with aiosqlite.connect(DB_FILE) as db:
        # Count total posts
        cursor = await db.execute("SELECT COUNT(*) FROM shop_sections WHERE sub_category = ? AND is_active = 1", (sub_category,))
        total_count = (await cursor.fetchone())[0]
        
        if total_count == 0:
            await callback.answer("😔 В этом разделе пока нет новостей", show_alert=True)
            return
            
        # Get posts for current page (1 per page for better visibility)
        offset = page - 1
        cursor = await db.execute("""
            SELECT id, title, content, image_url, created_at 
            FROM shop_sections 
            WHERE sub_category = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1 OFFSET ?
        """, (sub_category, offset))
        post = await cursor.fetchone()
        
    if not post:
        await callback.answer("❌ Ошибка загрузки поста", show_alert=True)
        return
        
    pid, title, content, image_id, created_at = post
    
    # Text formatting
    text = f"📅 {created_at[:10]}\n\n"
    text += f"**{title}**\n\n"
    text += f"{content}"
    
    # Keyboard
    builder = InlineKeyboardBuilder()
    
    # Navigation
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"view_section_{sub_category}_{page-1}"))
    
    nav_buttons.append(types.InlineKeyboardButton(text=f"{page}/{total_count}", callback_data="noop"))
    
    if page < total_count:
        nav_buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=f"view_section_{sub_category}_{page+1}"))
        
    builder.row(*nav_buttons)
    
    # Comment Button (Link to discussion group)
    # Using a placeholder URL if CHAT_ID is just an ID, ideally needs a link.
    # Check if we have a config for discussion link, otherwise just show button text.
    # Assuming config.py has user_chat_link or similar? Or just put a generic one.
    # For now, let's assume we can link to the group if we knew the username.
    # Instead, we'll make a callback that says "Go to chat"
    
    # builder.row(types.InlineKeyboardButton(text="💬 Комментировать", url="https://t.me/YOUR_CHAT_LINK"))
    # Since I don't have the link, I will use a visual button for now.
    builder.row(types.InlineKeyboardButton(text="💬 Комментировать", callback_data="comment_placeholder"))
    
    # Back button - needs to know where to go back. 
    # Determine parent menu based on prefix
    if sub_category.startswith("promo"):
        back_callback = "promotions_menu"
    elif sub_category.startswith("news"):
        back_callback = "news_menu"
    elif sub_category.startswith("pop"):
        back_callback = "popular_menu"
    else:
        back_callback = "main_shop_page"
        
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback))
    
    try:
        if image_id:
            # Check if current message has media
            if callback.message.content_type == types.ContentType.PHOTO:
                 await callback.message.edit_media(
                    media=types.InputMediaPhoto(media=image_id, caption=text),
                    reply_markup=builder.as_markup()
                )
            else:
                 # Delete and send new if switching from text to photo
                await callback.message.delete()
                await callback.message.answer_photo(image_id, caption=text, reply_markup=builder.as_markup())
        else:
            if callback.message.content_type == types.ContentType.TEXT:
                await callback.message.edit_text(text, reply_markup=builder.as_markup())
            else:
                # Delete and send new if switching from photo to text
                await callback.message.delete()
                await callback.message.answer(text, reply_markup=builder.as_markup())
    except Exception as e:
        print(f"Error showing post: {e}")
        # Fallback
        await callback.message.answer(text, reply_markup=builder.as_markup())
        
    await callback.answer()

@dp.callback_query(F.data == "comment_placeholder")
async def comment_placeholder_handler(callback: types.CallbackQuery):
    await callback.answer("💬 Для комментариев перейдите в чат сообщества", show_alert=True)