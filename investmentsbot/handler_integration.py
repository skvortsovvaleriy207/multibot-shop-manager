# handlers/integration_handlers.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from integration import (
    integrate_user_to_besthome_sheets_only,
    integrate_user_to_autoavia_sheets_only,
)
from dispatcher import dp

router = Router()


@dp.callback_query(F.data == "handle_besthome_integration")
async def handle_besthome_integration_callback(callback: CallbackQuery):
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
            f"Теперь вы можете перейти в бота Besthome и продолжить работу там.",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
    await callback.answer()


@dp.callback_query(F.data == "handle_autoavia_integration")
async def handle_autoavia_integration_callback(callback: CallbackQuery):
    """Обработчик коллбэка для интеграции только Google Sheets с ботом Autoavia"""
    print("Начало интеграции Google Sheets с Autoavia")

    # Отправляем сообщение о начале интеграции

    # Выполняем интеграцию только в Google Sheets
    result = await integrate_user_to_autoavia_sheets_only(callback.from_user.id)

    if result["success"]:
        # Создаем клавиатуру с ссылкой
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚗 Перейти в бот Autoavia",
                    url="https://t.me/BestAutoAviaBot?start_shop"
                )]
            ]
        )

        if callback.message.caption is not None:
            await callback.message.edit_caption(
                caption=f"Теперь вы можете перейти в бота Auto и продолжить работу там.",
                reply_markup=keyboard
            )

        else:
            await callback.message.edit_text(
                text=f"Теперь вы можете перейти в бота Auto и продолжить работу там.",
                reply_markup=keyboard
            )
    else:
        await callback.message.answer(
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
    await callback.answer()