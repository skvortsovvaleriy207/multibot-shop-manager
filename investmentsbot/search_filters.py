from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
from dispatcher import dp
from utils import check_blocked_user

class SearchStates(StatesGroup):
    SEARCH_PRODUCTS = State()
    SEARCH_SERVICES = State()
    FILTER_PRICE_MIN = State()
    FILTER_PRICE_MAX = State()

# Поиск товаров
@dp.callback_query(F.data == "search_products")
async def search_products_start(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return
    
    await callback.message.edit_text(
        "🔍 **Поиск автотехники**\n\n"
        "Введите ключевые слова для поиска:\n"
        "• Марка автомобиля\n"
        "• Модель\n"
        "• Год выпуска\n"
        "• Любые другие характеристики"
    )
    await state.set_state(SearchStates.SEARCH_PRODUCTS)
    await callback.answer()

@dp.message(SearchStates.SEARCH_PRODUCTS)
async def search_products_process(message: Message, state: FSMContext):
    search_query = message.text.lower()
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT ap.id, ap.title, ap.price, ap.description, ap.specifications, 
                   u.username, ac.name as category_name
            FROM auto_products ap
            JOIN users u ON ap.user_id = u.user_id
            JOIN auto_categories ac ON ap.category_id = ac.id
            WHERE ap.status = 'active' AND (
                LOWER(ap.title) LIKE ? OR 
                LOWER(ap.description) LIKE ? OR 
                LOWER(ap.specifications) LIKE ?
            )
            ORDER BY ap.created_at DESC
            LIMIT 20
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        
        results = await cursor.fetchall()
    
    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_products"))
        builder.add(types.InlineKeyboardButton(text="◀️ К каталогу", callback_data="products"))
        
        await message.answer(
            f"🔍 **Поиск: '{search_query}'**\n\n"
            "❌ Ничего не найдено.\n\n"
            "Попробуйте изменить запрос или просмотрите каталог.",
            reply_markup=builder.as_markup()
        )
        await state.clear()
        return
    
    text = f"🔍 **Результаты поиска: '{search_query}'**\n\n"
    text += f"Найдено: {len(results)} товаров\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for item_id, title, price, description, specs, username, category in results[:10]:
        price_text = f"{price}₽" if price else "Цена не указана"
        button_text = f"{title[:25]}... - {price_text}"
        builder.add(types.InlineKeyboardButton(
            text=button_text, 
            callback_data=f"item_tech_{item_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_products"))
    builder.add(types.InlineKeyboardButton(text="◀️ К каталогу", callback_data="products"))
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()

# Поиск услуг
@dp.callback_query(F.data == "search_services")
async def search_services_start(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return
    
    await callback.message.edit_text(
        "🔍 **Поиск автоуслуг**\n\n"
        "Введите ключевые слова для поиска:\n"
        "• Тип услуги\n"
        "• Название сервиса\n"
        "• Местоположение\n"
        "• Любые другие параметры"
    )
    await state.set_state(SearchStates.SEARCH_SERVICES)
    await callback.answer()

@dp.message(SearchStates.SEARCH_SERVICES)
async def search_services_process(message: Message, state: FSMContext):
    search_query = message.text.lower()
    
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT as_.id, as_.title, as_.price, as_.description, as_.location,
                   u.username, ac.name as category_name
            FROM auto_services as_
            JOIN users u ON as_.user_id = u.user_id
            JOIN auto_categories ac ON as_.category_id = ac.id
            WHERE as_.status = 'active' AND (
                LOWER(as_.title) LIKE ? OR 
                LOWER(as_.description) LIKE ? OR 
                LOWER(as_.location) LIKE ?
            )
            ORDER BY as_.created_at DESC
            LIMIT 20
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        
        results = await cursor.fetchall()
    
    if not results:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_services"))
        builder.add(types.InlineKeyboardButton(text="◀️ К каталогу", callback_data="services"))
        
        await message.answer(
            f"🔍 **Поиск: '{search_query}'**\n\n"
            "❌ Ничего не найдено.\n\n"
            "Попробуйте изменить запрос или просмотрите каталог.",
            reply_markup=builder.as_markup()
        )
        await state.clear()
        return
    
    text = f"🔍 **Результаты поиска: '{search_query}'**\n\n"
    text += f"Найдено: {len(results)} услуг\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for item_id, title, price, description, location, username, category in results[:10]:
        price_text = f"{price}₽" if price else "Цена не указана"
        button_text = f"{title[:25]}... - {price_text}"
        builder.add(types.InlineKeyboardButton(
            text=button_text, 
            callback_data=f"item_service_{item_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_services"))
    builder.add(types.InlineKeyboardButton(text="◀️ К каталогу", callback_data="services"))
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()

# Фильтр по цене для товаров
@dp.callback_query(F.data.startswith("filter_price_"))
async def filter_by_price(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return
    
    filter_type = callback.data.split("_")[2]  # products или services
    await state.update_data(filter_type=filter_type)
    
    await callback.message.edit_text(
        "💰 **Фильтр по цене**\n\n"
        "Введите минимальную цену в рублях:"
    )
    await state.set_state(SearchStates.FILTER_PRICE_MIN)
    await callback.answer()

@dp.message(SearchStates.FILTER_PRICE_MIN)
async def filter_price_min(message: Message, state: FSMContext):
    try:
        min_price = float(message.text.replace(",", "."))
        await state.update_data(min_price=min_price)
        
        await message.answer(
            "💰 **Фильтр по цене**\n\n"
            f"Минимальная цена: {min_price}₽\n\n"
            "Введите максимальную цену в рублях:"
        )
        await state.set_state(SearchStates.FILTER_PRICE_MAX)
    except ValueError:
        await message.answer("❌ Введите корректную цену (число)")

@dp.message(SearchStates.FILTER_PRICE_MAX)
async def filter_price_max(message: Message, state: FSMContext):
    try:
        max_price = float(message.text.replace(",", "."))
        data = await state.get_data()
        min_price = data['min_price']
        filter_type = data['filter_type']
        
        if max_price < min_price:
            await message.answer("❌ Максимальная цена не может быть меньше минимальной")
            return
        
        # Выполняем поиск по цене
        async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
            if filter_type == 'products':
                cursor = await db.execute("""
                    SELECT ap.id, ap.title, ap.price, u.username, ac.name as category_name
                    FROM auto_products ap
                    JOIN users u ON ap.user_id = u.user_id
                    JOIN auto_categories ac ON ap.category_id = ac.id
                    WHERE ap.status = 'active' AND ap.price BETWEEN ? AND ?
                    ORDER BY ap.price ASC
                    LIMIT 20
                """, (min_price, max_price))
            else:
                cursor = await db.execute("""
                    SELECT as_.id, as_.title, as_.price, u.username, ac.name as category_name
                    FROM auto_services as_
                    JOIN users u ON as_.user_id = u.user_id
                    JOIN auto_categories ac ON as_.category_id = ac.id
                    WHERE as_.status = 'active' AND as_.price BETWEEN ? AND ?
                    ORDER BY as_.price ASC
                    LIMIT 20
                """, (min_price, max_price))
            
            results = await cursor.fetchall()
        
        if not results:
            builder = InlineKeyboardBuilder()
            back_callback = "products" if filter_type == 'products' else "services"
            builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback))
            
            await message.answer(
                f"💰 **Фильтр по цене: {min_price}₽ - {max_price}₽**\n\n"
                "❌ Ничего не найдено в данном ценовом диапазоне.",
                reply_markup=builder.as_markup()
            )
            await state.clear()
            return
        
        text = f"💰 **Фильтр по цене: {min_price}₽ - {max_price}₽**\n\n"
        text += f"Найдено: {len(results)}\n\n"
        
        builder = InlineKeyboardBuilder()
        
        for item_id, title, price, username, category in results[:10]:
            price_text = f"{price}₽"
            button_text = f"{title[:25]}... - {price_text}"
            item_type = "tech" if filter_type == 'products' else "service"
            builder.add(types.InlineKeyboardButton(
                text=button_text, 
                callback_data=f"item_{item_type}_{item_id}"
            ))
        
        back_callback = "products" if filter_type == 'products' else "services"
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback))
        builder.adjust(1)
        
        await message.answer(text, reply_markup=builder.as_markup())
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную цену (число)")