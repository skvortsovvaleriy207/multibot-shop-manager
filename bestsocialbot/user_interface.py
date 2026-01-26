from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dispatcher import dp
import aiosqlite
from db import DB_FILE
from referral_system import generate_referral_link, get_referral_stats
from activity_system import save_user_activity_report, calculate_activity_score, ACTIVITY_TYPES

@dp.callback_query(F.data == "referral_program")
async def referral_program(callback: CallbackQuery):
    """Реферальная программа"""
    user_id = callback.from_user.id
    
    # Генерируем реферальную ссылку
    referral_link = await generate_referral_link(user_id)
    
    # Получаем статистику
    stats = await get_referral_stats(user_id)
    total_referrals = stats[0] if stats else 0
    earnings = stats[1] if stats else 0
    
    text = f"""
🔗 **Реферальная программа**

Ваша реферальная ссылка:
`{referral_link}`

📊 **Ваша статистика:**
• Приглашено рефералов: {total_referrals}
• Заработано монет: {earnings:.3f}

💰 **Как это работает:**
• За каждого активного реферала: 0.1 монеты/месяц
• Реферал должен пройти опрос и проявлять активность
• Бонусы начисляются автоматически

Поделитесь ссылкой с друзьями и получайте пассивный доход!
    """
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_personal_account"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "my_activity")
async def my_activity(callback: CallbackQuery):
    """Мой учет активности"""
    user_id = callback.from_user.id
    
    # Получаем текущую активность
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            SELECT daily_activity_points, monthly_activity_points, current_activity
            FROM users WHERE user_id = ?
        """, (user_id,))
        activity_data = await cursor.fetchone()
    
    daily_points = activity_data[0] if activity_data else 0
    monthly_points = activity_data[1] if activity_data else 0
    current_activity = activity_data[2] if activity_data else ""
    
    text = f"""
📊 **Мой учет активности**

📈 **Текущие показатели:**
• Дневная активность: {daily_points:.3f} монет
• Месячная активность: {monthly_points:.3f} монет

🎯 **Виды активности:**
{chr(10).join([f"• {name}" for name in ACTIVITY_TYPES.values()])}

📋 **Ваша активность:**
{current_activity or "Активность не зафиксирована"}

💡 **Максимум:**
• До 0.06 монеты в день
• До 1.0 монеты в месяц от админа
    """
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📝 Отчет о моей активности", callback_data="activity_report"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_personal_account"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "activity_report")
async def activity_report_menu(callback: CallbackQuery):
    """Меню отчета активности"""
    text = """
📝 **Отчет о моей активности**

Отметьте свою активность за сегодня:
• "+" - участвовал
• "-" - не участвовал

Бот сверит с реальными данными.
    """
    
    builder = InlineKeyboardBuilder()
    for key, name in ACTIVITY_TYPES.items():
        builder.add(types.InlineKeyboardButton(text=f"📋 {name}", callback_data=f"report_{key}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="my_activity"))
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Обработчики для отчетов активности
@dp.callback_query(F.data.startswith("report_"))
async def activity_report_handler(callback: CallbackQuery):
    """Обработка отчета активности"""
    activity_type = callback.data.replace("report_", "")
    activity_name = ACTIVITY_TYPES.get(activity_type, "Неизвестная активность")
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✅ Участвовал (+)", callback_data=f"set_{activity_type}_plus"))
    builder.add(types.InlineKeyboardButton(text="❌ Не участвовал (-)", callback_data=f"set_{activity_type}_minus"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="activity_report"))
    builder.adjust(2, 1)
    
    await callback.message.edit_text(
        f"📋 **{activity_name}**\n\nВы участвовали в этом виде активности сегодня?",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("set_"))
async def set_activity_handler(callback: CallbackQuery):
    """Установка активности"""
    user_id = callback.from_user.id
    data_parts = callback.data.replace("set_", "").split("_")
    activity_type = "_".join(data_parts[:-1])
    value = data_parts[-1]  # plus или minus
    
    # Сохраняем отчет (упрощенная версия)
    report_data = {f"{activity_type}_{value}": 1}
    await save_user_activity_report(user_id, report_data)
    
    # Пересчитываем активность
    await calculate_activity_score(user_id)
    
    await callback.message.edit_text(
        f"✅ Отчет сохранен!\n\nВаша активность будет пересчитана автоматически.",
        reply_markup=InlineKeyboardBuilder().add(
            types.InlineKeyboardButton(text="◀️ К активности", callback_data="my_activity")
        ).as_markup()
    )
    await callback.answer()