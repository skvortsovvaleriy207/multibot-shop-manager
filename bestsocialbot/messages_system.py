from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user
from config import ADMIN_ID


class MessageStates(StatesGroup):
    COMPOSE_SUBJECT = State()
    COMPOSE_TEXT = State()
    COMPOSE_RECIPIENT = State()


@dp.callback_query(F.data == "messages")
async def messages_menu(callback: CallbackQuery):
    """Система сообщений согласно ТЗ п.1.10"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    # Получаем количество непрочитанных сообщений
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE recipient_id = ? AND is_read = 0",
            (user_id,)
        )
        unread_count = (await cursor.fetchone())[0]

    builder = InlineKeyboardBuilder()

    inbox_text = f"📥 Входящие ({unread_count})" if unread_count > 0 else "📥 Входящие"
    builder.add(types.InlineKeyboardButton(text=inbox_text, callback_data="messages_inbox"))
    builder.add(types.InlineKeyboardButton(text="📤 Отправленные", callback_data="messages_sent"))
    builder.add(types.InlineKeyboardButton(text="✍️ Написать сообщение", callback_data="compose_message"))
    builder.add(types.InlineKeyboardButton(text="👤 Администратору", callback_data="message_admin"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(2, 1, 1, 1)

    text = "💬 **Система сообщений**\n\n"
    text += "Здесь вы можете:\n"
    text += "• Просматривать входящие сообщения\n"
    text += "• Отправлять сообщения другим пользователям\n"
    text += "• Написать администратору\n"
    text += "• Получать уведомления о заказах\n"
    text += "• Общаться с администрацией"

    if unread_count > 0:
        text += f"\n\n🔔 У вас {unread_count} непрочитанных сообщений"

    if callback.message.content_type == types.ContentType.TEXT:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "message_admin")
async def message_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начать написание сообщения администратору"""
    if await check_blocked_user(callback):
        return

    await callback.message.edit_text(
        "👤 **Сообщение администратору**\n\n"
        "Введите тему сообщения:"
    )
    await state.update_data(recipient_id=ADMIN_ID)
    await state.set_state(MessageStates.COMPOSE_SUBJECT)
    await callback.answer()


@dp.callback_query(F.data == "compose_message")
async def compose_message_start(callback: CallbackQuery, state: FSMContext):
    """Начать написание сообщения"""
    if await check_blocked_user(callback):
        return

    await callback.message.edit_text(
        "✍️ **Новое сообщение**\n\n"
        "Введите ID получателя:"
    )
    await state.set_state(MessageStates.COMPOSE_RECIPIENT)
    await callback.answer()


@dp.message(MessageStates.COMPOSE_RECIPIENT)
async def compose_recipient(message: Message, state: FSMContext):
    """Получить ID получателя"""
    try:
        recipient_id = int(message.text.strip())
        await state.update_data(recipient_id=recipient_id)
        await message.answer(
            f"✍️ **Получатель:** ID{recipient_id}\n\n"
            "Теперь введите тему сообщения:"
        )
        await state.set_state(MessageStates.COMPOSE_SUBJECT)
    except ValueError:
        await message.answer("❌ ID получателя должен быть числом. Попробуйте еще раз:")


@dp.message(MessageStates.COMPOSE_SUBJECT)
async def compose_subject(message: Message, state: FSMContext):
    """Получить тему сообщения"""
    subject = message.text.strip()
    if len(subject) > 100:
        await message.answer("❌ Тема слишком длинная (максимум 100 символов)")
        return

    await state.update_data(subject=subject)
    await message.answer(
        f"✍️ **Тема:** {subject}\n\n"
        "Теперь введите текст сообщения:"
    )
    await state.set_state(MessageStates.COMPOSE_TEXT)


@dp.message(MessageStates.COMPOSE_TEXT)
async def compose_text(message: Message, state: FSMContext):
    """Получить текст сообщения"""
    message_text = message.text.strip()
    if len(message_text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (максимум 1000 символов)")
        return

    data = await state.get_data()
    subject = data.get("subject", "Без темы")
    recipient_id = data.get("recipient_id")
    sender_id = message.from_user.id

    # Сохраняем сообщение в БД
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""
            INSERT INTO messages (sender_id, recipient_id, subject, message_text, sent_at, is_read)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (sender_id, recipient_id, subject, message_text, datetime.now().isoformat()))
        await db.commit()

    # Отправляем уведомление получателю
    try:
        from bot_instance import bot
        await bot.send_message(
            recipient_id,
            f"📧 **Новое сообщение**\n\n"
            f"👤 **От:** @{message.from_user.username or message.from_user.id}\n"
            f"📋 **Тема:** {subject}\n\n"
            f"💬 **Сообщение:**\n{message_text}"
        )
    except Exception as e:
        print(f"Ошибка отправки уведомления получателю: {e}")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📤 К отправленным", callback_data="messages_sent"))
    builder.add(types.InlineKeyboardButton(text="💬 К сообщениям", callback_data="messages"))

    await message.answer(
        "✅ **Сообщение отправлено!**\n\n"
        f"📋 **Тема:** {subject}\n"
        f"👤 **Получатель:** ID{recipient_id}\n\n"
        "Ответ придет в ваши входящие сообщения.",
        reply_markup=builder.as_markup()
    )
    await state.clear()


async def send_system_message(recipient_id: int, subject: str, message_text: str):
    """Отправить системное сообщение пользователю"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("""
                INSERT INTO messages (sender_id, recipient_id, subject, message_text, sent_at, is_read)
                VALUES (NULL, ?, ?, ?, ?, 0)
            """, (recipient_id, subject, message_text, datetime.now().isoformat()))
            await db.commit()

        # Уведомляем пользователя
        from bot_instance import bot
        await bot.send_message(
            recipient_id,
            f"📧 **Новое сообщение**\n\n"
            f"📋 **{subject}**\n\n"
            f"{message_text}\n\n"
            f"💬 Проверьте раздел 'Сообщения' в личном кабинете"
        )
    except Exception as e:
        print(f"Ошибка отправки системного сообщения: {e}")


async def notify_admin_new_order_request(user_id: int, request_id: int, request_data: dict):
    """Отправить админу уведомление о новой заявке"""
    try:
        user_info = f"@{user_id}"

        # Получаем информацию о пользователе из БД
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(
                "SELECT username, full_name FROM users WHERE user_id = ?",
                (user_id,)
            )
            user_data = await cursor.fetchone()
            if user_data:
                username, full_name = user_data
                user_info = f"@{username}" if username else full_name if full_name else f"ID{user_id}"

        subject = f"📋 Новая заявка #{request_id}"

        # Формируем текст сообщения на основе данных заявки
        message_text = f"👤 **Пользователь:** {user_info} (ID{user_id})\n"
        message_text += f"🎯 **Цель:** {request_data.get('operation', 'Не указано')}\n"
        message_text += f"📋 **Тип:** {request_data.get('item_type', 'Не указано')}\n"

        # Для товаров и предложений
        if request_data.get('item_type') in ['product', 'offer']:
            message_text += f"🏷 **Категория:** {request_data.get('category', 'Не указано')}\n"
            message_text += f"📊 **Класс:** {request_data.get('item_class', 'Не указано')}\n"
            message_text += f"🔧 **Тип:** {request_data.get('item_type_detail', 'Не указано')}\n"
            message_text += f"👁 **Вид:** {request_data.get('item_kind', 'Не указано')}\n"
            message_text += f"🔢 **ID в каталоге:** {request_data.get('catalog_id', 'Не указано')}\n"

        message_text += f"📝 **Название:** {request_data.get('title', 'Не указано')}\n"

        if request_data.get('purpose'):
            message_text += f"🎯 **Назначение:** {request_data.get('purpose')}\n"

        if request_data.get('name'):
            message_text += f"🏢 **Производитель/Бренд:** {request_data.get('name')}\n"

        if request_data.get('creation_date'):
            message_text += f"📅 **Дата создания:** {request_data.get('creation_date')}\n"

        if request_data.get('condition'):
            message_text += f"🔄 **Состояние:** {request_data.get('condition')}\n"

        if request_data.get('price'):
            message_text += f"💰 **Цена:** {request_data.get('price')}\n"

        if request_data.get('deadline'):
            message_text += f"⏰ **Срок:** {request_data.get('deadline')}\n"

        message_text += f"📞 **Контакты:** {request_data.get('contact', 'Не указано')}\n\n"
        message_text += f"📅 **Дата создания заявки:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"

        message_text += "**📋 Детали заявки:**\n"
        message_text += "1. **Для одобрения:** Проверьте данные заявки\n"
        message_text += "2. **Для отклонения:** Укажите причину в ответе пользователю\n"
        message_text += "3. **Для добавления в каталог:** Используйте админ-панель\n\n"

        message_text += "**💬 Действия:**\n"
        message_text += "✅ Одобрить - добавьте в каталог\n"
        message_text += "❌ Отклонить - ответьте пользователю с причиной\n"
        message_text += "🔄 На доработку - запросите доп. информацию"

        # Используем уже существующий функционал отправки сообщений
        # Сохраняем сообщение в БД
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("""
                INSERT INTO messages (sender_id, recipient_id, subject, message_text, sent_at, is_read)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (user_id, ADMIN_ID, subject, message_text, datetime.now().isoformat()))
            await db.commit()

        # Отправляем уведомление админу через существующий функционал
        await send_system_message(ADMIN_ID, subject, message_text)

        print(f"✅ Отправлено уведомление админу о новой заявке #{request_id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления админу: {e}")
        return False


async def notify_admin_new_category(category_type: str, value: str, user_id: int, username: str, item_type: str):
    """Отправляет уведомление админу о новой категории"""
    try:
        from config import ADMIN_ID

        # Формируем понятное название типа категории
        category_names = {
            'category': 'категория',
            'class': 'класс',
            'type': 'тип',
            'kind': 'вид'
        }

        category_type_name = category_names.get(category_type, category_type)

        # Формируем понятное название типа товара/услуги/предложения
        item_type_names = {
            'product': 'товара',
            'service': 'услуги',
            'offer': 'предложения'
        }

        item_type_name = item_type_names.get(item_type, item_type)

        # Формируем текст уведомления
        message_text = (
            f"🆕 **Запрос на добавление новой {category_type_name}**\n\n"
            f"📦 **Тип карточки:** {item_type_name.capitalize()}\n"
            f"📝 **Название {category_type_name}:** {value}\n"
            f"👤 **Пользователь:** @{username if username else 'без username'} (ID: {user_id})\n"
            f"⏰ **Время запроса:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"**📋 Действия администратора:**\n"
            f"1. Проверить корректность названия\n"
            f"2. Добавить в соответствующую таблицу БД:\n"
        )

        # Добавляем информацию о таблице БД в зависимости от типа карточки
        table_name = ""
        if item_type == 'product':
            if category_type == 'category':
                table_name = "product_purposes"
            elif category_type == 'class':
                table_name = "product_classes"
            elif category_type == 'type':
                table_name = "product_types"
            elif category_type == 'kind':
                table_name = "product_views"
        elif item_type == 'service':
            if category_type == 'category':
                table_name = "service_purposes"
            elif category_type == 'class':
                table_name = "service_classes"
            elif category_type == 'type':
                table_name = "service_types"
            elif category_type == 'kind':
                table_name = "service_views"
        else:  # offer
            # Предложения используют таблицы товаров
            if category_type == 'category':
                table_name = "product_purposes"
            elif category_type == 'class':
                table_name = "product_classes"
            elif category_type == 'type':
                table_name = "product_types"
            elif category_type == 'kind':
                table_name = "product_views"

        message_text += f"   - Таблица: `{table_name}`\n\n"
        message_text += f"**⚙️ Управление:**\n"
        message_text += f"Используйте **Админ Панель** -> **Магазин** -> **Каталог товаров** -> **{category_names.get(category_type, category_type).capitalize()}** для добавления.\n"

        # Сохраняем уведомление в БД для админа
        try:
            async with aiosqlite.connect("bot_database.db") as db:
                await db.execute("""
                    INSERT INTO messages (sender_id, recipient_id, subject, message_text, sent_at, is_read)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (
                    user_id,
                    ADMIN_ID,
                    f"Запрос на добавление {category_type_name}",
                    message_text,
                    datetime.now().isoformat()
                ))
                await db.commit()
        except Exception as db_error:
            print(f"❌ Ошибка сохранения в БД: {db_error}")
            # Продолжаем отправку даже если ошибка БД

        # Отправляем уведомление через существующий функционал
        try:

            await send_system_message(
                ADMIN_ID,
                f"Запрос на добавление {category_type_name}",
                message_text
            )
        except Exception as send_error:
            print(f"❌ Ошибка отправки сообщения: {send_error}")
            # Отправляем напрямую
            try:
                from bot_instance import bot
                await bot.send_message(ADMIN_ID, message_text)
            except Exception as bot_error:
                print(f"❌ Ошибка прямой отправки: {bot_error}")

        print(f"✅ Отправлено уведомление админу о новой {category_type_name}: {value}")
        return True

    except Exception as e:
        print(f"❌ Ошибка отправки уведомления админу о новой категории: {e}")
        return False


async def notify_order_status_change(user_id: int, order_id: int, new_status: str, item_title: str):
    """Уведомление об изменении статуса заказа согласно ТЗ п.1.10"""
    subject = f"Изменение статуса заказа #{order_id}"
    message_text = (
        f"Статус вашего заказа изменился:\n\n"
        f"🚗 Товар/Услуга: {item_title}\n"
        f"📊 Новый статус: {new_status}\n"
        f"📅 Дата изменения: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Вы можете отслеживать статус заказа в разделе 'Мои заказы'"
    )
    await send_system_message(user_id, subject, message_text)

async def send_order_request_to_admin(user_id: int, request_id: int, state_data: dict):
    """Отправить полную заявку админу для одобрения"""
    try:
        # Получаем информацию о пользователе
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(
                "SELECT username, full_name FROM users WHERE user_id = ?",
                (user_id,)
            )
            user_data = await cursor.fetchone()
            if user_data:
                username, full_name = user_data
                user_info = f"@{username}" if username else full_name if full_name else f"ID{user_id}"
            else:
                user_info = f"ID{user_id}"

        # Формируем заголовок
        item_type = state_data.get('item_type', '')
        operation = state_data.get('operation', '')

        if item_type == 'product':
            title = f"🛒 Заявка на товар #{request_id}"
        elif item_type == 'service':
            title = f"🛠 Заявка на услугу #{request_id}"
        elif item_type == 'offer':
            title = f"🤝 Заявка на предложение #{request_id}"
        else:
            title = f"📋 Заявка #{request_id}"

        subject = f"{title} - {operation}"

        # Формируем полный текст заявки
        message_text = f"**👤 Пользователь:** {user_info} (ID{user_id})\n"
        message_text += f"**🎯 Цель:** {operation}\n"
        message_text += f"**📋 Тип:** {item_type}\n"
        message_text += f"**📅 Дата создания:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"

        message_text += "**📊 КАТЕГОРИИ:**\n"
        message_text += f"🏷 Категория: {state_data.get('category', 'Не указано')}\n"
        message_text += f"📊 Класс: {state_data.get('item_class', 'Не указано')}\n"
        message_text += f"🔧 Тип: {state_data.get('item_type', 'Не указано')}\n"
        message_text += f"👁 Вид: {state_data.get('item_kind', 'Не указано')}\n"
        message_text += f"🔢 ID в каталоге: {state_data.get('catalog_id', 'Не указано')}\n\n"

        message_text += "**📝 ОСНОВНАЯ ИНФОРМАЦИЯ:**\n"
        message_text += f"📋 Название: {state_data.get('title', 'Не указано')}\n"

        if state_data.get('purpose'):
            message_text += f"🎯 Назначение: {state_data.get('purpose')}\n"

        if state_data.get('name'):
            message_text += f"🏢 Производитель/Бренд: {state_data.get('name')}\n"

        if state_data.get('creation_date'):
            message_text += f"📅 Дата создания: {state_data.get('creation_date')}\n"

        if state_data.get('condition'):
            message_text += f"🔄 Состояние: {state_data.get('condition')}\n\n"

        message_text += "**⚙️ ХАРАКТЕРИСТИКИ:**\n"
        if state_data.get('specifications'):
            message_text += f"📊 Основные характеристики:\n{state_data.get('specifications')}\n"

        if state_data.get('advantages'):
            message_text += f"✅ Преимущества:\n{state_data.get('advantages')}\n"

        if state_data.get('detailed_specs'):
            message_text += f"🔧 Детальные характеристики:\n{state_data.get('detailed_specs')}\n\n"

        message_text += "**💰 ФИНАНСОВАЯ ИНФОРМАЦИЯ:**\n"
        if state_data.get('price'):
            message_text += f"💵 Цена: {state_data.get('price')}\n"

        if state_data.get('pricing'):
            message_text += f"📋 Прайс работ и материалов:\n{state_data.get('pricing')}\n"

        if state_data.get('guarantees'):
            message_text += f"🛡️ Гарантии: {state_data.get('guarantees')}\n\n"

        message_text += "**📦 ДОПОЛНИТЕЛЬНО:**\n"
        if state_data.get('availability'):
            message_text += f"📍 Наличие: {state_data.get('availability')}\n"

        if state_data.get('delivery_info'):
            message_text += f"🚚 Доставка: {state_data.get('delivery_info')}\n"

        if state_data.get('supplier_info'):
            message_text += f"🏢 Поставщик: {state_data.get('supplier_info')}\n"

        if state_data.get('reviews'):
            message_text += f"⭐ Отзывы: {state_data.get('reviews')}\n"

        if state_data.get('rating'):
            message_text += f"🌟 Рейтинг: {state_data.get('rating')}/10\n"

        if state_data.get('statistics'):
            message_text += f"📈 Статистика: {state_data.get('statistics')}\n"

        if state_data.get('deadline'):
            message_text += f"⏰ Сроки: {state_data.get('deadline')}\n"

        if state_data.get('additional_info'):
            message_text += f"📄 Дополнительно: {state_data.get('additional_info')}\n"

        if state_data.get('tags'):
            message_text += f"🏷️ Теги: {state_data.get('tags')}\n\n"

        message_text += f"**📞 КОНТАКТЫ:**\n{state_data.get('contact', 'Не указано')}\n\n"

        message_text += "**✅ ЗАЯВКА СОЗДАНА И ОЖИДАЕТ ОДОБРЕНИЯ**\n\n"
        message_text += "**🔔 Действия администратора:**\n"
        message_text += "1. Проверить корректность данных\n"
        message_text += "2. Одобрить или отклонить заявку\n"
        message_text += "3. При одобрении - добавить в соответствующий каталог\n"
        message_text += "4. Уведомить пользователя о результате\n\n"
        message_text += "**📋 Для одобрения:** Используйте админ-панель\n"
        message_text += "**💬 Для связи:** Отправьте сообщение пользователю"

        # Сохраняем полную заявку как сообщение админу
        async with aiosqlite.connect("bot_database.db") as db:
            await db.execute("""
                INSERT INTO messages (sender_id, recipient_id, subject, message_text, sent_at, is_read)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (user_id, ADMIN_ID, subject, message_text, datetime.now().isoformat()))
            await db.commit()

        # Формируем клавиатуру для админа
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve_req_{item_type}_{request_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"edit_req_{item_type}_{request_id}"
        ))
        builder.add(types.InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject_req_{item_type}_{request_id}"
        ))
        builder.adjust(2, 1)

        # Отправляем через существующий функционал, но подменяем на прямую отправку для кнопок
        # Так как send_system_message не поддерживает кнопки, отправляем напрямую ботом
        from bot_instance import bot
        await bot.send_message(
            ADMIN_ID,
            f"📧 **Новое сообщение**\n\n📋 **{subject}**\n\n{message_text}",
            reply_markup=builder.as_markup()
        )

        print(f"✅ Полная заявка #{request_id} отправлена админу для одобрения")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки полной заявки админу: {e}")
        return False

async def notify_new_order(seller_id: int, order_id: int, item_title: str, buyer_username: str):
    """Уведомление продавцу о новом заказе согласно ТЗ п.1.10"""
    subject = f"Новый заказ #{order_id}"
    message_text = (
        f"У вас новый заказ!\n\n"
        f"📦 Товар/Услуга: {item_title}\n"
        f"👤 Покупатель: @{buyer_username}\n"
        f"📅 Дата заказа: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Проверьте раздел 'Заказы на мои товары' для обработки заказа"
    )
    await send_system_message(seller_id, subject, message_text)


# Остальные функции остаются без изменений...

@dp.callback_query(F.data == "messages_inbox")
async def messages_inbox(callback: CallbackQuery):
    """Входящие сообщения"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT m.id, m.sender_id, m.subject, m.message_text, m.sent_at, m.is_read, u.username
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.user_id
            WHERE m.recipient_id = ?
            ORDER BY m.sent_at DESC
            LIMIT 20
        """, (user_id,))

        messages = await cursor.fetchall()

    if not messages:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ К сообщениям", callback_data="messages"))

        await callback.message.edit_text(
            "📥 **Входящие сообщения**\n\n❌ У вас нет сообщений",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    text = "📥 **Входящие сообщения**\n\n"
    builder = InlineKeyboardBuilder()

    for msg_id, sender_id, subject, message_text, sent_at, is_read, username in messages[:10]:
        status = "🔴" if not is_read else "✅"
        sender_name = f"@{username}" if username else f"ID{sender_id}" if sender_id else "Система"
        date = sent_at[:10] if sent_at else "Неизвестно"

        button_text = f"{status} {subject[:25]}... ({sender_name})"
        builder.add(types.InlineKeyboardButton(
            text=button_text,
            callback_data=f"read_message_{msg_id}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ К сообщениям", callback_data="messages"))
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "messages_sent")
async def messages_sent(callback: CallbackQuery):
    """Отправленные сообщения"""
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT m.id, m.recipient_id, m.subject, m.message_text, m.sent_at, u.username
            FROM messages m
            LEFT JOIN users u ON m.recipient_id = u.user_id
            WHERE m.sender_id = ?
            ORDER BY m.sent_at DESC
            LIMIT 20
        """, (user_id,))

        messages = await cursor.fetchall()

    if not messages:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ К сообщениям", callback_data="messages"))

        await callback.message.edit_text(
            "📤 **Отправленные сообщения**\n\n❌ Вы не отправляли сообщений",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    text = "📤 **Отправленные сообщения**\n\n"
    builder = InlineKeyboardBuilder()

    for msg_id, recipient_id, subject, message_text, sent_at, username in messages[:10]:
        recipient_name = f"@{username}" if username else f"ID{recipient_id}"
        date = sent_at[:10] if sent_at else "Неизвестно"

        button_text = f"📤 {subject[:25]}... → {recipient_name}"
        builder.add(types.InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_sent_{msg_id}"
        ))

    builder.add(types.InlineKeyboardButton(text="◀️ К сообщениям", callback_data="messages"))
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("read_message_"))
async def read_message(callback: CallbackQuery):
    """Прочитать входящее сообщение"""
    if await check_blocked_user(callback):
        return

    message_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT m.sender_id, m.subject, m.message_text, m.sent_at, u.username
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.user_id
            WHERE m.id = ? AND m.recipient_id = ?
        """, (message_id, user_id))

        message = await cursor.fetchone()

        if message:
            # Отмечаем как прочитанное
            await db.execute(
                "UPDATE messages SET is_read = 1 WHERE id = ?",
                (message_id,)
            )
            await db.commit()

    if not message:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return

    sender_id, subject, message_text, sent_at, username = message
    sender_name = f"@{username}" if username else f"ID{sender_id}" if sender_id else "Система"
    date = sent_at[:16] if sent_at else "Неизвестно"

    text = f"📧 **{subject}**\n\n"
    text += f"👤 **От:** {sender_name}\n"
    text += f"📅 **Дата:** {date}\n\n"
    text += f"💬 **Сообщение:**\n{message_text}"

    builder = InlineKeyboardBuilder()
    if sender_id:  # Если есть отправитель (не системное сообщение)
        builder.add(types.InlineKeyboardButton(text="↩️ Ответить", callback_data=f"reply_{sender_id}"))
    builder.add(types.InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_message_{message_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ К входящим", callback_data="messages_inbox"))
    builder.adjust(2, 1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_message_"))
async def delete_message(callback: CallbackQuery):
    """Удалить сообщение"""
    if await check_blocked_user(callback):
        return

    try:
        message_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id

        async with aiosqlite.connect("bot_database.db") as db:
            # Проверяем, принадлежит ли сообщение пользователю (как получателю или отправителю)
            cursor = await db.execute("""
                SELECT id FROM messages 
                WHERE id = ? AND (recipient_id = ? OR sender_id = ?)
            """, (message_id, user_id, user_id))
            
            if not await cursor.fetchone():
                await callback.answer("Сообщение не найдено или доступ запрещен", show_alert=True)
                return

            # Удаляем сообщение
            await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            await db.commit()

        await callback.answer("✅ Сообщение удалено", show_alert=True)
        
        # Возвращаемся во входящие
        await messages_inbox(callback)

    except Exception as e:
        print(f"Ошибка удаления сообщения: {e}")
        await callback.answer("❌ Ошибка при удалении", show_alert=True)