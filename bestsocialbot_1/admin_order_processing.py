from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
from config import ADMIN_ID
from dispatcher import dp
from messages_system import send_system_message
import json

class AdminProcessingStates(StatesGroup):
    waiting_supplier_id = State()
    waiting_reject_reason = State()

@dp.callback_query(F.data.startswith("reject_req_"))
async def reject_request_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса отклонения заявки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    parts = callback.data.split("_")
    # reject_req_type_id
    item_type = parts[2]
    request_id = int(parts[3])

    await state.update_data(current_request_id=request_id, current_item_type=item_type)
    
    await callback.message.answer(
        f"❌ Отклонение заявки #{request_id}\n"
        "Введите причину отклонения:"
    )
    await state.set_state(AdminProcessingStates.waiting_reject_reason)
    await callback.answer()

@dp.message(AdminProcessingStates.waiting_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext):
    """Обработка причины отклонения"""
    reason = message.text.strip()
    data = await state.get_data()
    request_id = data.get('current_request_id')
    item_type = data.get('current_item_type')

    # Обновляем статус в БД
    table_name = "service_orders" if item_type == "service" else "order_requests"
    
    async with aiosqlite.connect("bot_database.db") as db:
        # Проверяем существование записи
        cursor = await db.execute(f"SELECT user_id, title FROM {table_name} WHERE id = ?", (request_id,))
        row = await cursor.fetchone()
        
        if row:
            user_id, title = row
            await db.execute(f"UPDATE {table_name} SET status = 'rejected' WHERE id = ?", (request_id,))
            await db.commit()
            
            # Уведомляем пользователя
            await send_system_message(
                user_id,
                f"❌ Заявка отклонена: {title}",
                f"Ваша заявка была отклонена администратором.\nПричина: {reason}"
            )
            await message.answer("✅ Заявка отклонена, пользователь уведомлен.")
        else:
            await message.answer("❌ Заявка не найдена.")

    await state.clear()

@dp.callback_query(F.data.startswith("approve_req_"))
async def approve_request_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса одобрения заявки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    parts = callback.data.split("_")
    item_type = parts[2]
    request_id = int(parts[3])
    
    await state.update_data(current_request_id=request_id, current_item_type=item_type)
    
    # Спрашиваем ID поставщика
    # Если заявка сама от поставщика, можно было бы взять его ID, но лучше уточнить
    await callback.message.answer(
        f"✅ Одобрение {item_type} #{request_id}\n"
        "Введите Telegram ID поставщика (число) или перешлите сообщение от него.\n"
        "Этот ID будет использоваться для связи покупателя с поставщиком."
    )
    await state.set_state(AdminProcessingStates.waiting_supplier_id)
    await callback.answer()

@dp.message(AdminProcessingStates.waiting_supplier_id)
async def process_supplier_id(message: Message, state: FSMContext):
    """Обработка ID поставщика и добавление в каталог"""
    data = await state.get_data()
    request_id = data.get('current_request_id')
    item_type = data.get('current_item_type')
    
    supplier_id = None
    if message.forward_from:
         supplier_id = message.forward_from.id
    elif message.text.isdigit():
         supplier_id = int(message.text)
    
    if not supplier_id:
         await message.answer("❌ Некорректный ID. Введите число.")
         return

    await message.answer("⏳ Обработка...")
    
    result = await approve_and_add_to_catalog(request_id, item_type, supplier_id)
    
    if result:
        await message.answer(f"✅ Успешно! Карточка добавлена в каталог, пользователь уведомлен.")
    else:
        await message.answer("❌ Произошла ошибка при добавлении.")
        
    await state.clear()

async def approve_and_add_to_catalog(request_id, item_type, supplier_id):
    try:
        source_table = "service_orders" if item_type == "service" else "order_requests"
        target_table = "auto_services" if item_type == "service" else "auto_products"
        
        async with aiosqlite.connect("bot_database.db") as db:
            # 1. Получаем данные заявки
            cursor = await db.execute(f"SELECT * FROM {source_table} WHERE id = ?", (request_id,))
            row = await cursor.fetchone()
            
            if not row:
                print(f"Заявка {request_id} не найдена в {source_table}")
                return False
                
            # Получаем имена колонок
            columns = [description[0] for description in cursor.description]
            request_data = dict(zip(columns, row))
            
            # 2. Определяем category_id
            category_name = request_data.get('category')
            category_id = 999 # Fallback
            
            if category_name:
                # Ищем в auto_categories (для каталога магазина)
                # Если не найдено, возможно придется создать или использовать default
                # В текущей реализации auto_categories имеет type 'tech' или 'service'
                cat_type = 'service' if item_type == 'service' else 'tech'
                
                cursor = await db.execute("SELECT id FROM auto_categories WHERE name = ? AND type = ?", (category_name, cat_type))
                cat_row = await cursor.fetchone()
                
                if cat_row:
                    category_id = cat_row[0]
                else:
                    # Если категории нет, создаем новую? Или используем "Общая"?
                    # Создадим новую для простоты
                    await db.execute("INSERT INTO auto_categories (name, type) VALUES (?, ?)", (category_name, cat_type))
                    cursor = await db.execute("SELECT last_insert_rowid()")
                    category_id = (await cursor.fetchone())[0]

            # 3. Добавляем в каталог (auto_products / auto_services)
            # Маппинг полей
            # auto_products: user_id, category_id, title, description, price, images, specifications, status, created_at
            # + rating columns...
            
            # Form description from request data fields
            description_parts = []
            if request_data.get('additional_info'): description_parts.append(request_data['additional_info'])
            if request_data.get('purpose'): description_parts.append(f"Назначение: {request_data['purpose']}")
            if request_data.get('condition'): description_parts.append(f"Состояние: {request_data['condition']}")
            if request_data.get('item_class'): description_parts.append(f"Класс: {request_data['item_class']}")
            if request_data.get('detailed_specs'): description_parts.append(f"Детали: {request_data['detailed_specs']}")
            
            description = "\n".join(description_parts)
            
            # Handle images (already JSON in request?)
            images = request_data.get('images', '[]')
            
            # Handle specifications
            specs = request_data.get('specifications', '')
            
            # Insert
            await db.execute(f"""
                INSERT INTO {target_table} 
                (user_id, category_id, title, description, price, images, specifications, status, created_at, contact_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """, (
                supplier_id, 
                category_id, 
                request_data.get('title'),
                description,
                _parse_price(request_data.get('price')),
                images,
                specs,
                datetime.now().isoformat(),
                request_data.get('contact')
            ))
            
            await db.commit()
            
            # 4. Обновляем статус заявки
            await db.execute(f"UPDATE {source_table} SET status = 'approved' WHERE id = ?", (request_id,))
            await db.commit()
            
            # 5. Уведомляем пользователя
            user_id = request_data.get('user_id')
            await send_system_message(
                user_id,
                f"✅ Заявка одобрена: {request_data.get('title')}",
                f"Ваша карточка была добавлена в каталог магазина!\n\n"
                f"👤 **Поставщик:** [Открыть профиль](tg://user?id={supplier_id}) (ID: {supplier_id})\n"
                f"Используйте эту ссылку для прямой связи."
            )
            
            return True
            
    except Exception as e:
        print(f"Error in approve_and_add_to_catalog: {e}")
        import traceback
        traceback.print_exc()
        return False

def _parse_price(price_str):
    if not price_str: return 0.0
    # Try to extract number from string like "1000 rub"
    try:
        import re
        nums = re.findall(r'\d+', str(price_str))
        if nums:
             return float("".join(nums))
        return 0.0
    except:
        return 0.0
