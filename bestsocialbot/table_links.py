
from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dispatcher import dp
import logging
from integration import integrate_user_to_besthome_sheets_only, integrate_user_to_autoavia_sheets_only
from google_sheets import sync_db_to_main_survey_sheet
from utils import check_blocked_user

router = Router()

@dp.callback_query(F.data == "links_menu")
async def show_links_menu(callback: CallbackQuery):
    """Меню перехода к другим ботам с сохранением данных"""
    if await check_blocked_user(callback):
        return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="🏠 BestHome (Недвижимость)",
        callback_data="process_integration_besthome"
    ))
    builder.add(types.InlineKeyboardButton(
        text="🚗 AutoAvia (Авто)",
        callback_data="process_integration_autoavia"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="personal_account"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "🤖 **Наши боты**\n\n"
        "Выберите бота для перехода.\n"
        "⚠️ **Внимание:** При переходе ваши данные (профиль, баланс, бонусы) будут автоматически сохранены и синхронизированы.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "process_integration_besthome")
async def process_integration_besthome(callback: CallbackQuery):
    """Обработка перехода в BestHome"""
    await callback.message.edit_text("⏳ Сохранение данных и синхронизация... Пожалуйста, подождите.")
    
    user_id = callback.from_user.id
    
    # 1. Синхронизация локальной БД с Google Sheet (Сохраняем данные текущего бота)
    sync_success = await sync_db_to_main_survey_sheet()
    
    if not sync_success:
        await callback.message.edit_text(
            "❌ Ошибка сохранения данных. Попробуйте позже.",
            reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="links_menu")).as_markup()
        )
        return

    # 2. Интеграция (Копирование) в таблицу целевого бота
    result = await integrate_user_to_besthome_sheets_only(user_id)
    
    if result.get("success"):
        keyboard = InlineKeyboardBuilder()
        keyboard.add(types.InlineKeyboardButton(
            text="✅ Перейти в BestHome",
            url="https://t.me/Better_House_Bot?start=transfer"
        ))
        keyboard.add(types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="links_menu"
        ))
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            "✅ **Данные успешно сохранены и переданы!**\n\n"
            "Теперь вы можете перейти в BestHomeBot.",
            reply_markup=keyboard.as_markup()
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка передачи данных: {result.get('message')}\n"
            "Но локальные данные успешно сохранены.",
            reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="links_menu")).as_markup()
        )


@dp.callback_query(F.data == "process_integration_autoavia")
async def process_integration_autoavia(callback: CallbackQuery):
    """Обработка перехода в AutoAvia"""
    await callback.message.edit_text("⏳ Сохранение данных и синхронизация... Пожалуйста, подождите.")
    
    user_id = callback.from_user.id
    
    # 1. Синхронизация
    sync_success = await sync_db_to_main_survey_sheet()
    
    if not sync_success:
        await callback.message.edit_text(
            "❌ Ошибка сохранения данных. Попробуйте позже.",
            reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="links_menu")).as_markup()
        )
        return

    # 2. Интеграция
    result = await integrate_user_to_autoavia_sheets_only(user_id)
    
    if result.get("success"):
        keyboard = InlineKeyboardBuilder()
        keyboard.add(types.InlineKeyboardButton(
            text="🚗 Перейти в AutoAvia",
            url="https://t.me/BestAutoAviaBot?start=transfer"
        ))
        keyboard.add(types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="links_menu"
        ))
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            "✅ **Данные успешно сохранены и переданы!**\n\n"
            "Теперь вы можете перейти в AutoAviaBot.",
            reply_markup=keyboard.as_markup()
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка передачи данных: {result.get('message')}\n"
            "Но локальные данные успешно сохранены.",
            reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="links_menu")).as_markup()
        )
