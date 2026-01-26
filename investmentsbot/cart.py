from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import DB_FILE
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user
from messages_system import send_system_message



class CartOrderStates(StatesGroup):
    waiting_quantity = State()
    waiting_options = State()


# Добавление в корзину из каталога (Shop)
@dp.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart_from_shop(callback: CallbackQuery):
    """Обработчик добавления в корзину из каталога магазина"""
    if await check_blocked_user(callback):
        return
    
    # Формат: add_to_cart_{type}_{id}
    # type: product, service, offer
    try:
        parts = callback.data.split("_")
        
        item_type_raw = parts[3]
        item_id = int(parts[4])
        user_id = callback.from_user.id
        
        # Определяем тип для базы данных
        async with aiosqlite.connect(DB_FILE) as db:
            # 1. Проверяем существование товара и получаем цену
            cursor = await db.execute("""
                SELECT title, price FROM order_requests WHERE id = ?
            """, (item_id,))
            item = await cursor.fetchone()
            
            if not item:
                await callback.answer("❌ Товар не найден или удален", show_alert=True)
                return
            
            title, price = item
            
            # 2. Проверяем, нет ли уже в корзине
            cursor = await db.execute("""
                SELECT quantity FROM cart_order 
                WHERE user_id = ? AND item_id = ? AND item_type IN ('order_request', 'товар', 'product', 'offer')
            """, (user_id, item_id))
            existing = await cursor.fetchone()
            
            new_qty = 1
            if existing:
                # Если уже есть - увеличиваем количество
                new_qty = existing[0] + 1
                await db.execute("""
                    UPDATE cart_order SET quantity = ? 
                    WHERE user_id = ? AND item_id = ? AND item_type IN ('order_request', 'товар', 'product', 'offer')
                """, (new_qty, user_id, item_id))
            else:
                # Если нет - добавляем
                await db.execute("""
                    INSERT INTO cart_order (
                        user_id, item_type, item_id, quantity, selected_options, price, added_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    "order_request", # Используем общий тип для товаров из заявок
                    item_id,
                    1,
                    "",
                    price or "0",
                    datetime.now().isoformat()
                ))
            
            await db.commit()

            # 3. Обновляем клавиатуру для визуального подтверждения
            try:
                current_markup = callback.message.reply_markup
                if current_markup:
                    for row in current_markup.inline_keyboard:
                        for btn in row:
                            if btn.callback_data == callback.data:
                                btn.text = f"✅ В корзине ({new_qty})"
                    
                    await callback.message.edit_reply_markup(reply_markup=current_markup)
            except Exception as e:
                print(f"Не удалось обновить кнопку: {e}")

            await callback.answer(f"✅ Добавлено (всего {new_qty})", show_alert=False)
            
    except Exception as e:
        print(f"Ошибка добавления в корзину: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)



async def auto_fill_cart_from_orders(user_id: int):
    """Автоматическое заполнение корзины из заявок пользователя"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Проверяем, не заполнена ли уже корзина
        cursor = await db.execute("""
            SELECT COUNT(*) FROM cart_order WHERE user_id = ?
        """, (user_id,))
        cart_count = (await cursor.fetchone())[0]

        if cart_count > 0:
            return False  # Корзина уже заполнена

        # Получаем активные заявки пользователя
        cursor = await db.execute("""
            SELECT id, title, price, category, operation, item_type 
            FROM order_requests 
            WHERE user_id = ? AND status IN ('active', 'new', 'pending')
            ORDER BY created_at DESC
        """, (user_id,))
        orders = await cursor.fetchall()

        if not orders:
            return False  # Нет активных заявок

        added_count = 0
        # Добавляем каждую заявку в корзину
        for order in orders:
            order_id, title, price, category, operation, item_type = order

            # Проверяем, нет ли уже этой заявки в корзине
            cursor = await db.execute("""
                SELECT id FROM cart_order 
                WHERE user_id = ? AND item_id = ? AND item_type IN ('order_request', 'товар', 'product', 'offer')
            """, (user_id, order_id))
            existing = await cursor.fetchone()

            if not existing:
                # Добавляем заявку в корзину
                await db.execute("""
                    INSERT INTO cart_order (
                        user_id, item_type, item_id, quantity, selected_options, price, added_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    "order_request",
                    order_id,
                    1,  # Количество по умолчанию
                    "",  # Без опций по умолчанию
                    price or "0",
                    datetime.now().isoformat()
                ))
                added_count += 1

        await db.commit()
        return added_count > 0


async def get_cart_items_paginated(user_id: int, page: int = 1, items_per_page: int = 3):
    """Получить заявки из корзины с пагинацией"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Общее количество заявок
        cursor = await db.execute("""
            SELECT COUNT(*) FROM cart_order WHERE user_id = ?
        """, (user_id,))
        total_items = (await cursor.fetchone())[0]

        if total_items == 0:
            return [], 0, 0, 0

        # Общее количество страниц
        total_pages = (total_items + items_per_page - 1) // items_per_page

        # Проверка корректности страницы
        if page > total_pages:
            page = total_pages
        if page < 1:
            page = 1

        # Вычисляем смещение
        offset = (page - 1) * items_per_page

        # Получаем заявки для текущей страницы
        cursor = await db.execute("""
            SELECT c.id as cart_id, c.item_type, c.item_id, c.quantity, c.selected_options, c.price,
                   o.title, o.category, o.operation, o.item_type, o.price as original_price,
                   o.condition, o.specifications, o.purpose, o.created_at
            FROM cart_order c
            LEFT JOIN order_requests o ON c.item_id = o.id AND c.item_type IN ('order_request', 'товар', 'product', 'offer')
            WHERE c.user_id = ?
            ORDER BY c.added_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, items_per_page, offset))

        items = await cursor.fetchall()

        # Получаем общую сумму
        cursor = await db.execute("""
            SELECT SUM(c.quantity * CAST(c.price AS REAL))
            FROM cart_order c
            WHERE c.user_id = ?
        """, (user_id,))
        total_sum = (await cursor.fetchone())[0] or 0

        return items, total_items, total_pages, total_sum


async def cart_order_main_menu(callback: CallbackQuery, state: FSMContext, page: int = 1):
    """Главное меню корзины с автоматическим заполнением"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    # Загружаем заявки из Google Sheets
    try:
        from google_sheets import sync_requests_from_sheets_to_db
        loaded = await sync_requests_from_sheets_to_db()

        if loaded:
            # Обновляем корзину после загрузки
            # await auto_fill_cart_from_orders(user_id)  # DISABLED: Prevents clearing cart after order
            pass
    except Exception as e:
        print(f"Ошибка загрузки заявок: {e}")

    # Получаем заявки с пагинацией
    items, total_items, total_pages, total_sum = await get_cart_items_paginated(user_id, page)

    builder = InlineKeyboardBuilder()

    if total_items > 0:
        # Создаем уникальный идентификатор сообщения чтобы избежать ошибки "message is not modified"
        message_id = f"{callback.message.message_id}_{user_id}_{page}_{datetime.now().timestamp()}"

        # Создаем сообщение с деталями
        response = f"🛒 **Корзина заявок**\n\n"

        response += f"📊 **Страница {page} из {total_pages if total_pages > 0 else 1}**\n"
        response += f"📦 Всего заявок: {total_items}\n"

        if total_sum > 0:
            response += f"💰 Общая сумма: {total_sum:.2f} руб.\n"

        response += "\n" + "=" * 30 + "\n\n"

        # Отображаем заявки текущей страницы
        for i, item in enumerate(items, 1):
            cart_id, item_type, item_id, quantity, options, price, title, category, operation, item_type_detail, original_price, condition, specifications, purpose, created_at = item

            # Используем цену из корзины или оригинальную цену
            try:
                item_price = float(price) if price and price != "0" else float(original_price) if original_price else 0
                item_total = item_price * quantity
            except (ValueError, TypeError):
                item_price = 0
                item_total = 0

            response += f"**{i + (page - 1) * 3}. {title or f'Заявка #{item_id}'}**\n"
            response += f"🆔 ID: {item_id}\n"

            if operation:
                operation_emoji = "🛒" if operation == "buy" else "💰" if operation == "sell" else "🤝"
                response += f"{operation_emoji} Операция: {operation}\n"

            response += f"📦 Количество: {quantity}\n"

            if item_price > 0:
                response += f"💰 Цена: {item_price:.2f} руб. × {quantity} = {item_total:.2f} руб.\n"

            if category:
                response += f"🏷 Категория: {category}\n"

            if item_type_detail:
                response += f"📋 Тип: {item_type_detail}\n"

            if condition:
                response += f"🔧 Состояние: {condition}\n"

            if purpose:
                response += f"🎯 Назначение: {purpose}\n"

            if created_at:
                response += f"📅 Дата создания: {created_at[:10] if len(created_at) > 10 else created_at}\n"

            # Кнопки действий для каждой заявки
            builder.add(types.InlineKeyboardButton(
                text=f"✏️ {i} изменить",
                callback_data=f"cart_edit_{item_id}_{page}"
            ))
            builder.add(types.InlineKeyboardButton(
                text=f"❌ {i} удалить",
                callback_data=f"cart_remove_{item_id}_{page}"
            ))

            response += "\n" + "-" * 20 + "\n\n"

        # Добавляем кнопки навигации если есть несколько страниц
        if total_pages > 1:
            nav_row = []
            if page > 1:
                nav_row.append(types.InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"cart_page_{page - 1}"
                ))

            nav_row.append(types.InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data=f"cart_page_info_{message_id}"  # Уникальный callback
            ))

            if page < total_pages:
                nav_row.append(types.InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=f"cart_page_{page + 1}"
                ))

            builder.row(*nav_row)

        # Основные кнопки управления корзиной
        builder.row(
            types.InlineKeyboardButton(text="📋 Оформить заказ", callback_data="cart_order_checkout"),
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"cart_refresh_{message_id}")
            # Уникальный callback
        )
        builder.row(
            types.InlineKeyboardButton(text="🗑 Очистить всё", callback_data="cart_order_clear"),
            types.InlineKeyboardButton(text="📋 Создать заявку", callback_data="create_order")
        )

    else:
        response = (
            "🛒 **Корзина заявок**\n\n"
            "Ваша корзина пуста.\n\n"
            "Вы можете:\n"
            "• Создать новую заявку\n"
            "• Подождать синхронизации с Google Sheets\n"
            "• Проверить статус своих заявок"
        )

        builder.add(types.InlineKeyboardButton(text="📝 Создать заявку", callback_data="create_order"))
        builder.add(types.InlineKeyboardButton(text="🔄 Обновить корзину", callback_data="cart_refresh_empty"))

    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))

    # Настраиваем расположение кнопок
    if total_items > 0:
        # Для кнопок редактирования/удаления (2 в строке)
        builder.adjust(2, 2, 2, 2, 2, 2, 1)

    try:
        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        if "message is not modified" in str(e):
            # Игнорируем эту ошибку - сообщение уже актуально
            pass
        else:
            print(f"Ошибка редактирования сообщения: {e}")
            await callback.message.answer(
                response,
                reply_markup=builder.as_markup()
            )
    await callback.answer()


@dp.callback_query(F.data == "cart_order")
async def cart_order_start(callback: CallbackQuery, state: FSMContext):
    """Точка входа в корзину - можно использовать для кнопки в другом файле"""
    await cart_order_main_menu(callback, state, page=1)


@dp.callback_query(F.data == "cart_from_account")
async def cart_from_account_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки Корзина из личного кабинета - перенаправляет в корзину заявок"""
    await cart_order_main_menu(callback, state, page=1)


@dp.callback_query(F.data.startswith("cart_page_"))
async def cart_order_page(callback: CallbackQuery, state: FSMContext):
    """Обработка переключения страниц корзины"""
    data = callback.data.replace("cart_page_", "")

    if data.startswith("info_"):
        await callback.answer(f"Навигация по страницам корзины", show_alert=False)
        return

    try:
        page = int(data)
        await cart_order_main_menu(callback, state, page)
    except ValueError:
        await callback.answer("❌ Ошибка перехода на страницу", show_alert=True)


@dp.callback_query(F.data.startswith("cart_refresh_"))
async def cart_refresh(callback: CallbackQuery, state: FSMContext):
    """Обновление корзины с уникальным callback"""
    try:
        # Извлекаем номер страницы из текущего сообщения
        text = callback.message.text
        page = 1
        if "Страница" in text:
            import re
            match = re.search(r'Страница (\d+) из (\d+)', text)
            if match:
                page = int(match.group(1))

        await cart_order_main_menu(callback, state, page)
        await callback.answer("✅ Корзина обновлена", show_alert=False)
    except Exception as e:
        print(f"Ошибка обновления корзины: {e}")
        await callback.answer("❌ Ошибка обновления", show_alert=True)


@dp.callback_query(F.data == "cart_refresh_empty")
async def cart_refresh_empty(callback: CallbackQuery, state: FSMContext):
    """Обновление пустой корзины"""
    await cart_order_start(callback, state)


@dp.callback_query(F.data.startswith("cart_edit_"))
async def cart_edit_item(callback: CallbackQuery, state: FSMContext):
    """Редактирование заявки в корзине"""
    try:
        # data format: cart_edit_{item_id}_{page} OR cart_qty_{inc/dec}_{item_id}_{page}
        parts = callback.data.split("_")
        if len(parts) < 3:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        if parts[1] == 'qty':
            # cart_qty_inc_123_1
            if len(parts) < 5:
                await callback.answer("❌ Ошибка формата количества", show_alert=True)
                return
            item_id = int(parts[3])
            page = int(parts[4])
        else:
            # cart_edit_123_1
            if len(parts) < 4:
                item_id = int(parts[2])
                page = 1
            else:
                item_id = int(parts[2])
                page = int(parts[3])

        user_id = callback.from_user.id

        # Получаем информацию о заявке
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("""
                SELECT c.quantity, c.price, c.selected_options,
                       o.title, o.category, o.operation, o.item_type, 
                       o.condition, o.purpose
                FROM cart_order c
                LEFT JOIN order_requests o ON c.item_id = o.id
                WHERE c.user_id = ? AND c.item_id = ? AND c.item_type IN ('order_request', 'товар', 'product', 'offer')
            """, (user_id, item_id))
            item = await cursor.fetchone()

        if not item:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return

        quantity, price, options, title, category, operation, item_type_detail, condition, purpose = item

        builder = InlineKeyboardBuilder()

        # Кнопки изменения количества
        builder.add(types.InlineKeyboardButton(text="➖ Уменьшить", callback_data=f"cart_qty_dec_{item_id}_{page}"))
        builder.add(types.InlineKeyboardButton(text="➕ Увеличить", callback_data=f"cart_qty_inc_{item_id}_{page}"))

        builder.row(
            types.InlineKeyboardButton(text="✅ Сохранить", callback_data=f"cart_save_{item_id}_{page}"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cart_page_{page}")
        )

        response = f"✏️ **Редактирование заявки**\n\n"
        response += f"📝 **{title}**\n"
        response += f"🆔 ID: {item_id}\n"
        response += f"📦 Текущее количество: {quantity}\n"

        try:
            item_price = float(price) if price else 0
            response += f"💰 Цена за ед.: {item_price:.2f} руб.\n"
            response += f"💵 Общая сумма: {item_price * quantity:.2f} руб.\n"
        except ValueError:
            response += f"💰 Цена: не указана\n"

        if category:
            response += f"🏷 Категория: {category}\n"

        if operation:
            response += f"🎯 Операция: {operation}\n"

        if item_type_detail:
            response += f"📋 Тип: {item_type_detail}\n"

        if condition:
            response += f"🔧 Состояние: {condition}\n"

        if purpose:
            response += f"🎯 Назначение: {purpose}\n"

        if options:
            response += f"⚙️ Опции: {options}\n"

        response += "\nИспользуйте кнопки для изменения количества:"

        await callback.message.edit_text(
            response,
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        print(f"Ошибка редактирования: {e}")
        await callback.answer("❌ Ошибка редактирования", show_alert=True)


@dp.callback_query(F.data.startswith("cart_qty_"))
async def cart_change_quantity(callback: CallbackQuery):
    """Изменение количества товара в корзине"""
    try:
        # data format: cart_qty_{inc/dec}_{item_id}_{page}
        parts = callback.data.split("_")
        if len(parts) < 4:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        action = parts[2]  # inc или dec
        item_id = int(parts[3])
        page = int(parts[4])
        user_id = callback.from_user.id

        async with aiosqlite.connect(DB_FILE) as db:
            # Получаем текущее количество
            cursor = await db.execute("""
                SELECT quantity FROM cart_order 
                WHERE user_id = ? AND item_id = ? AND item_type IN ('order_request', 'товар', 'product', 'offer')
            """, (user_id, item_id))
            result = await cursor.fetchone()

            if not result:
                await callback.answer("❌ Заявка не найдена", show_alert=True)
                return

            current_qty = result[0]

            # Изменяем количество
            if action == "inc":
                new_qty = current_qty + 1
            elif action == "dec":
                new_qty = max(1, current_qty - 1)  # Минимум 1
            else:
                await callback.answer("❌ Неизвестное действие", show_alert=True)
                return

            # Обновляем количество
            await db.execute("""
                UPDATE cart_order SET quantity = ? 
                WHERE user_id = ? AND item_id = ? AND item_type IN ('order_request', 'товар', 'product', 'offer')
            """, (new_qty, user_id, item_id))

            await db.commit()

        # Обновляем интерфейс редактирования
        await cart_edit_item(callback, state=None)
        await callback.answer(f"✅ Количество изменено: {new_qty}", show_alert=False)

    except Exception as e:
        print(f"Ошибка изменения количества: {e}")
        await callback.answer("❌ Ошибка изменения количества", show_alert=True)


@dp.callback_query(F.data.startswith("cart_save_"))
async def cart_save_changes(callback: CallbackQuery):
    """Сохранение изменений в корзине"""
    try:
        # data format: cart_save_{item_id}_{page}
        parts = callback.data.split("_")
        if len(parts) < 4:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        item_id = int(parts[2])
        page = int(parts[3])

        await callback.answer("✅ Изменения сохранены", show_alert=False)
        await cart_order_main_menu(callback, state=None, page=page)

    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        await callback.answer("❌ Ошибка сохранения", show_alert=True)


@dp.callback_query(F.data.startswith("cart_remove_"))
async def cart_remove_item(callback: CallbackQuery):
    """Удаление заявки из корзины"""
    try:
        # data format: cart_remove_{item_id}_{page}
        parts = callback.data.split("_")
        if len(parts) < 4:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        item_id = int(parts[2])
        page = int(parts[3])
        user_id = callback.from_user.id

        async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
            await db.execute("""
                DELETE FROM cart_order 
                WHERE user_id = ? AND item_id = ? AND item_type IN ('order_request', 'товар', 'product', 'offer')
            """, (user_id, item_id))
            await db.commit()

        await callback.answer("✅ Заявка удалена из корзины", show_alert=False)

        # Обновляем корзину
        await cart_order_main_menu(callback, state=None, page=page)

    except Exception as e:
        print(f"Ошибка удаления: {e}")
        await callback.answer("❌ Ошибка удаления", show_alert=True)


@dp.callback_query(F.data == "cart_order_checkout")
async def cart_order_checkout(callback: CallbackQuery):
    """Оформление заказа из корзины"""
    user_id = callback.from_user.id

    from utils import has_active_process
    if await has_active_process(user_id):
        # Получаем детали активного процесса
        from utils import get_active_process_details
        reason = await get_active_process_details(user_id)
        
        await callback.message.edit_text(
            f"⚠️ **У вас уже есть активная заявка или заказ.**\n\n"
            f"Причина: {reason}\n\n"
            "Вы не можете оформлять новые заявки/заказы, пока не будет завершен предыдущий процесс.\n"
            "Пожалуйста, дождитесь выполнения или отмените его в личном кабинете.",
            reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="cart_order")).as_markup()
        )
        await callback.answer("❌ Есть активная заявка", show_alert=True)
        return

    # Проверяем, есть ли товары в корзине
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT COUNT(*) FROM cart_order WHERE user_id = ?
        """, (user_id,))
        count = (await cursor.fetchone())[0]

    if count == 0:
        await callback.answer("❌ Корзина пуста", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="cart_order_confirm"))
    builder.add(types.InlineKeyboardButton(text="✏️ Редактировать корзину", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="cart_order"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Оформление заказа**\n\n"
        "Все заявки из корзины будут оформлены как единый заказ.\n"
        "После подтверждения заявка отправится администратору.\n\n"
        "Подтвердить оформление?",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "cart_order_confirm")
async def cart_order_confirm(callback: CallbackQuery):
    """Подтверждение заказа из корзины"""
    user_id = callback.from_user.id

    # Получаем товары из корзины
    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        cursor = await db.execute("""
            SELECT c.item_id, c.quantity, c.selected_options, c.price,
                   o.title, o.operation, o.item_type, o.category,
                   o.condition, o.purpose, o.specifications
            FROM cart_order c
            LEFT JOIN order_requests o ON c.item_id = o.id AND c.item_type IN ('order_request', 'товар', 'product', 'offer')
            WHERE c.user_id = ?
        """, (user_id,))
        items = await cursor.fetchall()

        if not items:
            await callback.answer("❌ Корзина пуста", show_alert=True)
            return

        # Формируем описание заказа
        order_description = "Заказ из корзины заявок:\n\n"
        total_price = 0

        for item in items:
            item_id, quantity, options, price, title, operation, item_type_detail, category, condition, purpose, specifications = item

            # Расчет стоимости
            try:
                item_price = float(price) if price else 0
                item_total = item_price * quantity
                total_price += item_total
            except ValueError:
                item_price = 0
                item_total = 0

            order_description += f"📦 **{title or f'Заявка #{item_id}'}**\n"
            order_description += f"   🆔 ID заявки: {item_id}\n"
            order_description += f"   📦 Количество: {quantity}\n"
            if options:
                order_description += f"   ⚙️ Опции: {options}\n"
            if item_price > 0:
                order_description += f"   💰 Цена за ед.: {item_price} руб.\n"
                order_description += f"   💵 Сумма: {item_total} руб.\n"
            if category:
                order_description += f"   🏷 Категория: {category}\n"
            if item_type_detail:
                order_description += f"   📋 Тип: {item_type_detail}\n"
            if condition:
                order_description += f"   🔧 Состояние: {condition}\n"
            if purpose:
                order_description += f"   🎯 Назначение: {purpose}\n"
            if operation:
                operation_text = "Покупка" if operation == "buy" else "Продажа" if operation == "sell" else operation
                order_description += f"   🎯 Операция: {operation_text}\n"
            order_description += "\n"

        if total_price > 0:
            order_description += f"💰 **Общая сумма заказа:** {total_price:.2f} руб.\n\n"

        order_description += f"👤 **Пользователь:** ID {user_id}\n"
        order_description += f"📅 **Дата оформления:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"

        # Создаем записи в таблице orders для каждого товара
        created_orders_count = 0
        for item in items:
            item_id, quantity, options, price, title, operation, item_type_detail, category, condition, purpose, specifications = item
            
            # Находим продавца
            cursor = await db.execute("SELECT user_id, item_type FROM order_requests WHERE id = ?", (item_id,))
            seller_row = await cursor.fetchone()
            seller_id = seller_row[0] if seller_row else None
            
            # Определяем тип заказа (product, service, offer)
            # Используем item_type_detail, если он есть, иначе fallback на operation или seller data
            final_order_type = 'service' # Default
            if item_type_detail in ('product', 'offer', 'товар', 'предложение'):
                final_order_type = 'product' if item_type_detail in ('product', 'товар') else 'offer'
            elif item_type_detail in ('service', 'услуга'):
                final_order_type = 'service'
            elif seller_row and seller_row[1]:
                # Fallback to DB
                db_type = seller_row[1]
                if db_type in ('product', 'offer'):
                     final_order_type = db_type
                elif db_type == 'service':
                     final_order_type = 'service'

            # Вставляем в orders
            await db.execute("""
                INSERT INTO orders (user_id, order_type, item_id, seller_id, status, order_date, notes)
                VALUES (?, ?, ?, ?, 'new', ?, ?)
            """, (
                user_id, 
                final_order_type,
                item_id, 
                seller_id, 
                datetime.now().isoformat(),
                f"Заказ из корзины. Кол-во: {quantity}. Цена: {price}. Опции: {options}"
            ))
            
            # Обновляем статус исходной заявки на 'processing' (или удаляем, если требуется)
            # Пользователь спрашивал "почему заявка не удалилась". Помечаем как 'processing'.
            if item_id:
                await db.execute("UPDATE order_requests SET status = 'processing' WHERE id = ?", (item_id,))
            
            created_orders_count += 1
            
            # Уведомляем продавца
            if seller_id and seller_id != user_id:
                await send_system_message(
                    seller_id,
                    "📦 Новый заказ!",
                    f"Пользователь оформил заказ на ваш товар: {title}.\nКоличество: {quantity}\nПроверьте Google Таблицу 'Заказы'."
                )

        # Очищаем корзину после оформления
        print(f"[DEBUG] Очистка корзины для пользователя {user_id}...")
        cursor = await db.execute("DELETE FROM cart_order WHERE user_id = ?", (user_id,))
        print(f"[DEBUG] Удалено строк из корзины: {cursor.rowcount}")
        await db.commit()
        print(f"[DEBUG] Заказы созданы: {created_orders_count}")

    # Синхронизация с Google Sheets (теперь и заказов)
    try:
        from google_sheets import sync_orders_to_sheets
        await sync_orders_to_sheets()
    except Exception as e:
        print(f"Ошибка синхронизации заказов: {e}")
        # Fallback to requests sync if orders sync fails or not exists yet
        try:
             from google_sheets import sync_order_requests_to_sheets
             await sync_order_requests_to_sheets()
        except:
             pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🏠 В личный кабинет", callback_data="personal_account"))
    builder.add(types.InlineKeyboardButton(text="🛒 К корзине", callback_data="cart_order"))
    builder.adjust(1)

    from config import ADMIN_ID

    if user_id == ADMIN_ID:
        message_text = (
            "✅ **Заказ успешно оформлен!**\n\n"
            "Заявки сохранены в базе данных.\n"
            "Корзина очищена."
        )
    else:
        message_text = (
            "✅ **Заказ успешно оформлен!**\n\n"
            "Все заявки из корзины отправлены администратору.\n"
            "Корзина очищена.\n\n"
            "Администратор свяжется с вами для уточнения деталей."
        )

    await callback.message.edit_text(
        message_text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "cart_order_clear")
async def cart_order_clear(callback: CallbackQuery):
    """Очистка корзины"""
    user_id = callback.from_user.id

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✅ Да, очистить", callback_data="cart_order_clear_confirm"))
    builder.add(types.InlineKeyboardButton(text="❌ Нет, отмена", callback_data="cart_order"))
    builder.adjust(2)

    await callback.message.edit_text(
        "🗑 **Очистка корзины**\n\n"
        "Вы уверены, что хотите удалить все заявки из корзины?\n"
        "Это действие нельзя отменить.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "cart_order_clear_confirm")
async def cart_order_clear_confirm(callback: CallbackQuery):
    """Подтверждение очистки корзины"""
    user_id = callback.from_user.id

    async with aiosqlite.connect("/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager/shared_storage/bot_database.db") as db:
        await db.execute("DELETE FROM cart_order WHERE user_id = ?", (user_id,))
        await db.commit()

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔄 Обновить корзину", callback_data="cart_order"))
    builder.add(types.InlineKeyboardButton(text="📝 Создать заявку", callback_data="create_order"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🗑 **Корзина очищена**\n\n"
        "Все заявки удалены из корзины.\n"
        "Новые активные заявки появятся в корзине автоматически.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()