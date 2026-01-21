import random
from aiogram import types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class CaptchaStates(StatesGroup):
    waiting_for_captcha = State()

COLORED_EMOJIS = [
    "🔴", 
    "🟠", 
    "🟡", 
    "🟢", 
    "🔵", 
    "🟣", 
    "🟤", 
    "⚫", 
    "⚪", 
]

async def send_captcha(message: types.Message, state: FSMContext):
    target_emoji = random.choice(COLORED_EMOJIS)
    options = COLORED_EMOJIS.copy()
    random.shuffle(options)

    data = await state.get_data()
    if "captcha_attempt_count" not in data:
        await state.update_data(captcha_attempt_count=0)
    
    await state.update_data(target_emoji=target_emoji)

    builder = InlineKeyboardBuilder()
    for emoji in options:
        builder.add(types.InlineKeyboardButton(text=emoji, callback_data=f"captcha_{emoji}"))
    builder.adjust(3)

    print(f"DEBUG: Sending captcha with target: {target_emoji}") 
    print(f"DEBUG: Callback data patterns: {[f'captcha_{emoji}' for emoji in options]}")

    await message.answer(
        f"Выберите эмодзи цвета: {target_emoji}",
        reply_markup=builder.as_markup()
    )

    await state.set_state(CaptchaStates.waiting_for_captcha)

async def process_captcha_selection(callback: types.CallbackQuery, state: FSMContext) -> bool:
    print(f"DEBUG: process_captcha_selection called with callback.data={callback.data}")

    selected_emoji = callback.data.removeprefix("captcha_")

    data = await state.get_data()
    target_emoji = data.get("target_emoji")
    print(f"DEBUG: target_emoji={target_emoji}, selected_emoji={selected_emoji}")

    if selected_emoji == target_emoji:
        await callback.message.answer("✅ Вы выбрали правильный цвет!")
        success = True
    else:
        await callback.message.answer(f"❌ Неправильно. Правильный цвет был: {target_emoji}")
        success = False

    await callback.answer()

    return success
