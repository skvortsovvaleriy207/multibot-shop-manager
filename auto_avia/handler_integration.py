# handlers/integration_handlers.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from integration import (
    integrate_user_to_wond_sheets_only,
    integrate_user_to_besthome_sheets_only,
)
from dispatcher import dp

router = Router()


@dp.callback_query(F.data == "handle_wond_integration")
async def handle_wond_integration_callback(callback: CallbackQuery):
    """Обработчик коллбэка для интеграции только Google Sheets с ботом Wond"""
    print("Начало интеграции Google Sheets с Wond")


    # Выполняем интеграцию только в Google Sheets
    result = await integrate_user_to_wond_sheets_only(callback.from_user.id)


    if result["success"]:
        # Создаем клавиатуру с ссылкой
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="✅ Перейти в бот Wond",
                    url="https://t.me/OurWonderfulBot?start_shop"
                )]
            ]
        )

        await callback.message.answer(
            f"Теперь вы можете перейти в бота Wond.",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            f"❌ Ошибка интеграции в Google Sheets:\n{result['message']}\n\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
    await callback.answer()


@dp.callback_query(F.data == "handle_besthome_integration")
async def handle_besthome_integration(callback: CallbackQuery):
    """Обработчик коллбэка для интеграции только Google Sheets с ботом besthome"""
    print("Начало интеграции Google Sheets с besthome")


    # Выполняем интеграцию только в Google Sheets
    result = await integrate_user_to_besthome_sheets_only(callback.from_user.id)

    if result["success"]:
        # Создаем клавиатуру с ссылкой
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="✅ Перейти в бот besthome",
                    url="https://t.me/Better_House_Bot?start_shop"
                )]
            ]
        )

        await callback.message.answer(
            f"Теперь вы можете перейти в бота besthome.",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
    await callback.answer()