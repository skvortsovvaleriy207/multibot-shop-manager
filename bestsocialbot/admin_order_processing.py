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
import re

class AdminProcessingStates(StatesGroup):
    waiting_supplier_id = State()
    waiting_reject_reason = State()
    # Edit states
    waiting_edit_field = State()
    waiting_new_value = State()
    waiting_new_photo = State()

@dp.callback_query(F.data.startswith("edit_req_"))
async def process_edit_request_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования заявки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    # approve_req_type_id or edit_req_type_id
    payload = callback.data.replace("edit_req_", "")
    try:
        item_type, request_id = payload.rsplit("_", 1)
        request_id = int(request_id)
    except ValueError:
        await callback.answer("❌ Ошибка парсинга данных", show_alert=True)
        return
    
    await state.update_data(current_request_id=request_id, current_item_type=item_type)
    
    # Меню выбора поля для редактирования
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📝 Название", callback_data="edit_field_title"))
    builder.add(types.InlineKeyboardButton(text="📄 Описание (Additional)", callback_data="edit_field_additional_info"))
    builder.add(types.InlineKeyboardButton(text="💰 Цена", callback_data="edit_field_price"))
    builder.add(types.InlineKeyboardButton(text="🏷️ Категория", callback_data="edit_field_category"))
    builder.add(types.InlineKeyboardButton(text="📊 Класс", callback_data="edit_field_item_class"))
    builder.add(types.InlineKeyboardButton(text="👁 Вид (Kind)", callback_data="edit_field_item_kind"))
    builder.add(types.InlineKeyboardButton(text="🎯 Назначение", callback_data="edit_field_purpose"))
    builder.add(types.InlineKeyboardButton(text="🔄 Состояние", callback_data="edit_field_condition"))
    builder.add(types.InlineKeyboardButton(text="📋 Детали (Spec)", callback_data="edit_field_detailed_specs"))
    builder.add(types.InlineKeyboardButton(text="⚙️ Характеристики", callback_data="edit_field_specifications"))
    builder.add(types.InlineKeyboardButton(text="📞 Контакты", callback_data="edit_field_contact"))
    builder.add(types.InlineKeyboardButton(text="🖼 Изменить фото", callback_data="edit_photo_start"))
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="cancel_edit"))
    builder.adjust(2, 2, 2, 2, 2, 2, 1)
    
    await callback.message.answer(
        f"✏️ Редактирование заявки #{request_id}\n"
        "Выберите поле для изменения:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminProcessingStates.waiting_edit_field)
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    """Отмена редактирования"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("Редактирование отменено")

@dp.callback_query(F.data.startswith("edit_field_"))
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    field = callback.data.replace("edit_field_", "")
    await state.update_data(editing_field=field)
    
    field_names = {
        "title": "Название",
        "additional_info": "Описание",
        "price": "Цена",
        "category": "Категория",
        "item_class": "Класс",
        "item_type_detail": "Тип",
        "item_kind": "Вид",
        "purpose": "Назначение",
        "condition": "Состояние",
        "detailed_specs": "Детальные характеристики",
        "specifications": "Характеристики",
        "contact": "Контакты"
    }
    
    field_name = field_names.get(field, field)
    
    # Add Cancel/Back button
    builder = InlineKeyboardBuilder()
    item_type = (await state.get_data()).get('current_item_type')
    request_id = (await state.get_data()).get('current_request_id')
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"edit_req_{item_type}_{request_id}"))
    
    await callback.message.edit_text(
        f"✏️ Редактирование поля: **{field_name}**\n\n"
        "Введите новое значение:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminProcessingStates.waiting_new_value)
    try:
        await callback.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "edit_photo_start")
async def process_edit_photo_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор изменения фото"""
    await state.update_data(editing_field="images")
    
    # Add Cancel/Back button
    builder = InlineKeyboardBuilder()
    item_type = (await state.get_data()).get('current_item_type')
    request_id = (await state.get_data()).get('current_request_id')
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"edit_req_{item_type}_{request_id}"))

    await callback.message.edit_text(
        "🖼 **Изменение главного фото**\n\n"
        "Отправьте новое фото для этой карточки.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminProcessingStates.waiting_new_photo)
    try:
        await callback.answer()
    except Exception:
        pass

@dp.message(AdminProcessingStates.waiting_new_photo, F.photo)
async def process_new_photo(message: Message, state: FSMContext):
    """Сохранение нового фото"""
    data = await state.get_data()
    request_id = data.get('current_request_id')
    item_type = data.get('current_item_type')
    
    # Get largest photo
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Construct JSON for images
    # We will replace the main image and keep entry minimal as per current simple logic
    # Or ideally, read existing and update 'main'? Let's keep it simple: new main photo.
    
    images_json = json.dumps({
        "main": {"file_id": file_id},
        "additional": [] 
    })
    
    table_name = "order_requests"
    
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute(f"UPDATE {table_name} SET images = ? WHERE id = ?", (images_json, request_id))
            await db.commit()
            
            await message.answer("✅ Фото обновлено!")
            
            # Show next steps
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="✏️ Продолжить редактирование", 
                callback_data=f"edit_req_{item_type}_{request_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text="✅ Одобрить и добавить в каталог", 
                callback_data=f"approve_req_{item_type}_{request_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text="🔙 Вернуться к просмотру", 
                callback_data=f"view_item_{item_type}_{request_id}"
            ))
            builder.adjust(1)
            
            await message.answer("Что дальше?", reply_markup=builder.as_markup())
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении фото: {e}")
        
    await state.clear()

@dp.message(AdminProcessingStates.waiting_new_value)
async def process_new_value(message: Message, state: FSMContext):
    """Сохранение нового значения"""
    data = await state.get_data()
    request_id = data.get('current_request_id')
    item_type = data.get('current_item_type')
    field = data.get('editing_field')
    new_value = message.text.strip()
    
    table_name = "order_requests" # Using order_requests for all types as per recent migration
    
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # Проверяем, существует ли колонка (simple check)
            # В реальном проекте лучше использовать безопасный маппинг
            allowed_fields = [
                "title", "additional_info", "price", "category", 
                "item_class", "item_type_detail", "item_kind",
                "purpose", "condition", "detailed_specs", "specifications", "contact"
            ]
            
            if field not in allowed_fields:
                await message.answer("❌ Ошибка: недопустимое поле.")
                await state.clear()
                return

            await db.execute(f"UPDATE {table_name} SET {field} = ? WHERE id = ?", (new_value, request_id))
            await db.commit()
            
            # Получаем обновленные данные, чтобы показать админу
            cursor = await db.execute(f"SELECT * FROM {table_name} WHERE id = ?", (request_id,))
            row = await cursor.fetchone()
            columns = [description[0] for description in cursor.description]
            updated_data = dict(zip(columns, row))
            
            # Перегенерируем уведомление (опционально) или просто подтверждаем
            await message.answer(f"✅ Поле обновлено!\nНовое значение: {new_value}")
            
            # Предлагаем продолжить редактирование или закончить
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="✏️ Продолжить редактирование", 
                callback_data=f"edit_req_{item_type}_{request_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text="✅ Одобрить и добавить в каталог", 
                callback_data=f"approve_req_{item_type}_{request_id}"
            ))
            builder.add(types.InlineKeyboardButton(
                text="🔙 Вернуться к просмотру", 
                callback_data=f"view_item_{item_type}_{request_id}"
            ))
            builder.adjust(1)
            
            await message.answer("Что дальше?", reply_markup=builder.as_markup())
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении: {e}")
        
    await state.clear()

@dp.callback_query(F.data.startswith("reject_req_"))
async def reject_request_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса отклонения заявки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    # reject_req_type_id
    payload = callback.data.replace("reject_req_", "")
    try:
        item_type, request_id = payload.rsplit("_", 1)
        request_id = int(request_id)
    except ValueError:
        await callback.answer("❌ Ошибка парсинга данных", show_alert=True)
        return

    await state.update_data(current_request_id=request_id, current_item_type=item_type)
    
    await callback.message.answer(
        f"❌ Отклонение заявки #{request_id}\n"
        "Введите причину отклонения:"
    )
    await state.set_state(AdminProcessingStates.waiting_reject_reason)
    try:
        await callback.answer()
    except Exception:
        pass

@dp.message(AdminProcessingStates.waiting_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext):
    """Обработка причины отклонения"""
    reason = message.text.strip()
    data = await state.get_data()
    request_id = data.get('current_request_id')
    item_type = data.get('current_item_type')

    # Обновляем статус в БД
    table_name = "order_requests"
    
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

    # approve_req_type_id
    payload = callback.data.replace("approve_req_", "")
    try:
        item_type, request_id = payload.rsplit("_", 1)
        request_id = int(request_id)
    except ValueError:
        await callback.answer("❌ Ошибка парсинга данных", show_alert=True)
        return
    
    await state.update_data(current_request_id=request_id, current_item_type=item_type)

    if item_type == 'cart_order':
        # Для заказов из корзины пропускаем шаг выбора поставщика и сразу одобряем (завершаем)
        await approve_cart_order(callback.message, request_id)
        await state.clear()
        return
    
    # Спрашиваем ID поставщика
    # Если заявка сама от поставщика, можно было бы взять его ID, но лучше уточнить
    await callback.message.answer(
        f"✅ Одобрение {item_type} #{request_id}\n"
        "Введите Telegram ID поставщика (число) или перешлите сообщение от него.\n"
        "Этот ID будет использоваться для связи покупателя с поставщиком."
    )
    await state.set_state(AdminProcessingStates.waiting_supplier_id)
    try:
        await callback.answer()
    except Exception:
        pass

async def approve_cart_order(message: Message, request_id: int):
    """Одобрение заказа из корзины (смена статуса на confirmed/completed) + создание заказов"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # Получаем данные
            cursor = await db.execute("SELECT user_id, title, additional_info FROM order_requests WHERE id = ?", (request_id,))
            row = await cursor.fetchone()
            
            if not row:
                await message.answer("❌ Заказ не найден")
                return

            user_id, title, additional_info = row
            
            # Парсим товары из описания (поскольку cart_order удаляет оригинальные записи)
            # Формат: "   🆔 ID заявки: 123"
            created_orders_count = 0
            if additional_info:
                # Ищем все ID заявок
                item_ids = re.findall(r"ID заявки:\s*(\d+)", additional_info)
                
                for item_id_str in item_ids:
                    try:
                        item_id = int(item_id_str)
                        
                        # Находим продавца этого товара/услуги
                        cursor = await db.execute("SELECT user_id FROM order_requests WHERE id = ?", (item_id,))
                        seller_row = await cursor.fetchone()
                        seller_id = seller_row[0] if seller_row else None
                        
                        # Создаем запись в таблице orders
                        # order_type='order_request' так как это товары из списка заявок
                        await db.execute("""
                            INSERT INTO orders (user_id, order_type, item_id, seller_id, status, order_date)
                            VALUES (?, ?, ?, ?, 'active', ?)
                        """, (user_id, 'order_request', item_id, seller_id, datetime.now().isoformat()))
                        
                        created_orders_count += 1
                        
                        # Опционально: можно уведомить продавца здесь
                        if seller_id and seller_id != user_id:
                             await send_system_message(
                                seller_id,
                                "📦 Новый заказ!",
                                f"Пользователь оформил заказ на ваш товар (ID {item_id}).\nПроверьте раздел 'Мои заказы' или свяжитесь с покупателем."
                            )

                    except Exception as e:
                        print(f"Ошибка при создании заказа для item_id {item_id_str}: {e}")

            # Обновляем статус самой заявки-корзины
            await db.execute("UPDATE order_requests SET status = 'completed' WHERE id = ?", (request_id,))
            await db.commit()
            
            # Уведомляем пользователя
            await send_system_message(
                user_id,
                f"✅ Заказ выполнен: {title}",
                f"Ваш заказ #{request_id} был успешно обработан и закрыт администратором.\n"
                f"Создано отдельных заказов: {created_orders_count}\n"
                f"Спасибо за покупку!"
            )
            
            # Кнопка назад к списку заявок
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="◀️ Назад в админку", callback_data="back_to_admin"))
            builder.adjust(1)

            await message.answer(
                f"✅ Заказ #{request_id} ('{title}') успешно закрыт/выполнен.\n"
                f"Создано заказов в БД: {created_orders_count}",
                reply_markup=builder.as_markup()
            )
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при одобрении заказа: {e}")

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
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔙 К заявкам", callback_data="admin_new_requests"))
        await message.answer(f"✅ Успешно! Карточка добавлена в каталог, пользователь уведомлен.", reply_markup=builder.as_markup())
    else:
        await message.answer("❌ Произошла ошибка при добавлении.")
        
    await state.clear()

async def approve_and_add_to_catalog(request_id, item_type, supplier_id):
    try:
        source_table = "order_requests"
        if item_type == "offer":
             target_table = None
        else:
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
            
            # 2. Определяем category_id и добавляем в каталог только если не offer
            catalog_id = 0
            if target_table:
                category_name = request_data.get('category')
                category_id = 999 # Fallback
                
                if category_name:
                    # Ищем в auto_categories (для каталога магазина)
                    cat_type = 'service' if item_type == 'service' else 'tech'
                    
                    cursor = await db.execute("SELECT id FROM auto_categories WHERE name = ? AND type = ?", (category_name, cat_type))
                    cat_row = await cursor.fetchone()
                    
                    if cat_row:
                        category_id = cat_row[0]
                    else:
                        # Если категории нет, создаем новую для простоты
                        await db.execute("INSERT INTO auto_categories (name, type) VALUES (?, ?)", (category_name, cat_type))
                        cursor = await db.execute("SELECT last_insert_rowid()")
                        category_id = (await cursor.fetchone())[0]

                # 3. Добавляем в каталог (auto_products / auto_services)
                
                # Form description from request data fields
                description_parts = []
                if request_data.get('additional_info'): description_parts.append(request_data['additional_info'])
                if request_data.get('purpose'): description_parts.append(f"Назначение: {request_data['purpose']}")
                if request_data.get('condition'): description_parts.append(f"Состояние: {request_data['condition']}")
                if request_data.get('item_class'): description_parts.append(f"Класс: {request_data['item_class']}")
                if request_data.get('detailed_specs'): description_parts.append(f"Детали: {request_data['detailed_specs']}")
                
                description = "\n".join(description_parts)
                
                # Handle images
                images = request_data.get('images', '[]')
                
                # Handle specifications
                specs = request_data.get('specifications', '')
                
                # Insert
                cursor = await db.execute(f"""
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
                
                # Получаем ID новой карточки в каталоге
                catalog_id = cursor.lastrowid
                
                await db.commit()
            
            # Export to Google Sheet (Заявки)
            try:
                from automarket_sheets import export_request_to_sheet
                await export_request_to_sheet(request_id, item_type, catalog_id)
            except Exception as e:
                print(f"Ошибка при вызове экспорта заявки: {e}")
                
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
        print(f"Ошибка в approve_and_add_to_catalog: {e}")
        return False


@dp.callback_query(F.data == "admin_new_requests")
async def admin_new_requests_handler(callback: CallbackQuery, state: FSMContext):
    """Список новых заявок для обработки администратором"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    await state.clear()
    
    async with aiosqlite.connect("bot_database.db") as db:
        # Получаем все заявки в статусе active/new/pending
        cursor = await db.execute("""
            SELECT id, title, item_type, operation, created_at, user_id
            FROM order_requests 
            WHERE status IN ('active', 'new', 'pending')
            ORDER BY created_at DESC
            LIMIT 20
        """)
        requests = await cursor.fetchall()
        
    if not requests:
        await callback.answer("Новых заявок нет", show_alert=True)
        # Если это было редактирование сообщения
        try:
             builder = InlineKeyboardBuilder()
             builder.add(types.InlineKeyboardButton(text="◀️ В админ-панель", callback_data="admin_panel_menu"))
             await callback.message.edit_text("📭 **Новых заявок нет**\n\nВсе заявки обработаны.", reply_markup=builder.as_markup())
        except:
             pass
        return

    builder = InlineKeyboardBuilder()
    
    for req_id, title, item_type, operation, created_at, user_id in requests:
        # Формируем текст кнопки
        req_type_icon = "📦" if item_type == "product" else "🛠" if item_type == "service" else "📋"
        op_icon = "🛒" if operation == "buy" else "💰" if operation == "sell" else "🤝"
        
        btn_text = f"{req_type_icon} {op_icon} #{req_id} {title[:15]}..."
        
        # Callback для просмотра заявки
        builder.add(types.InlineKeyboardButton(
            text=btn_text, 
            callback_data=f"view_item_{item_type}_{req_id}"
        ))

    builder.add(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_new_requests"))
    builder.add(types.InlineKeyboardButton(text="◀️ В админ-панель", callback_data="admin_panel_menu"))
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📋 **Список новых заявок ({len(requests)})**\n\n"
        "Выберите заявку для просмотра и обработки:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

def _parse_price(price_str):
    if not price_str: return 0
    try:
        return float(''.join(filter(str.isdigit, str(price_str))))
    except:
        return 0
            
