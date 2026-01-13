from aiogram import F, types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime
from dispatcher import dp
from utils import check_blocked_user
from messages_system import notify_admin_new_category, send_order_request_to_admin


class ProductCardForm(StatesGroup):
    """Состояния для формы карточки товара"""
    waiting_operation = State()
    editing_form = State()
    waiting_for_value = State()
    selecting_category = State()
    selecting_class = State()
    selecting_type = State()
    selecting_kind = State()


class ServiceCardForm(StatesGroup):
    """Состояния для формы карточки услуги"""
    waiting_operation = State()
    editing_form = State()
    waiting_for_value = State()
    selecting_category = State()
    selecting_class = State()
    selecting_type = State()
    selecting_kind = State()


class OfferCardForm(StatesGroup):
    """Состояния для формы карточки предложения"""
    waiting_operation = State()
    editing_form = State()
    waiting_for_value = State()
    selecting_category = State()
    selecting_class = State()
    selecting_type = State()
    selecting_kind = State()


@dp.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания заявки"""
    if await check_blocked_user(callback):
        return

    # ОЧИЩАЕМ СОСТОЯНИЕ при начале создания новой карточки
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📋 Карточка товара", callback_data="product_card_form"))
    builder.add(types.InlineKeyboardButton(text="🔧 Карточка услуги", callback_data="service_card_form"))
    builder.add(types.InlineKeyboardButton(text="💼 Карточка предложения/актива", callback_data="offer_card_form"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Создание заявки**\n\n"
        "Выберите тип карточки:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ========== ШАБЛОНЫ КАРТОЧЕК ==========

PRODUCT_TEMPLATE = {
    "category": {"title": "📋 Категория", "value": None, "required": False, "type": "choice"},
    "item_class": {"title": "🏷️ Класс", "value": None, "required": False, "type": "choice"},
    "item_type": {"title": "🔧 Тип", "value": None, "required": False, "type": "choice"},
    "item_kind": {"title": "📊 Вид", "value": None, "required": False, "type": "choice"},
    "catalog_id": {"title": "🆔 ID в Каталоге", "value": None, "required": False, "type": "text"},
    "title": {"title": "📝 Название товара", "value": None, "required": False, "type": "text"},
    "purpose": {"title": "🎯 Назначение и способы использования", "value": None, "required": False, "type": "text"},
    "name": {"title": "🏷️ Наименование", "value": None, "required": False, "type": "text"},
    "creation_date": {"title": "📅 Дата создания/выпуска", "value": None, "required": False, "type": "text"},
    "condition": {"title": "⚙️ Состояние", "value": None, "required": False, "type": "text"},
    "specifications": {"title": "📋 Эксплуатационные характеристики", "value": None, "required": False, "type": "text"},
    "advantages": {"title": "⭐ Преимущества в сравнении с аналогами", "value": None, "required": False, "type": "text"},
    "additional_info": {"title": "ℹ️ Другая важная и полезная информация", "value": None, "required": False,
                        "type": "text"},
    "images": {"title": "🖼️ Изображения и/или видео", "value": None, "required": False, "type": "media"},
    "price": {"title": "💰 Цена", "value": None, "required": False, "type": "text"},
    "availability": {"title": "📦 Наличие", "value": None, "required": False, "type": "text"},
    "detailed_specs": {"title": "⚙️ Характеристики", "value": None, "required": False, "type": "text"},
    "reviews": {"title": "💬 Отзывы покупателей и экспертов", "value": None, "required": False, "type": "text"},
    "rating": {"title": "⭐ Рейтинг (из 10 звезд)", "value": None, "required": False, "type": "text"},
    "delivery_info": {"title": "🚚 Информация о доставке и оплате", "value": None, "required": False, "type": "text"},
    "supplier_info": {"title": "🏢 Поставщик-гарант товара", "value": None, "required": False, "type": "text"},
    "statistics": {"title": "📊 Статистика реализации", "value": None, "required": False, "type": "text"},
    "deadline": {"title": "⏱️ Сроки", "value": None, "required": False, "type": "text"},
    "tags": {"title": "🏷️ Теги/ключевые слова", "value": None, "required": False, "type": "text"},
    "contact": {"title": "📞 Контактная информация", "value": None, "required": False, "type": "text"},
}

SERVICE_TEMPLATE = {
    "category": {"title": "📋 Категория", "value": None, "required": False, "type": "choice"},
    "item_class": {"title": "🏷️ Класс", "value": None, "required": False, "type": "choice"},
    "item_type": {"title": "🔧 Тип", "value": None, "required": False, "type": "choice"},
    "item_kind": {"title": "📊 Вид", "value": None, "required": False, "type": "choice"},
    "catalog_id": {"title": "🆔 ID в Каталоге", "value": None, "required": False, "type": "text"},
    "service_date": {"title": "📅 Дата заявки/заказа/выполнения", "value": None, "required": False, "type": "text"},
    "title": {"title": "📝 Наименование и объем услуги", "value": None, "required": False, "type": "text"},
    "works": {"title": "🛠️ Перечень выполняемых работ", "value": None, "required": False, "type": "text"},
    "materials": {"title": "📦 Марки, типы, особенности материалов/деталей", "value": None, "required": False,
                  "type": "text"},
    "images": {"title": "🖼️ Информационные фото/видео", "value": None, "required": False, "type": "media"},
    "price": {"title": "💰 Стоимость и срок выполнения", "value": None, "required": False, "type": "text"},
    "pricing": {"title": "📋 Прайс работ и материалов", "value": None, "required": False, "type": "text"},
    "guarantees": {"title": "✅ Гарантии сервиса, скидки", "value": None, "required": False, "type": "text"},
    "conditions": {"title": "📄 Особые условия", "value": None, "required": False, "type": "text"},
    "supplier_info": {"title": "🏢 Реквизиты, лицензии, формы договоров", "value": None, "required": False,
                      "type": "text"},
    "reviews": {"title": "💬 Отзывы", "value": None, "required": False, "type": "text"},
    "rating": {"title": "⭐ Рейтинг услуги (из 10 звезд)", "value": None, "required": False, "type": "text"},
    "statistics": {"title": "📊 Статистика реализации", "value": None, "required": False, "type": "text"},
    "additional_info": {"title": "ℹ️ Иная информация", "value": None, "required": False, "type": "text"},
    "deadline": {"title": "⏱️ Сроки", "value": None, "required": False, "type": "text"},
    "tags": {"title": "🏷️ Теги/ключевые слова", "value": None, "required": False, "type": "text"},
    "contact": {"title": "📞 Контактная информация", "value": None, "required": False, "type": "text"},
}

OFFER_TEMPLATE = PRODUCT_TEMPLATE.copy()  # Предложение аналогично товару


# ========== КАРТОЧКА ТОВАРА ==========

@dp.callback_query(F.data == "product_card_form")
async def product_card_form_start(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения карточки товара - выбор операции"""
    if await check_blocked_user(callback):
        return

    # Очищаем состояние и начинаем новую карточку
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 Продать", callback_data="product_sell"))
    builder.add(types.InlineKeyboardButton(text="🛒 Купить", callback_data="product_buy"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="create_order"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Карточка товара**\n\n"
        "Выберите цель:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(item_type="product")
    await state.set_state(ProductCardForm.waiting_operation)
    await callback.answer()


@dp.callback_query(F.data == "product_sell")
async def product_select_sell(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Продать для товара"""
    await state.update_data(operation="sell")
    await show_product_form(callback.message, state)


@dp.callback_query(F.data == "product_buy")
async def product_select_buy(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Купить для товара"""
    await state.update_data(operation="buy")
    await show_product_form(callback.message, state)


async def show_product_form(message: Message, state: FSMContext):
    """Показывает форму карточки товара - всегда новая форма"""
    # Всегда создаем НОВУЮ форму при показе
    product_form = PRODUCT_TEMPLATE.copy()
    await state.update_data(
        product_form=product_form,
        current_form_type="product"
    )

    await show_form(message, state, "product")
    await state.set_state(ProductCardForm.editing_form)


# ========== КАРТОЧКА УСЛУГИ ==========

@dp.callback_query(F.data == "service_card_form")
async def service_card_form_start(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения карточки услуги - выбор операции"""
    if await check_blocked_user(callback):
        return

    # Очищаем состояние и начинаем новую карточку
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🛠 Предложить услугу", callback_data="service_offer"))
    builder.add(types.InlineKeyboardButton(text="🔧 Заказать услугу", callback_data="service_order"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="create_order"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Карточка услуги**\n\n"
        "Выберите цель:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(item_type="service")
    await state.set_state(ServiceCardForm.waiting_operation)
    await callback.answer()


@dp.callback_query(F.data == "service_offer")
async def service_select_offer(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Предложить услугу"""
    await state.update_data(operation="sell")
    await show_service_form(callback.message, state)


@dp.callback_query(F.data == "service_order")
async def service_select_order(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Заказать услугу"""
    await state.update_data(operation="buy")
    await show_service_form(callback.message, state)


async def show_service_form(message: Message, state: FSMContext):
    """Показывает форму карточки услуги - всегда новая форма"""
    # Всегда создаем НОВУЮ форму при показе
    service_form = SERVICE_TEMPLATE.copy()
    await state.update_data(
        service_form=service_form,
        current_form_type="service"
    )

    await show_form(message, state, "service")
    await state.set_state(ServiceCardForm.editing_form)


# ========== КАРТОЧКА ПРЕДЛОЖЕНИЯ ==========

@dp.callback_query(F.data == "offer_card_form")
async def offer_card_form_start(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения карточки предложения - выбор операции"""
    if await check_blocked_user(callback):
        return

    # Очищаем состояние и начинаем новую карточку
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 Продать", callback_data="offer_sell"))
    builder.add(types.InlineKeyboardButton(text="🛒 Купить", callback_data="offer_buy"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="create_order"))
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 **Карточка предложения/актива**\n\n"
        "Выберите цель:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(item_type="offer")
    await state.set_state(OfferCardForm.waiting_operation)
    await callback.answer()


@dp.callback_query(F.data == "offer_sell")
async def offer_select_sell(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Продать для предложения"""
    await state.update_data(operation="sell")
    await show_offer_form(callback.message, state)


@dp.callback_query(F.data == "offer_buy")
async def offer_select_buy(callback: CallbackQuery, state: FSMContext):
    """Выбор операции Купить для предложения"""
    await state.update_data(operation="buy")
    await show_offer_form(callback.message, state)


async def show_offer_form(message: Message, state: FSMContext):
    """Показывает форму карточки предложения - всегда новая форма"""
    # Всегда создаем НОВУЮ форму при показе
    offer_form = OFFER_TEMPLATE.copy()
    await state.update_data(
        offer_form=offer_form,
        current_form_type="offer"
    )

    await show_form(message, state, "offer")
    await state.set_state(OfferCardForm.editing_form)


# ========== ОБЩИЕ ФУНКЦИИ ДЛЯ ФОРМ ==========

async def show_form(message: Message, state: FSMContext, form_type: str, edit_message_id: int = None):
    """Показывает форму карточки - всегда создает новую при необходимости"""
    data = await state.get_data()

    # Проверяем, есть ли форма в состоянии, если нет - создаем новую
    if form_type == "product":
        if "product_form" not in data:
            product_form = PRODUCT_TEMPLATE.copy()
            await state.update_data(product_form=product_form)
        form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())
        title = "📦 КАРТОЧКА ТОВАРА"
        operation = data.get("operation", "")
        operation_text = "💰 Продать" if operation == "sell" else "🛒 Купить"
        title = f"{title} ({operation_text})"
    elif form_type == "service":
        if "service_form" not in data:
            service_form = SERVICE_TEMPLATE.copy()
            await state.update_data(service_form=service_form)
        form_data = data.get("service_form", SERVICE_TEMPLATE.copy())
        title = "🔧 КАРТОЧКА УСЛУГИ"
        operation = data.get("operation", "")
        operation_text = "🛠️ Предложить услугу" if operation == "sell" else "🔧 Заказать услугу"
        title = f"{title} ({operation_text})"
    else:  # offer
        if "offer_form" not in data:
            offer_form = OFFER_TEMPLATE.copy()
            await state.update_data(offer_form=offer_form)
        form_data = data.get("offer_form", OFFER_TEMPLATE.copy())
        title = "💼 КАРТОЧКА ПРЕДЛОЖЕНИЯ"
        operation = data.get("operation", "")
        operation_text = "💰 Продать" if operation == "sell" else "🛒 Купить"
        title = f"{title} ({operation_text})"

    # Формируем текст формы
    form_text = f"<b>{title}</b>\n"
    form_text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    filled_count = 0
    total_fields = len(form_data)

    for field_key, field_info in form_data.items():
        value = field_info.get("value")
        status = "✅" if value else "⬜"

        # Форматируем значение для отображения
        if value:
            if field_info.get("type") == "media" and value:
                display_value = f"[{len(value.split(','))} файлов]" if value else "[Нет файлов]"
            else:
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
            filled_count += 1
        else:
            display_value = "__________"

        form_text += f"{status} <b>{field_info['title']}:</b>\n"
        form_text += f"   <i>{display_value}</i>\n\n"

    form_text += "━━━━━━━━━━━━━━━━━━━━\n"
    form_text += f"Заполнено: {filled_count}/{total_fields} полей\n\n"
    form_text += "Нажмите на поле для редактирования ⬇️"

    # Создаем клавиатуру
    keyboard = await generate_form_keyboard(form_data, form_type)

    if edit_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=edit_message_id,
                text=form_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except:
            # Если не удалось редактировать (сообщение старое), отправляем новое
            await message.answer(form_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(form_text, reply_markup=keyboard, parse_mode="HTML")


async def generate_form_keyboard(form_data: dict, form_type: str) -> InlineKeyboardBuilder:
    """Генерирует клавиатуру для формы"""
    builder = InlineKeyboardBuilder()

    # Группируем поля
    basic_fields = []
    details_fields = []
    media_fields = []
    contact_fields = []

    for field_key, field_info in form_data.items():
        if field_key in ["category", "item_class", "item_type", "item_kind", "catalog_id", "title"]:
            basic_fields.append((field_key, field_info))
        elif field_key in ["images", "price", "availability"]:
            media_fields.append((field_key, field_info))
        elif field_key == "contact":
            contact_fields.append((field_key, field_info))
        else:
            details_fields.append((field_key, field_info))

    # Кнопки основных полей
    for field_key, field_info in basic_fields[:6]:
        emoji = "✅" if field_info.get("value") else "⬜"
        text = f"{emoji} {field_info['title'][:15]}"
        builder.button(
            text=text,
            callback_data=f"edit_{form_type}_{field_key}"
        )

    builder.adjust(2)

    # Кнопки медиа и цены
    if media_fields:
        builder.row()
        for field_key, field_info in media_fields:
            emoji = "✅" if field_info.get("value") else "⬜"
            text = f"{emoji} {field_info['title'][:15]}"
            builder.button(
                text=text,
                callback_data=f"edit_{form_type}_{field_key}"
            )
        builder.adjust(2)

    # Кнопка "Еще поля"
    builder.row(
        types.InlineKeyboardButton(
            text="⏩ Еще поля",
            callback_data=f"more_fields_{form_type}_1"
        )
    )

    # Основные действия
    builder.row(
        types.InlineKeyboardButton(
            text="👁️ Предпросмотр",
            callback_data=f"preview_{form_type}"
        ),
        types.InlineKeyboardButton(
            text="💾 Сохранить",
            callback_data=f"save_{form_type}"
        )
    )

    # Кнопка назад
    if form_type == "product":
        back_callback = "product_card_form"
    elif form_type == "service":
        back_callback = "service_card_form"
    else:
        back_callback = "offer_card_form"

    builder.row(
        types.InlineKeyboardButton(
            text="◀️ Назад к выбору операции",
            callback_data=back_callback
        )
    )

    return builder.as_markup()


async def show_more_fields(message: Message, state: FSMContext, form_type: str, page: int):
    """Показывает дополнительные поля формы"""
    data = await state.get_data()

    if form_type == "product":
        form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())
    elif form_type == "service":
        form_data = data.get("service_form", SERVICE_TEMPLATE.copy())
    else:
        form_data = data.get("offer_form", OFFER_TEMPLATE.copy())

    # Сортируем поля для постраничного отображения
    all_fields = list(form_data.items())
    start_idx = (page - 1) * 10
    end_idx = start_idx + 10
    page_fields = all_fields[start_idx:end_idx]

    if not page_fields:
        await message.answer("✅ Все поля показаны")
        return

    builder = InlineKeyboardBuilder()

    for field_key, field_info in page_fields:
        emoji = "✅" if field_info.get("value") else "⬜"
        text = f"{emoji} {field_info['title'][:20]}"
        builder.button(
            text=text,
            callback_data=f"edit_{form_type}_{field_key}"
        )

    builder.adjust(2)

    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⏪ Назад",
                callback_data=f"more_fields_{form_type}_{page - 1}"
            )
        )

    nav_buttons.append(
        types.InlineKeyboardButton(
            text="🏠 К форме",
            callback_data=f"show_form_{form_type}"
        )
    )

    if end_idx < len(all_fields):
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="Далее ⏩",
                callback_data=f"more_fields_{form_type}_{page + 1}"
            )
        )

    builder.row(*nav_buttons)

    try:
        await message.edit_text(
            f"📋 <b>Дополнительные поля (страница {page})</b>\n\n"
            "Выберите поле для редактирования:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except:
        await message.answer(
            f"📋 <b>Дополнительные поля (страница {page})</b>\n\n"
            "Выберите поле для редактирования:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )


# ========== РЕДАКТИРОВАНИЕ СПЕЦИАЛЬНЫХ ПОЛЕЙ (Категория, Класс, Тип, Вид) ==========

@dp.callback_query(F.data.startswith("edit_product_"))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    """Редактирование поля товара"""
    field_key = callback.data.replace("edit_product_", "")
    data = await state.get_data()
    form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())

    if field_key not in form_data:
        await callback.answer("❌ Поле не найдено", show_alert=True)
        return

    field_info = form_data[field_key]

    # Сохраняем информацию о редактируемом поле
    await state.update_data(
        editing_field=field_key,
        editing_form_type="product",
        last_message_id=callback.message.message_id
    )

    # Особые обработчики для полей выбора
    if field_key == "category":
        await state.set_state(ProductCardForm.selecting_category)
        await show_category_selection(callback.message, "product", "product_purposes")
        return
    elif field_key == "item_class":
        await state.set_state(ProductCardForm.selecting_class)
        await show_class_selection(callback.message, "product", "product_classes")
        return
    elif field_key == "item_type":
        await state.set_state(ProductCardForm.selecting_type)
        await show_type_selection(callback.message, "product", "product_types")
        return
    elif field_key == "item_kind":
        await state.set_state(ProductCardForm.selecting_kind)
        await show_kind_selection(callback.message, "product", "product_views")
        return
    elif field_key == "images":
        await show_media_selection(callback.message, "product")
        return

    # Стандартный запрос значения
    current_value = field_info.get("value", "")
    await callback.message.edit_text(
        f"✏️ <b>Редактирование:</b> {field_info['title']}\n\n"
        f"Текущее значение: <i>{current_value if current_value else 'Не задано'}</i>\n\n"
        f"Введите новое значение или напишите 'пропустить':",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="◀️ Отмена",
                        callback_data="show_form_product"
                    )
                ]
            ]
        )
    )

    await state.set_state(ProductCardForm.waiting_for_value)
    await callback.answer()


@dp.callback_query(F.data.startswith("edit_service_"))
async def edit_service_field(callback: CallbackQuery, state: FSMContext):
    """Редактирование поля услуги"""
    field_key = callback.data.replace("edit_service_", "")
    data = await state.get_data()
    form_data = data.get("service_form", SERVICE_TEMPLATE.copy())

    if field_key not in form_data:
        await callback.answer("❌ Поле не найдено", show_alert=True)
        return

    field_info = form_data[field_key]

    # Сохраняем информацию о редактируемом поле
    await state.update_data(
        editing_field=field_key,
        editing_form_type="service",
        last_message_id=callback.message.message_id
    )

    # Особые обработчики для полей выбора
    if field_key == "category":
        await state.set_state(ServiceCardForm.selecting_category)
        await show_category_selection(callback.message, "service", "service_purposes")
        return
    elif field_key == "item_class":
        await state.set_state(ServiceCardForm.selecting_class)
        await show_class_selection(callback.message, "service", "service_classes")
        return
    elif field_key == "item_type":
        await state.set_state(ServiceCardForm.selecting_type)
        await show_type_selection(callback.message, "service", "service_types")
        return
    elif field_key == "item_kind":
        await state.set_state(ServiceCardForm.selecting_kind)
        await show_kind_selection(callback.message, "service", "service_views")
        return
    elif field_key == "images":
        await show_media_selection(callback.message, "service")
        return

    # Стандартный запрос значения
    current_value = field_info.get("value", "")
    await callback.message.edit_text(
        f"✏️ <b>Редактирование:</b> {field_info['title']}\n\n"
        f"Текущее значение: <i>{current_value if current_value else 'Не задано'}</i>\n\n"
        f"Введите новое значение или напишите 'пропустить':",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="◀️ Отмена",
                        callback_data="show_form_service"
                    )
                ]
            ]
        )
    )

    await state.set_state(ServiceCardForm.waiting_for_value)
    await callback.answer()


@dp.callback_query(F.data.startswith("edit_offer_"))
async def edit_offer_field(callback: CallbackQuery, state: FSMContext):
    """Редактирование поля предложения"""
    field_key = callback.data.replace("edit_offer_", "")
    data = await state.get_data()
    form_data = data.get("offer_form", OFFER_TEMPLATE.copy())

    if field_key not in form_data:
        await callback.answer("❌ Поле не найдено", show_alert=True)
        return

    field_info = form_data[field_key]

    # Сохраняем информацию о редактируемом поле
    await state.update_data(
        editing_field=field_key,
        editing_form_type="offer",
        last_message_id=callback.message.message_id
    )

    # Особые обработчики для полей выбора
    if field_key == "category":
        await state.set_state(OfferCardForm.selecting_category)
        await show_category_selection(callback.message, "offer", "product_purposes")
        return
    elif field_key == "item_class":
        await state.set_state(OfferCardForm.selecting_class)
        await show_class_selection(callback.message, "offer", "product_classes")
        return
    elif field_key == "item_type":
        await state.set_state(OfferCardForm.selecting_type)
        await show_type_selection(callback.message, "offer", "product_types")
        return
    elif field_key == "item_kind":
        await state.set_state(OfferCardForm.selecting_kind)
        await show_kind_selection(callback.message, "offer", "product_views")
        return
    elif field_key == "images":
        await show_media_selection(callback.message, "offer")
        return

    # Стандартный запрос значения
    current_value = field_info.get("value", "")
    await callback.message.edit_text(
        f"✏️ <b>Редактирование:</b> {field_info['title']}\n\n"
        f"Текущее значение: <i>{current_value if current_value else 'Не задано'}</i>\n\n"
        f"Введите новое значение или напишите 'пропустить':",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="◀️ Отмена",
                        callback_data="show_form_offer"
                    )
                ]
            ]
        )
    )

    await state.set_state(OfferCardForm.waiting_for_value)
    await callback.answer()


# ========== ОБРАБОТЧИКИ ВВОДА ЗНАЧЕНИЙ ==========

@dp.message(ProductCardForm.waiting_for_value)
async def process_product_field_value(message: Message, state: FSMContext):
    """Обработка введенного значения для товара"""
    data = await state.get_data()
    field_key = data.get("editing_field")
    form_type = data.get("editing_form_type")

    if form_type != "product":
        return

    form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())

    if field_key and field_key in form_data:
        field_info = form_data[field_key]
        user_input = message.text.strip()

        # Обработка "пропустить"
        if user_input.lower() == "пропустить":
            user_input = ""

        # Сохраняем значение
        form_data[field_key]["value"] = user_input
        await state.update_data(product_form=form_data)

        # Возвращаемся к форме
        last_message_id = data.get("last_message_id")
        await show_form(message, state, "product", last_message_id)
        await state.set_state(ProductCardForm.editing_form)


@dp.message(ServiceCardForm.waiting_for_value)
async def process_service_field_value(message: Message, state: FSMContext):
    """Обработка введенного значения для услуги"""
    data = await state.get_data()
    field_key = data.get("editing_field")
    form_type = data.get("editing_form_type")

    if form_type != "service":
        return

    form_data = data.get("service_form", SERVICE_TEMPLATE.copy())

    if field_key and field_key in form_data:
        field_info = form_data[field_key]
        user_input = message.text.strip()

        # Обработка "пропустить"
        if user_input.lower() == "пропустить":
            user_input = ""

        # Сохраняем значение
        form_data[field_key]["value"] = user_input
        await state.update_data(service_form=form_data)

        # Возвращаемся к форме
        last_message_id = data.get("last_message_id")
        await show_form(message, state, "service", last_message_id)
        await state.set_state(ServiceCardForm.editing_form)


@dp.message(OfferCardForm.waiting_for_value)
async def process_offer_field_value(message: Message, state: FSMContext):
    """Обработка введенного значения для предложения"""
    data = await state.get_data()
    field_key = data.get("editing_field")
    form_type = data.get("editing_form_type")

    if form_type != "offer":
        return

    form_data = data.get("offer_form", OFFER_TEMPLATE.copy())

    if field_key and field_key in form_data:
        field_info = form_data[field_key]
        user_input = message.text.strip()

        # Обработка "пропустить"
        if user_input.lower() == "пропустить":
            user_input = ""

        # Сохраняем значение
        form_data[field_key]["value"] = user_input
        await state.update_data(offer_form=form_data)

        # Возвращаемся к форме
        last_message_id = data.get("last_message_id")
        await show_form(message, state, "offer", last_message_id)
        await state.set_state(OfferCardForm.editing_form)


# ========== ОБРАБОТЧИКИ СПЕЦИАЛЬНЫХ ПОЛЕЙ ВЫБОРА ==========

async def show_category_selection(message: Message, form_type: str, table_name: str):
    """Показывает выбор категории из базы данных"""
    builder = InlineKeyboardBuilder()

    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(f"SELECT id, name FROM {table_name} ORDER BY name")
            items = await cursor.fetchall()

            for item in items:
                item_id = item[0]
                category_name = item[1]
                # Используем ID вместо имени для callback_data
                builder.add(types.InlineKeyboardButton(
                    text=category_name,
                    callback_data=f"select_{form_type}_cat_{item_id}"
                ))
    except Exception as e:
        print(f"❌ Ошибка при загрузке категорий: {e}")

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить новую",
        callback_data=f"add_{form_type}_category"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад к форме",
        callback_data=f"show_form_{form_type}"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📋 <b>Выберите категорию:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


async def show_class_selection(message: Message, form_type: str, table_name: str):
    """Показывает выбор класса из базы данных"""
    builder = InlineKeyboardBuilder()

    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(f"SELECT id, name FROM {table_name} ORDER BY name")
            items = await cursor.fetchall()

            for item in items:
                item_id = item[0]
                class_name = item[1]
                # Используем ID вместо имени для callback_data
                builder.add(types.InlineKeyboardButton(
                    text=class_name,
                    callback_data=f"select_{form_type}_cls_{item_id}"
                ))
    except Exception as e:
        print(f"❌ Ошибка при загрузке классов: {e}")

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить новый",
        callback_data=f"add_{form_type}_class"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад к форме",
        callback_data=f"show_form_{form_type}"
    ))
    builder.adjust(2)

    await message.edit_text(
        "🏷️ <b>Выберите класс:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


async def show_type_selection(message: Message, form_type: str, table_name: str):
    """Показывает выбор типа из базы данных"""
    builder = InlineKeyboardBuilder()

    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(f"SELECT id, name FROM {table_name} ORDER BY name")
            items = await cursor.fetchall()

            for item in items:
                item_id = item[0]
                type_name = item[1]
                # Используем ID вместо имени для callback_data
                builder.add(types.InlineKeyboardButton(
                    text=type_name,
                    callback_data=f"select_{form_type}_typ_{item_id}"
                ))
    except Exception as e:
        print(f"❌ Ошибка при загрузке типов: {e}")

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить новый",
        callback_data=f"add_{form_type}_type"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад к форме",
        callback_data=f"show_form_{form_type}"
    ))
    builder.adjust(2)

    await message.edit_text(
        "🔧 <b>Выберите тип:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


async def show_kind_selection(message: Message, form_type: str, table_name: str):
    """Показывает выбор вида из базы данных"""
    builder = InlineKeyboardBuilder()

    try:
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(f"SELECT id, name FROM {table_name} ORDER BY name")
            items = await cursor.fetchall()

            for item in items:
                item_id = item[0]
                kind_name = item[1]
                # Используем ID вместо имени для callback_data
                builder.add(types.InlineKeyboardButton(
                    text=kind_name,
                    callback_data=f"select_{form_type}_knd_{item_id}"
                ))
    except Exception as e:
        print(f"❌ Ошибка при загрузке видов: {e}")

    builder.add(types.InlineKeyboardButton(
        text="➕ Добавить новый",
        callback_data=f"add_{form_type}_kind"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад к форме",
        callback_data=f"show_form_{form_type}"
    ))
    builder.adjust(2)

    await message.edit_text(
        "📊 <b>Выберите вид:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


async def show_media_selection(message: Message, form_type: str):
    """Показывает интерфейс для добавления медиа"""
    builder = InlineKeyboardBuilder()

    builder.add(types.InlineKeyboardButton(
        text="📷 Добавить фото",
        callback_data=f"add_{form_type}_photo"
    ))
    builder.add(types.InlineKeyboardButton(
        text="🎥 Добавить видео",
        callback_data=f"add_{form_type}_video"
    ))
    builder.add(types.InlineKeyboardButton(
        text="🗑️ Очистить",
        callback_data=f"clear_{form_type}_media"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад к форме",
        callback_data=f"show_form_{form_type}"
    ))
    builder.adjust(2)

    await message.edit_text(
        "🖼️ <b>Добавление медиафайлов</b>\n\n"
        "Отправьте фото или видео, или используйте кнопки ниже:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# ========== ОБРАБОТЧИКИ ВЫБОРА ЗНАЧЕНИЙ ==========

@dp.callback_query(F.data.startswith("select_"))
async def select_field_value(callback: CallbackQuery, state: FSMContext):
    """Установка выбранного значения поля"""
    try:
        parts = callback.data.split("_")
        if len(parts) < 4:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        form_type = parts[1]  # product, service, offer
        field_type = parts[2]  # cat, cls, typ, knd
        item_id = int(parts[3])  # ID из базы данных

        # Определяем поле в форме по типу
        field_mapping = {
            "cat": ("category", "product_purposes", "service_purposes"),
            "cls": ("item_class", "product_classes", "service_classes"),
            "typ": ("item_type", "product_types", "service_types"),
            "knd": ("item_kind", "product_views", "service_views")
        }

        if field_type not in field_mapping:
            await callback.answer("❌ Неизвестный тип поля", show_alert=True)
            return

        field_key, product_table, service_table = field_mapping[field_type]

        # Определяем правильную таблицу по типу формы
        table_name = product_table if form_type in ["product", "offer"] else service_table

        # Получаем имя из базы данных по ID
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute(f"SELECT name FROM {table_name} WHERE id = ?", (item_id,))
            item = await cursor.fetchone()

            if not item:
                await callback.answer("❌ Элемент не найден", show_alert=True)
                return

            value = item[0]

        data = await state.get_data()
        last_message_id = data.get("last_message_id", callback.message.message_id)

        # Получаем текущую форму и обновляем значение
        if form_type == "product":
            form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())
            state_class = ProductCardForm
        elif form_type == "service":
            form_data = data.get("service_form", SERVICE_TEMPLATE.copy())
            state_class = ServiceCardForm
        else:  # offer
            form_data = data.get("offer_form", OFFER_TEMPLATE.copy())
            state_class = OfferCardForm

        if field_key in form_data:
            form_data[field_key]["value"] = value

            # Сохраняем обновленную форму
            await state.update_data(**{f"{form_type}_form": form_data})

            # Возвращаемся к форме
            await show_form(callback.message, state, form_type, last_message_id)
            await state.set_state(state_class.editing_form)

        await callback.answer(f"✅ Установлено: {value}")

    except Exception as e:
        print(f"❌ Ошибка при установке значения: {e}")
        await callback.answer("❌ Ошибка при сохранении", show_alert=True)


# ========== ОБРАБОТЧИКИ МЕДИА ==========

@dp.message(F.photo | F.video)
async def handle_media(message: Message, state: FSMContext):
    """Обработка загрузки медиафайлов"""
    data = await state.get_data()
    form_type = data.get("editing_form_type")
    field_key = data.get("editing_field")
    last_message_id = data.get("last_message_id", message.message_id)

    if not form_type or field_key != "images":
        return

    # Получаем текущую форму
    if form_type == "product":
        form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())
        state_class = ProductCardForm
    elif form_type == "service":
        form_data = data.get("service_form", SERVICE_TEMPLATE.copy())
        state_class = ServiceCardForm
    else:  # offer
        form_data = data.get("offer_form", OFFER_TEMPLATE.copy())
        state_class = OfferCardForm

    # Получаем текущие файлы
    current_files = form_data["images"].get("value", "")
    file_list = current_files.split(",") if current_files else []

    # Добавляем новый файл
    if message.photo:
        file_id = message.photo[-1].file_id
        file_list.append(f"photo:{file_id}")
    elif message.video:
        file_id = message.video.file_id
        file_list.append(f"video:{file_id}")

    # Ограничиваем количество файлов
    if len(file_list) > 10:
        file_list = file_list[-10:]

    form_data["images"]["value"] = ",".join(file_list)

    # Сохраняем обновленную форму
    await state.update_data(**{f"{form_type}_form": form_data})

    # Возвращаемся к форме
    await show_form(message, state, form_type, last_message_id)
    await state.set_state(state_class.editing_form)


# ========== ОБРАБОТЧИКИ ДОПОЛНИТЕЛЬНЫХ ДЕЙСТВИЙ ==========

@dp.callback_query(F.data.startswith("show_form_"))
async def show_form_handler(callback: CallbackQuery, state: FSMContext):
    """Показывает основную форму"""
    form_type = callback.data.replace("show_form_", "")

    if form_type == "product":
        await state.set_state(ProductCardForm.editing_form)
    elif form_type == "service":
        await state.set_state(ServiceCardForm.editing_form)
    else:  # offer
        await state.set_state(OfferCardForm.editing_form)

    await show_form(callback.message, state, form_type, callback.message.message_id)
    await callback.answer()


@dp.callback_query(F.data.startswith("more_fields_"))
async def more_fields_handler(callback: CallbackQuery, state: FSMContext):
    """Показывает дополнительные поля"""
    try:
        parts = callback.data.split("_")
        form_type = parts[2]
        page = int(parts[3])

        await show_more_fields(callback.message, state, form_type, page)
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка в more_fields: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@dp.callback_query(F.data.startswith("preview_"))
async def preview_form(callback: CallbackQuery, state: FSMContext):
    """Предпросмотр заполненной формы"""
    form_type = callback.data.replace("preview_", "")
    data = await state.get_data()

    if form_type == "product":
        form_data = data.get("product_form", {})
        item_type = "product"
        operation = data.get("operation", "")
        operation_text = "💰 Продать" if operation == "sell" else "🛒 Купить"
    elif form_type == "service":
        form_data = data.get("service_form", {})
        item_type = "service"
        operation = data.get("operation", "")
        operation_text = "🛠️ Предложить услугу" if operation == "sell" else "🔧 Заказать услугу"
    else:  # offer
        form_data = data.get("offer_form", {})
        item_type = "offer"
        operation = data.get("operation", "")
        operation_text = "💰 Продать" if operation == "sell" else "🛒 Купить"

    # Формируем предпросмотр
    preview_text = f"🛒 <b>ПРЕДПРОСМОТР КАРТОЧКИ ({operation_text})</b>\n"
    preview_text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    has_data = False
    for field_key, field_info in form_data.items():
        value = field_info.get("value")
        if value:
            has_data = True
            if field_key == "images" and value:
                file_count = len(value.split(','))
                preview_text += f"<b>{field_info['title']}:</b>\n"
                preview_text += f"[{file_count} файлов]\n\n"
            else:
                preview_text += f"<b>{field_info['title']}:</b>\n"
                preview_text += f"{value}\n\n"

    if not has_data:
        preview_text += "⚠️ <i>Карточка пока пуста. Заполните хотя бы одно поле.</i>\n\n"

    preview_text += "━━━━━━━━━━━━━━━━━━━━\n"
    preview_text += "ℹ️ Это предварительный просмотр. Карточка еще не опубликована."

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✏️ Редактировать",
        callback_data=f"show_form_{form_type}"
    ))
    builder.add(types.InlineKeyboardButton(
        text="💾 Сохранить",
        callback_data=f"save_{form_type}"
    ))

    await callback.message.edit_text(
        preview_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("save_"))
async def save_form(callback: CallbackQuery, state: FSMContext):
    """Сохранение формы в базу данных"""
    form_type = callback.data.replace("save_", "")
    data = await state.get_data()
    operation = data.get("operation", "")

    if form_type == "product":
        form_data = data.get("product_form", {})
        item_type = "product"
    elif form_type == "service":
        form_data = data.get("service_form", {})
        item_type = "service"
    else:  # offer
        form_data = data.get("offer_form", {})
        item_type = "offer"

    # Проверяем, есть ли хоть какие-то данные
    has_data = False
    for field_key, field_info in form_data.items():
        if field_info.get("value"):
            has_data = True
            break

    if not has_data:
        await callback.answer("❌ Карточка пуста. Заполните хотя бы одно поле.", show_alert=True)
        return

    # Подготавливаем данные для сохранения
    save_data = {"operation": operation}
    for field_key, field_info in form_data.items():
        value = field_info.get("value", "")
        # Заменяем пустые значения на "не заполнено"
        if not value:
            value = "не заполнено"
        save_data[field_key] = value

    # Сохраняем в базу данных
    try:
        if item_type == "service":
            # Сохранение услуги
            async with aiosqlite.connect("bot_database.db") as db:
                cursor = await db.execute("""
                    INSERT INTO service_orders 
                    (user_id, operation, category, item_class, item_type, item_kind,
                     catalog_id, service_date, title, works, materials, images, price, pricing,
                     guarantees, conditions, supplier_info, reviews, rating, statistics, 
                     additional_info, deadline, tags, contact, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    callback.from_user.id,
                    save_data.get('operation', 'не заполнено'),
                    save_data.get('category', 'не заполнено'),
                    save_data.get('item_class', 'не заполнено'),
                    save_data.get('item_type', 'не заполнено'),
                    save_data.get('item_kind', 'не заполнено'),
                    save_data.get('catalog_id', 'не заполнено'),
                    save_data.get('service_date', 'не заполнено'),
                    save_data.get('title', 'не заполнено'),
                    save_data.get('works', 'не заполнено'),
                    save_data.get('materials', 'не заполнено'),
                    save_data.get('images', 'не заполнено'),
                    save_data.get('price', 'не заполнено'),
                    save_data.get('pricing', 'не заполнено'),
                    save_data.get('guarantees', 'не заполнено'),
                    save_data.get('conditions', 'не заполнено'),
                    save_data.get('supplier_info', 'не заполнено'),
                    save_data.get('reviews', 'не заполнено'),
                    save_data.get('rating', 'не заполнено'),
                    save_data.get('statistics', 'не заполнено'),
                    save_data.get('additional_info', 'не заполнено'),
                    save_data.get('deadline', 'не заполнено'),
                    save_data.get('tags', 'не заполнено'),
                    save_data.get('contact', 'не заполнено'),
                    'active',
                    datetime.now().isoformat()
                ))

                new_request_id = cursor.lastrowid
                await db.commit()

                # Добавляем в корзину ТОЛЬКО если операция "заказать услугу" (operation = "buy")
                if operation == "buy":  # заказать услугу
                    await db.execute("""
                        INSERT OR IGNORE INTO cart_order 
                        (user_id, item_type, item_id, quantity, price, added_at, source_table)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        callback.from_user.id,
                        'услуга',
                        new_request_id,
                        1,
                        save_data.get('price', '0'),
                        datetime.now().isoformat(),
                        'service_orders'
                    ))
                    await db.commit()

        else:
            # Сохранение товара или предложения
            table_name = "order_requests"
            async with aiosqlite.connect("bot_database.db") as db:
                cursor = await db.execute("""
                    INSERT INTO order_requests 
                    (user_id, operation, item_type, category, item_class, item_type_detail, item_kind,
                     title, purpose, name, creation_date, condition, specifications, 
                     advantages, additional_info, images, price, availability, detailed_specs, 
                     reviews, rating, delivery_info, supplier_info, statistics, deadline, tags, 
                     contact, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    callback.from_user.id,
                    save_data.get('operation', 'не заполнено'),
                    item_type,
                    save_data.get('category', 'не заполнено'),
                    save_data.get('item_class', 'не заполнено'),
                    save_data.get('item_type', 'не заполнено'),
                    save_data.get('item_kind', 'не заполнено'),
                    save_data.get('title', 'не заполнено'),
                    save_data.get('purpose', 'не заполнено'),
                    save_data.get('name', 'не заполнено'),
                    save_data.get('creation_date', 'не заполнено'),
                    save_data.get('condition', 'не заполнено'),
                    save_data.get('specifications', 'не заполнено'),
                    save_data.get('advantages', 'не заполнено'),
                    save_data.get('additional_info', 'не заполнено'),
                    save_data.get('images', 'не заполнено'),
                    save_data.get('price', 'не заполнено'),
                    save_data.get('availability', 'не заполнено'),
                    save_data.get('detailed_specs', 'не заполнено'),
                    save_data.get('reviews', 'не заполнено'),
                    save_data.get('rating', 'не заполнено'),
                    save_data.get('delivery_info', 'не заполнено'),
                    save_data.get('supplier_info', 'не заполнено'),
                    save_data.get('statistics', 'не заполнено'),
                    save_data.get('deadline', 'не заполнено'),
                    save_data.get('tags', 'не заполнено'),
                    save_data.get('contact', 'не заполнено'),
                    'active',
                    datetime.now().isoformat()
                ))

                new_request_id = cursor.lastrowid
                await db.commit()

                # Добавляем в корзину ТОЛЬКО если операция "купить" (operation = "buy")
                if operation == "buy":  # купить товар/предложение
                    cart_item_type = 'товар' if item_type == 'product' else 'предложение'
                    await db.execute("""
                        INSERT OR IGNORE INTO cart_order 
                        (user_id, item_type, item_id, quantity, price, added_at, source_table)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        callback.from_user.id,
                        cart_item_type,
                        new_request_id,
                        1,
                        save_data.get('price', '0'),
                        datetime.now().isoformat(),
                        table_name
                    ))
                    await db.commit()

        # Синхронизация с Google Sheets
        try:
            from google_sheets import sync_order_requests_to_sheets
            result = await sync_order_requests_to_sheets()
            if result:
                print(f"✅ Заявка {new_request_id} синхронизирована с Google Sheets")
            else:
                print(f"⚠️ Заявка {new_request_id} сохранена, но произошла ошибка синхронизации с Google Sheets")
        except Exception as e:
            print(f"❌ Ошибка импорта модуля Google Sheets: {e}")

        # Уведомление админу
        await send_order_request_to_admin(callback.message.chat.id, new_request_id, save_data)

        # Уведомление пользователю
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🏠 В личный кабинет", callback_data="personal_account"))
        builder.add(types.InlineKeyboardButton(text="🛒 К корзине", callback_data="cart_order"))
        builder.adjust(1)

        # Формируем сообщение в зависимости от операции
        if operation == "sell":  # продать/предложить
            message_text = (
                f"✅ **Заявка №{new_request_id} успешно создана!**\n\n"
                f"Ваше предложение сохранено и будет доступно другим пользователям."
            )
        else:  # купить/заказать
            message_text = (
                f"✅ **Заявка №{new_request_id} успешно создана!**\n\n"
                f"Ваш заказ сохранен и добавлен в корзину."
            )

        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup()
        )

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        print(f"❌ Ошибка при сохранении заявки: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Произошла ошибка при сохранении. Попробуйте еще раз.", show_alert=True)


# ========== ОБРАБОТЧИКИ ДОБАВЛЕНИЯ КАТЕГОРИЙ ==========

@dp.callback_query(F.data.startswith("add_"))
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления новой категории/класса/типа/вида"""
    try:
        parts = callback.data.split("_")
        if len(parts) < 3:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        form_type = parts[1]  # product, service, offer
        field_type = parts[2]  # category, class, type, kind, photo, video

        # Определяем поле в форме по типу
        field_mapping = {
            "category": "category",
            "class": "item_class",
            "type": "item_type",
            "kind": "item_kind"
        }

        if field_type in field_mapping:
            field_key = field_mapping[field_type]

            # Определяем тип для уведомления админу
            type_names = {
                "category": "категорию",
                "class": "класс",
                "type": "тип",
                "kind": "вид"
            }

            await state.update_data(
                adding_for=form_type,
                adding_field=field_key,
                adding_field_type=field_type,
                adding_type_name=type_names[field_type],
                last_message_id=callback.message.message_id
            )

            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="◀️ Отмена",
                callback_data=f"show_form_{form_type}"
            ))

            await callback.message.edit_text(
                f"➕ <b>Добавление нового {type_names[field_type]}</b>\n\n"
                f"Введите название нового {type_names[field_type]}:",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        elif field_type in ["photo", "video"]:
            # Для медиа просто возвращаемся к форме - пользователь отправит файл
            await show_form(callback.message, state, form_type, callback.message.message_id)
            if form_type == "product":
                await state.set_state(ProductCardForm.editing_form)
            elif form_type == "service":
                await state.set_state(ServiceCardForm.editing_form)
            else:
                await state.set_state(OfferCardForm.editing_form)

        await callback.answer()

    except Exception as e:
        print(f"❌ Ошибка в add_category: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@dp.callback_query(F.data.startswith("clear_"))
async def clear_media(callback: CallbackQuery, state: FSMContext):
    """Очистка медиафайлов"""
    try:
        parts = callback.data.split("_")
        form_type = parts[1]  # product, service, offer

        data = await state.get_data()
        last_message_id = data.get("last_message_id", callback.message.message_id)

        if form_type == "product":
            form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())
            state_class = ProductCardForm
        elif form_type == "service":
            form_data = data.get("service_form", SERVICE_TEMPLATE.copy())
            state_class = ServiceCardForm
        else:  # offer
            form_data = data.get("offer_form", OFFER_TEMPLATE.copy())
            state_class = OfferCardForm

        form_data["images"]["value"] = ""
        await state.update_data(**{f"{form_type}_form": form_data})

        # Возвращаемся к форме
        await show_form(callback.message, state, form_type, last_message_id)
        await state.set_state(state_class.editing_form)

        await callback.answer("✅ Медиафайлы очищены")

    except Exception as e:
        print(f"❌ Ошибка при очистке медиа: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@dp.message()
async def handle_category_input(message: Message, state: FSMContext):
    """Обработка ввода новой категории/класса/типа/вида"""
    data = await state.get_data()
    form_type = data.get("adding_for")
    field_key = data.get("adding_field")
    field_type = data.get("adding_field_type")
    type_name = data.get("adding_type_name")
    last_message_id = data.get("last_message_id", message.message_id)

    if not form_type or not field_key:
        return

    value = message.text.strip()
    if not value:
        await message.answer(f"❌ Название {type_name} не может быть пустым. Введите название:")
        return

    # Определяем тип категории для уведомления админу
    category_type_mapping = {
        "product": {
            "category": "товара",
            "class": "класса товара",
            "type": "типа товара",
            "kind": "вида товара"
        },
        "service": {
            "category": "услуги",
            "class": "класса услуги",
            "type": "типа услуги",
            "kind": "вида услуги"
        },
        "offer": {
            "category": "предложения",
            "class": "класса предложения",
            "type": "типа предложения",
            "kind": "вида предложения"
        }
    }

    category_type = category_type_mapping.get(form_type, {}).get(field_type, "")

    # Уведомляем админа
    user_id = message.from_user.id
    username = message.from_user.username
    await notify_admin_new_category(category_type, value, user_id, username, form_type)

    # Устанавливаем значение в форме
    if form_type == "product":
        form_data = data.get("product_form", PRODUCT_TEMPLATE.copy())
        state_class = ProductCardForm
    elif form_type == "service":
        form_data = data.get("service_form", SERVICE_TEMPLATE.copy())
        state_class = ServiceCardForm
    else:  # offer
        form_data = data.get("offer_form", OFFER_TEMPLATE.copy())
        state_class = OfferCardForm

    form_data[field_key]["value"] = value
    await state.update_data(**{f"{form_type}_form": form_data})

    # Уведомляем пользователя
    await message.answer(
        f"✅ **{type_name.capitalize()} '{value}' отправлен на рассмотрение администратору.**\n\n"
        "Администратор проверит и добавит его в систему."
    )

    # Возвращаемся к форме
    await show_form(message, state, form_type, last_message_id)
    await state.set_state(state_class.editing_form)