from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user

class ReviewStates(StatesGroup):
    RATING = State()
    REVIEW_TEXT = State()

# Добавление отзыва
@dp.callback_query(F.data.startswith("add_review_"))
async def add_review_start(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    item_type = parts[2]  # tech или service
    item_id = int(parts[3])
    
    await state.update_data(item_type=item_type, item_id=item_id)
    
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.add(types.InlineKeyboardButton(text=f"⭐ {i}", callback_data=f"rating_{i}"))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Отмена", callback_data=f"item_{item_type}_{item_id}"))
    builder.adjust(5, 5, 1)
    
    await callback.message.edit_text(
        "⭐ **Оценка товара/услуги**\n\n"
        "Поставьте оценку от 1 до 10 звезд:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ReviewStates.RATING)
    await callback.answer()

@dp.callback_query(F.data.startswith("rating_"), ReviewStates.RATING)
async def add_review_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_review_text"))
    
    await callback.message.edit_text(
        f"⭐ **Оценка: {rating}/10**\n\n"
        "Напишите отзыв о товаре/услуге или нажмите 'Пропустить':",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ReviewStates.REVIEW_TEXT)
    await callback.answer()

@dp.message(ReviewStates.REVIEW_TEXT)
async def add_review_text(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(review_text=message.text)
    await finish_review(message, state)

@dp.callback_query(F.data == "skip_review_text", ReviewStates.REVIEW_TEXT)
async def skip_review_text(callback: CallbackQuery, state: FSMContext):
    await state.update_data(review_text="")
    await finish_review(callback.message, state)
    await callback.answer()

async def finish_review(message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        # Проверяем, не оставлял ли пользователь уже отзыв
        cursor = await db.execute(
            "SELECT id FROM reviews WHERE item_type = ? AND item_id = ? AND user_id = ?",
            (data['item_type'], data['item_id'], user_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            await message.answer("❌ Вы уже оставляли отзыв на этот товар/услугу.")
            await state.clear()
            return
        
        # Добавляем отзыв
        await db.execute(
            "INSERT INTO reviews (item_type, item_id, user_id, rating, review_text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (data['item_type'], data['item_id'], user_id, data['rating'], data.get('review_text', ''), datetime.now().isoformat())
        )
        
        # Обновляем средний рейтинг товара/услуги
        cursor = await db.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE item_type = ? AND item_id = ?",
            (data['item_type'], data['item_id'])
        )
        avg_rating, count = await cursor.fetchone()
        
        table_name = "auto_products" if data['item_type'] == 'tech' else "auto_services"
        await db.execute(
            f"UPDATE {table_name} SET rating = ?, reviews_count = ? WHERE id = ?",
            (round(avg_rating, 1), count, data['item_id'])
        )
        
        await db.commit()
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ К товару", callback_data=f"item_{data['item_type']}_{data['item_id']}"))
    
    await message.answer(
        f"✅ **Отзыв добавлен!**\n\n"
        f"Ваша оценка: {data['rating']}/10\n"
        f"Средний рейтинг обновлен.",
        reply_markup=builder.as_markup()
    )
    await state.clear()

# Просмотр отзывов
@dp.callback_query(F.data.startswith("view_reviews_"))
async def view_reviews(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    
    parts = callback.data.split("_")
    item_type = parts[2]
    item_id = int(parts[3])
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT r.rating, r.review_text, r.created_at, u.username
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.item_type = ? AND r.item_id = ?
            ORDER BY r.created_at DESC
            LIMIT 10
        """, (item_type, item_id))
        
        reviews = await cursor.fetchall()
        
        # Получаем средний рейтинг
        cursor = await db.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE item_type = ? AND item_id = ?",
            (item_type, item_id)
        )
        avg_rating, count = await cursor.fetchone()
    
    if not reviews:
        text = "📝 **Отзывы**\n\nПока нет отзывов об этом товаре/услуге."
    else:
        text = f"📝 **Отзывы ({count})**\n\n"
        text += f"⭐ Средний рейтинг: {round(avg_rating, 1)}/10\n\n"
        
        for rating, review_text, created_at, username in reviews:
            stars = "⭐" * rating
            text += f"{stars} {rating}/10\n"
            text += f"👤 @{username}\n"
            if review_text:
                text += f"💬 {review_text}\n"
            text += f"📅 {created_at[:10]}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="➕ Добавить отзыв", callback_data=f"add_review_{item_type}_{item_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ К товару", callback_data=f"item_{item_type}_{item_id}"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()