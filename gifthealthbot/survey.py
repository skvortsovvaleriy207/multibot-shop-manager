from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
import asyncio
from integration import *
from datetime import datetime
from db import check_channel_subscription
from config import CHANNEL_ID, ADMIN_ID, CHANNEL_URL
from dispatcher import dp
from bot_instance import bot
from notifications import send_user_notification
from filters import is_valid_email, is_valid_phone
from utils import check_blocked_user
from handler_integration import handle_besthome_integration_callback, handle_autoavia_integration_callback
from initiatives_system import is_valid_proposal
import sys
import os
 
# Add shared_storage to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared_storage.global_db import (
    get_user_subscription_count, 
    is_user_subscribed, 
    register_user_subscription, 
    get_global_user_survey, 
    save_global_user,
    get_legal_document
)
from aiogram.types import BufferedInputFile

BOT_FOLDER_NAME = os.path.basename(os.path.dirname(__file__))

class SurveyStates(StatesGroup):
    START = State()
    Q3 = State()
    Q4 = State()
    Q6 = State()
    Q7 = State()
    Q9 = State()
    Q10 = State()
    Q11 = State()
    Q12 = State()
    Q13 = State()
    Q14 = State()
    Q15 = State()
    Q16 = State()
    FINISH = State()

SHOWCASE_TEXT = """
ДОБРО ПОЖАЛОВАТЬ В ЧАТ-БОТ СООБЩЕСТВА!
"""

SURVEY_GREETING = """
Добро пожаловать в чат-бот Telegram сообщества для совместного решения наиболее важных проблем каждого участника!

Достоверные ответы на все вопросы чат-бота дают вам право на:
1. Создание и использование вашего Личного кабинета- личного профиля в сообществе,
2. Доступ в магазин сообщества для продажи вами своих цифровых товаров и услуг или покупки цифровых активов у других подписчиков,
3. Сотрудничество с другими подписчиками и привлечение в проект рефералов для целевого роста ваших доходов и решения заявленных при опросе ваших проблем, 
4. Ежемесячное и бесплатное получение вами за вашу активность в сообществе цифровых монет, номинальная стоимость которых обеспечена собственными реальными активами и капиталами всех подписчиков сообщества, 
5. Учет и постепенное накопление ваших цифровых капиталов в личном кабинете, а также их обмен и продажу с помощью партнеров и инвесторов сообщества для получения вами безусловных базовых доходов, 
6. Бесплатное открытие вами своего бизнеса в виде ИП или ООО с регистрацией и РКО в банке-партнере сообщества,  
7. Совместные инвестиции с другими подписчиками, партнерами и инвесторами сообщества в общие проекты для роста ваших доходов и целевого решения личных и общих проблем, 
8. Участие в создании общей децентрализованной экосистемы учета, управления и роста активов и капиталов у каждого подписчика сообщества,
9. Благотворительную поддержку остронуждающихся, малоимущих подписчиков для их выхода из кризиса, 
10. Инициация и участие в реализации актуальных экологических программ сообщества в вашем регионе. 

Примечания: 
* Номинальная стоимость 1,0 монеты = 1,0 Ethereum.
* Подписчик проходит опрос в чат-боте только 1 раз и несет полную и самостоятельную ответственность в сообществе за достоверность своих ответов в опросе.
"""

SURVEY_QUESTIONS = {
    3: "1. Телеграм @username подписчика",
    4: "2. ФИО и возраст подписчика",
    6: "3. Место жительства: область, район, город, поселок",
    7: "4. Действующая эл. почта подписчика",
    9: "5. Текущая занятость подписчика (учеба, свой бизнес, работа по найму, ИП, ООО, самозанятый, пенсионер, иное - пояснить)",
    10: "6. Cамая важная финансовая проблема (долги, текущие расходы, убытки бизнеса, нужны инвесторы или долевые партнеры, иное - пояснить)",
    11: "7. Самая важная социальная проблема (улучшение семьи, здоровья, жилья, образования, иное - пояснить)",
    12: "8. Самая важная экологическая проблема в вашем регионе (загрязнения, пожары, наводнения, качество воды, загазованность, иное - пояснить)",
    13: "9. Вы будете пассивным подписчиком в нашем ТГ сообществе для выполнения в контенте просмотров, реакций, комментариев, опросов? - Вы получаете по 1,0 бонусу-монете в месяц",
    14: "10. Вы будете активным партнером - предпринимателем для развития и роста ТГ сообщества? - Вы получаете по 2,0 бонуса-монеты в месяц",
    15: "11. Вы будете инвестором или биржевым трейдером по продажам цифровым активов в сообществе? - Вы получаете по 3,0 бонуса-монеты в месяц",
    16: "12. У вас есть свое бизнес-предложение сотрудничества в сообществе? - Оцените здесь его полезность для вас в бонусах-монетах в месяц"
}

SURVEY_FINISH = """
Уважаемый подписчик! 
В опросе вы заявили свою самую важную проблему - она может быть не только личной, но и общей также и для других подписчиков, партнеров и инвесторов. С целью взаимодействия с ними вы можете выбрать здесь в меню ТОЛЬКО ОДНУ КНОПКУ Телеграм сообщества, которое наиболее соответствует вашей проблеме, и перейти в его чат-бот, где будет создан ваш личный профиль с учётом ваших данных, активности и баланса бонусов. 
ЖЕЛАЕМ ВАМ УСПЕШНОГО РЕШЕНИЯ ВАШИХ ПРОБЛЕМ В КЛУБЕ ПО ОБЩИМ ИНТЕРЕСАМ!
"""

from datetime import datetime


from db import check_account_status

async def save_user_data_to_db(user_id: int, data: dict):
    """
    Saves user data to the local bot database.
    Used by main.py when importing from Global DB.
    """
    async with aiosqlite.connect("bot_database.db") as db:
        # 1. Update/Insert into users table
        # We need to map the flat data dictionary to table columns
        # Default values for missing fields
        
        await db.execute(
            """
            INSERT OR REPLACE INTO users (
                user_id, username, first_name, last_name, has_completed_survey, created_at,
                survey_date, full_name, birth_date, location, email, phone, employment,
                financial_problem, social_problem, ecological_problem, passive_subscriber,
                active_partner, investor_trader, business_proposal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data.get("username", ""),
                data.get("first_name", ""),
                data.get("last_name", ""),
                1, # has_completed_survey
                datetime.now().isoformat(),
                datetime.now().strftime("%Y-%m-%d"),
                data.get("full_name", data.get("q4", "")), # Fallback to q4 if full_name not explicit
                data.get("birth_date", ""),
                data.get("location", data.get("q6", "")),
                data.get("email", data.get("q7", "")),
                data.get("phone", ""),
                data.get("employment", data.get("q9", "")),
                data.get("financial_problem", data.get("q10", "")),
                data.get("social_problem", data.get("q11", "")),
                data.get("ecological_problem", data.get("q12", "")),
                data.get("passive_subscriber", data.get("q13", "")),
                data.get("active_partner", data.get("q14", "")),
                data.get("investor_trader", data.get("q15", "")),
                data.get("business_proposal", data.get("q16", ""))
            )
        )
        
        # 2. Save Survey Answers (Optional, but good for consistency)
        # We assume data keys might be like "q3", "q4" etc if coming from survey state
        # Or keys like "financial_problem" if coming from structured dict.
        # For now, let's just save valid q-keys if present.
        for q_num in [3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]:
            key = f"q{q_num}"
            if key in data:
                 await db.execute(
                    "INSERT INTO survey_answers (user_id, question_id, answer_text, answered_at) VALUES (?, ?, ?, ?)",
                    (user_id, q_num, data[key], datetime.now().isoformat())
                )

        # 3. Save Bonuses
        # Calculate bonus if valid
        bonus_total = 0
        try:
            if "да" in str(data.get("passive_subscriber", "")).lower() or "да" in str(data.get("q13", "")).lower(): bonus_total += 1
            if "да" in str(data.get("active_partner", "")).lower() or "да" in str(data.get("q14", "")).lower(): bonus_total += 2
            if "да" in str(data.get("investor_trader", "")).lower() or "да" in str(data.get("q15", "")).lower(): bonus_total += 3
        except:
            pass
            
        await db.execute(
            "INSERT INTO user_bonuses (user_id, bonus_total, current_balance, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, bonus_total, bonus_total, datetime.now().isoformat())
        )
        await db.commit()


@dp.callback_query(F.data == "survey")
async def survey_start(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id

    # is_subscribed = await check_channel_subscription(bot, user_id, CHANNEL_ID)
    # if not is_subscribed:
    #    builder = InlineKeyboardBuilder()
    #    builder.add(types.InlineKeyboardButton(text="Подписаться", url=CHANNEL_URL))
    #    builder.add(types.InlineKeyboardButton(text="Я подписался", callback_data="start_survey"))
    #    builder.adjust(1)
    #    await callback.message.answer("Для прохождения опроса необходимо подписаться на наш канал.", reply_markup=builder.as_markup())
    #    await callback.answer()
    #    return

    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT has_completed_survey FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()

        if user and user[0] == 1:
            try:
                await callback.answer("Вы уже проходили опрос.", show_alert=True)
            except Exception:
                pass
            return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="СТАРТ", callback_data="start_survey"))

    await callback.message.answer(SURVEY_GREETING, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "start_survey")
async def start_survey(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return

    user_id = callback.from_user.id
    
    # --- GLOBAL USER CHECK ---
    # --- GLOBAL USER CHECK ---
    try:
        import_success = await import_global_user(
             user_id, 
             callback.from_user.username or "", 
             callback.from_user.first_name or "", 
             callback.from_user.last_name or ""
        )
        if import_success:
             await callback.message.answer("✅ Ваши данные успешно импортированы из общего профиля! Вы зарегистрированы в этом боте.")
             await state.clear()
             builder = InlineKeyboardBuilder()
             builder.add(types.InlineKeyboardButton(text="🏪 Перейти в магазин", callback_data="main_shop_page"))
             await callback.message.answer(
                "Регистрация завершена. Добро пожаловать!",
                reply_markup=builder.as_markup()
             )
             await callback.answer()
             return

    except Exception as e:
        if "limit" in str(e).lower():
             await callback.message.answer("❌ Вы не можете подписаться на этого бота, так как достигли лимита подписок (максимум 3 бота).")
             await callback.answer()
             return
        print(f"Global DB Error in start_survey: {e}")
        import traceback
        traceback.print_exc()
    # -------------------------

    await state.set_state(SurveyStates.Q3)
    # Автоматически заполняем username если есть
    if callback.from_user.username:
        await state.update_data(q3=f"@{callback.from_user.username}")
        await callback.message.answer(f"Ваш username: @{callback.from_user.username}\n\n{SURVEY_QUESTIONS[4]}")
        await state.set_state(SurveyStates.Q4)
    else:
        await callback.message.answer(SURVEY_QUESTIONS[3])
    await callback.answer()

from filters import IsBadWord

from filters import IsBadWord

async def check_bad_words(message: Message, state: FSMContext) -> bool:
    filter_instance = IsBadWord()
    is_bad = await filter_instance(message)
    if is_bad:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer("❌ Использование нецензурной лексики запрещено в нашем сообществе!")
        return True
    return False







@dp.message(IsBadWord(), SurveyStates.Q3)
async def process_q3_badword(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer("❌ Использование нецензурной лексики запрещено в нашем сообществе!")
    return

@dp.message(SurveyStates.Q3)
async def process_q3(message: Message, state: FSMContext):
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q3=message.text)
    await message.answer(SURVEY_QUESTIONS[4])
    await state.set_state(SurveyStates.Q4)

from filters import IsBadWord

@dp.message(SurveyStates.Q4)
async def process_q4(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q4=message.text)
    await message.answer(SURVEY_QUESTIONS[6])
    await state.set_state(SurveyStates.Q6)



@dp.message(SurveyStates.Q6)
async def process_q6(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q6=message.text)
    await message.answer(SURVEY_QUESTIONS[7])
    await state.set_state(SurveyStates.Q7)

@dp.message(SurveyStates.Q7)  # Email
async def process_q7(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if not is_valid_email(message.text):
        await message.answer("Пожалуйста, введите корректный email")
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q7=message.text)
    await message.answer(SURVEY_QUESTIONS[9])
    await state.set_state(SurveyStates.Q9)



@dp.message(SurveyStates.Q9)
async def process_q9(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q9=message.text)
    await message.answer(SURVEY_QUESTIONS[10])
    await state.set_state(SurveyStates.Q10)

@dp.message(SurveyStates.Q10)
async def process_q10(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q10=message.text)
    await message.answer(SURVEY_QUESTIONS[11])
    await state.set_state(SurveyStates.Q11)

@dp.message(SurveyStates.Q11)
async def process_q11(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q11=message.text)
    await message.answer(SURVEY_QUESTIONS[12])
    await state.set_state(SurveyStates.Q12)

@dp.message(SurveyStates.Q12)
async def process_q12(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q12=message.text)
    await message.answer(SURVEY_QUESTIONS[13])
    await state.set_state(SurveyStates.Q13)

@dp.message(SurveyStates.Q13)
async def process_q13(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q13=message.text)
    await message.answer(SURVEY_QUESTIONS[14])
    await state.set_state(SurveyStates.Q14)

@dp.message(SurveyStates.Q14)
async def process_q14(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q14=message.text)
    await message.answer(SURVEY_QUESTIONS[15])
    await state.set_state(SurveyStates.Q15)

@dp.message(IsBadWord(), SurveyStates.Q15)
async def process_q15_badword(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer("❌ Использование нецензурной лексики запрещено в нашем сообществе!")
    return

@dp.message(SurveyStates.Q15)
async def process_q15(message: Message, state: FSMContext):
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q15=message.text)
    await message.answer(SURVEY_QUESTIONS[16])
    await state.set_state(SurveyStates.Q16)

@dp.message(SurveyStates.Q16)
async def process_q16(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return

    user_id = message.from_user.id
    await state.update_data(q16=message.text)

    data = await state.get_data()

    bonus_total = 0
    try:
        if "да" in data.get("q13", "").lower(): bonus_total += 1
        if "да" in data.get("q14", "").lower(): bonus_total += 2
        if "да" in data.get("q15", "").lower(): bonus_total += 3
        try:
            q16_bonus = float(data.get("q16", "0"))
            bonus_total += q16_bonus
        except ValueError:
            pass
    except Exception:
        pass

    async with aiosqlite.connect("bot_database.db") as db:
        # Обновляем информацию о прохождении опроса
        await db.execute(
            """
            INSERT OR REPLACE INTO users (
                user_id, username, first_name, last_name, has_completed_survey, created_at,
                survey_date, full_name, birth_date, location, email, phone, employment,
                financial_problem, social_problem, ecological_problem, passive_subscriber,
                active_partner, investor_trader, business_proposal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                message.from_user.username or "",
                data.get("first_name", ""),
                data.get("last_name", ""),
                1,
                datetime.now().isoformat(),
                datetime.now().strftime("%Y-%m-%d"), # Автоматическая дата
                data.get("q4", ""),
                "", # Дата рождения удалена
                data.get("q6", ""),
                data.get("q7", ""),
                "", # Телефон удален
                data.get("q9", ""),
                data.get("q10", ""),
                data.get("q11", ""),
                data.get("q12", "") if is_valid_proposal(data.get("q12", "")) else "",
                data.get("q13", ""),
                data.get("q14", ""),
                data.get("q15", ""),
                data.get("q16", "")
            )
        )

        # Сохраняем ответы на вопросы
        for q_num in [3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]:
            await db.execute(
                "INSERT INTO survey_answers (user_id, question_id, answer_text, answered_at) VALUES (?, ?, ?, ?)",
                (user_id, q_num, data.get(f"q{q_num}", ""), datetime.now().isoformat())
            )
    
        # Сохраняем бонусы
        await db.execute(
            "INSERT INTO user_bonuses (user_id, bonus_total, current_balance, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, bonus_total, bonus_total, datetime.now().isoformat())
        )
        await db.commit()

    # --- SAVE TO GLOBAL DB ---
    try:
        # Sanitize Q3 (Username) to ensure single @
        if "q3" in data and data["q3"]:
             clean_q3 = data["q3"].replace("@", "").strip()
             data["q3"] = f"@{clean_q3}"

        await save_global_user(
            user_id, 
            message.from_user.username or "", 
            data.get("first_name", "") + " " + data.get("last_name", ""),
            data # Saving all state data (q3, q4, etc.)
        )
        await register_user_subscription(user_id, BOT_FOLDER_NAME)
    except Exception as global_e:
        print(f"Error saving to global DB: {global_e}")
    # -------------------------

    # Process referral
    referrer_id = data.get("referrer_id")
    if referrer_id:
        try:
             from referral_system import process_referral
             await process_referral(user_id, referrer_id)
        except Exception as e:
             print(f"Error processing referral in survey: {e}")

    try:
        # Отправляем уведомление о создании/обновлении профиля
        await send_user_notification(bot, user_id, {})
    except Exception as e:
        print(f"Ошибка отправки уведомления о профиле: {e}")

    from google_sheets import sync_db_to_google_sheets
    asyncio.create_task(sync_db_to_google_sheets())

    await message.answer(
        """Уважаемый подписчик! 
В опросе вы заявили свою самую важную проблему - она может быть не только личной, но и общей также и для других подписчиков, партнеров и инвесторов. С целью взаимодействия с ними вы можете выбрать здесь в меню ТОЛЬКО ОДНУ КНОПКУ Телеграм сообщества, которое наиболее соответствует вашей проблеме, и перейти в его чат-бот, где будет создан ваш личный профиль с учётом ваших данных, активности и баланса бонусов. 
ЖЕЛАЕМ ВАМ УСПЕШНОГО РЕШЕНИЯ ВАШИХ ПРОБЛЕМ В КЛУБЕ ПО ОБЩИМ ИНТЕРЕСАМ!"""
    )
    
    # Send Confirmation Message with Legal Docs buttons
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📜 Политика конфиденциальности", callback_data="get_legal_privacy"))
    builder.add(types.InlineKeyboardButton(text="📜 Пользовательское соглашение", callback_data="get_legal_terms"))
    builder.add(types.InlineKeyboardButton(text="✅ Подтверждаю", callback_data="confirm_legal"))
    builder.adjust(1)
    
    await message.answer(
        "✅ Подтверждаю, что мне больше 18 лет, я ознакомился и обязуюсь выполнять как подписчик Пользовательское соглашение и Политику конфиденциальности в Сообществе.",
        reply_markup=builder.as_markup()
    )
    await state.clear() # Clear state after survey is done
@dp.callback_query(F.data == "get_legal_privacy")
async def get_legal_privacy(callback: CallbackQuery):
    content = await get_legal_document("privacy_policy")
    if content:
        file = BufferedInputFile(content.encode('utf-8'), filename="privacy_policy.txt")
        await callback.message.answer_document(file, caption="📜 Политика конфиденциальности")
    else:
        await callback.answer("Документ не найден", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "get_legal_terms")
async def get_legal_terms(callback: CallbackQuery):
    content = await get_legal_document("user_agreement")
    if content:
        file = BufferedInputFile(content.encode('utf-8'), filename="user_agreement.txt")
        await callback.message.answer_document(file, caption="📜 Пользовательское соглашение")
    else:
        await callback.answer("Документ не найден", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "confirm_legal")
async def confirm_legal(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Дом/Жилье",
        url="https://t.me/Better_House_Bot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Автотехника",
        url="https://t.me/BestAutoAviaBot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Бизнес/Партнерство",
        url="https://t.me/bestsocialbot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Строительство/Ремонт",
        url="https://t.me/LandHouseBot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Проекты/Проблемы",
        url="t.me/wonderful_project_bot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Капиталы для инвестиций",
        url="https://t.me/Our_Inv_Bot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Финансы/Деньги",
        url="https://t.me/OurWonderfulBot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Образование/Профессия",
        url="https://t.me/Explore_Bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Стоимость/безопасность жизни",
        url="https://t.me/life_protection_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Инфляция/Потери",
        url="https://t.me/without_losses_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Семейное благополучие/Демография",
        url="https://t.me/ForBestFamilyBot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Оплата долгов",
        url="https://t.me/repay_all_debts_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Благотворительность",
        url="https://t.me/care_to_need_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Поддержка пенсионеров",
        url="https://t.me/pension_growth_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Православная община",
        url="https://t.me/BlessMyBot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Экология/Решение проблем",
        url="https://t.me/problems_in_nature_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="назад",
        callback_data="back_to_showcase"
    ))
    builder.add(types.InlineKeyboardButton(
        text="выход из чат-бота",
        url="https://t.me/+b6yAidzNRd8yMTgy"
    ))

    builder.adjust(1)

    await callback.message.edit_text(
        text="Выберите в меню и нажмите кнопку по вашей главной проблеме для перехода в свое целевое сообщество⏬",
        reply_markup=builder.as_markup()
    )
    await callback.answer()



from dispatcher import dp

@dp.callback_query(F.data == "end_surrey")
async def end_surrey(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Дом/Жилье",
        url="https://t.me/Better_House_Bot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Автотехника ",
        url="https://t.me/BestAutoAviaBot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Здоровье/Медицина",
        url="https://t.me/gifthealthbot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Бизнес/Партнерство",
        url="https://t.me/bestsocialbot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Проекты/Проблемы",
        url="t.me/wonderful_project_bot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Капиталы для инвестиций",
        url="https://t.me/Our_Inv_Bot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Финансы/Деньги",
        url="https://t.me/OurWonderfulBot"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Образование/Профессия",
        url="https://t.me/Explore_Bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Стоимость/безопасность жизни",
        url="https://t.me/life_protection_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Инфляция/Потери",
        url="https://t.me/without_losses_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Семейное благополучие/Демография",
        url="https://t.me/ForBestFamilyBot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Оплата долгов",
        url="https://t.me/repay_all_debts_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Благотворительность",
        url="https://t.me/care_to_need_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Поддержка пенсионеров",
        url="https://t.me/pension_growth_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Православная община",
        url="https://t.me/BlessMyBot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="Экология/Решение проблем",
        url="https://t.me/problems_in_nature_bot "
    ))
    builder.add(types.InlineKeyboardButton(
        text="назад",
        callback_data="back_to_showcase"
    ))
    builder.add(types.InlineKeyboardButton(
        text="выход из чат-бота",
        url="https://t.me/+KE2p9KvWHeMyZTcy "
    ))

    builder.adjust(1, 1, 1)

    if callback.message.caption is not None:

        await callback.message.edit_caption(
            caption="Выберите в меню и нажмите кнопку по вашей главной проблеме для перехода в свое целевое сообщество⏬",
            reply_markup=builder.as_markup()
        )
    else:

        await callback.message.edit_text(
            text="Выберите в меню и нажмите кнопку по вашей главной проблеме для перехода в свое целевое сообщество⏬",
            reply_markup=builder.as_markup()
        )
    await callback.answer()



async def links(callback: CallbackQuery, name_bot, url_bot, url_chanel, url_group):
    text = "выберите кнопку для перехода:"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="чат-бот "+name_bot,
        url=url_bot
    ))
    builder.add(types.InlineKeyboardButton(
        text="канал",
        url=url_chanel
    ))
    builder.add(types.InlineKeyboardButton(
        text="группа",
        url=url_group
    ))
    builder.add(types.InlineKeyboardButton(
        text="назад",
        callback_data="end_surrey"
    ))
    builder.adjust(1, 1, 1, 1)
    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "besthome_links")
async def besthome_links(callback: CallbackQuery):

    text = "выберите кнопку для перехода:"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="чат-бот BestHome",
        callback_data=f"handle_besthome_integration_callback"
    ))

    builder.add(types.InlineKeyboardButton(
        text="назад",
        callback_data="end_surrey"
    ))
    builder.adjust(1, 1, 1, 1)
    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "automotive_equipment_links")
async def automotive_equipment_links(callback: CallbackQuery):
    text = "выберите кнопку для перехода:"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="чат-бот Auto7bot",
        callback_data=f"handle_autoavia_integration_callback"
    ))
    builder.add(types.InlineKeyboardButton(
        text="канал",
        url="https://t.me/+7c-jajcT1RdkNDAy"
    ))
    builder.add(types.InlineKeyboardButton(
        text="группа",
        url="https://t.me/+-f-UEXHQlLRmOGMy"
    ))
    builder.add(types.InlineKeyboardButton(
        text="назад",
        callback_data="end_surrey"
    ))
    builder.adjust(1, 1, 1, 1)
    if callback.message.caption is not None:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "heals_links")
async def heals_links(callback: CallbackQuery):

    await links(callback, "your health",
                "https://t.me/gifthealthbot ",
                "https://t.me/+KE2p9KvWHeMyZTcy ",
                "https://t.me/+BpWWJWVExBtmMDJi ")

@dp.callback_query(F.data == "building_links")
async def building_links(callback: CallbackQuery):

    await links(callback, "LandHouse",
                "https://t.me/LandHouseBot",
                "https://t.me/+K8hzEWgStrthZjIy",
                "https://t.me/+e_mnyNQvKrE0NDky ")

@dp.callback_query(F.data == "project_links")
async def project_links(callback: CallbackQuery):

    await links(callback, "best project",
                "https://t.me/wonderful_project_bot",
                "https://t.me/+H9hPjlbyKHFlZjhi",
                "https://t.me/+9IBiBRivtbYxZDM6")

@dp.callback_query(F.data == "Investments_links")
async def Investments_links(callback: CallbackQuery):

    await links(callback, "Investments",
                "https://t.me/Our_Inv_Bot",
                "https://t.me/+Za9_9dD6hOEwZWQy",
                "https://t.me/+TczWbajLzshiNmEy")

@dp.callback_query(F.data == "social_links")
async def social_links(callback: CallbackQuery):

    await links(callback, "social",
                "https://t.me/bestsocialbot",
                "https://t.me/+b6yAidzNRd8yMTgy",
                "https://t.me/+kSPm1u0tZ8Q4OTA6")

@dp.callback_query(F.data == "Learn_links")
async def Learn_links(callback: CallbackQuery):

    await links(callback, "Learn",
                "https://t.me/Explore_Bot",
                "https://t.me/+xNHy5csn6e1kODEy",
                "https://t.me/+82VfGHteSh81N2Yy ")

@dp.callback_query(F.data == "life_protection_bot_links")
async def life_protection_bot_links(callback: CallbackQuery):

    await links(callback, "life_protection_bot",
                "https://t.me/life_protection_bot",
                "https://t.me/+URqrogxy_sgwOTUy",
                "https://t.me/+vd5H9nH3JBw2NjFi")

@dp.callback_query(F.data == "inflation_links")
async def inflation_links(callback: CallbackQuery):

    await links(callback, "inflation",
                "https://t.me/without_losses_bot",
                "https://t.me/+-eXp1btH31hhODJi",
                "https://t.me/+VxvOoPmu_n1mMTUy")

@dp.callback_query(F.data == "ForBestFamily_links")
async def ForBestFamily_links(callback: CallbackQuery):

    await links(callback, "ForBestFamily",
                "https://t.me/ForBestFamilyBot",
                "https://t.me/+s8sIatUAZsswMGEy",
                "https://t.me/+8JVt6CddS_thNWU6")

@dp.callback_query(F.data == "debts_links")
async def debts_links(callback: CallbackQuery):

    await links(callback, "repay all debts",
                "https://t.me/repay_all_debts_bot",
                "https://t.me/+58b5XG-_r7QwNjIy",
                "https://t.me/+TjjczMcJt0xkOTFi")

@dp.callback_query(F.data == "care_to_need_links")
async def care_to_need_links(callback: CallbackQuery):

    await links(callback, "care to need",
                "https://t.me/care_to_need_bot",
                "https://t.me/+DhW5MtE3jxEyNzdi",
                "https://t.me/+AvnAL7rUG0A5ZDMy")

@dp.callback_query(F.data == "pension_links")
async def pension_links(callback: CallbackQuery):

    await links(callback, "pension growth",
                "https://t.me/pension_growth_bot",
                "https://t.me/+tMvIlAqNCJM0YTZi",
                "https://t.me/+M4LXh9a2MYVkMTgy")

@dp.callback_query(F.data == "Bless_links")
async def Bless_links(callback: CallbackQuery):

    await links(callback, "Bless",
                "https://t.me/BlessMyBot",
                "https://t.me/+lmrs_MNK7dg5Y2Uy",
                "https://t.me/+Jk4_poSUzF42ZWZi")

@dp.callback_query(F.data == "nature_links")
async def nature_links(callback: CallbackQuery):

    await links(callback, "problems in nature",
                "https://t.me/problems_in_nature_bot",
                "https://t.me/+y7u2xXDQIUA3NGMy",
                "https://t.me/+x_qEjMskwVoyOGRi")

async def sync_local_to_global(user_id: int):
    """
    Syncs user data between Local DB and Global DB.
    1. If user in Global DB and Local user invalid -> Import from Global
    2. If user in Global DB and Local user valid -> Register subscription
    3. If user ONLY in Local DB and valid -> Export to Global
    """
    print(f"DEBUG: sync_local_to_global called for {user_id}")
    try:
        from shared_storage.global_db import get_global_user_info
        
        # Check if already in global DB
        global_survey = await get_global_user_survey(user_id)
        
        if global_survey:
            # User exists globally. Check local status.
            async with aiosqlite.connect("bot_database.db") as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT has_completed_survey FROM users WHERE user_id = ?", (user_id,))
                local_user = await cursor.fetchone()
                
                # If local user missing or incomplete, we IMPORT
                if not local_user or not local_user['has_completed_survey']:
                    print(f"DEBUG: Local user {user_id} is incomplete/missing but exists globally. Importing...")
                    
                    # Get basic info
                    global_info = await get_global_user_info(user_id)
                    username = global_info['username'] if global_info else ""
                    # extracting first/last name from full name is tricky, so we leave empty or try split
                    # For import_global_user, we need these.
                    # We can try to use survey data q4 if needed, but import_global_user handles it.
                    
                    await import_global_user(user_id, username, "", "") 
                    return

            print(f"DEBUG: User {user_id} found in Global DB and Local DB is valid. Registering subscription")
            await register_user_subscription(user_id, BOT_FOLDER_NAME)
            return

        print(f"DEBUG: Connecting to local DB for {user_id}")
        async with aiosqlite.connect("bot_database.db") as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_row = await cursor.fetchone()
            
            if not user_row:
                print(f"DEBUG: User {user_id} not found in local users table")
                return
            if not user_row['has_completed_survey']:
                print(f"DEBUG: User {user_id} has not completed survey")
                return

            print(f"DEBUG: User {user_id} found locally, preparing global data")
            survey_data = {
                "q3": f"@{str(user_row['username']).strip().lstrip('@')}" if user_row['username'] else "",
                "q4": user_row['full_name'] or "",
                "q6": user_row['location'] or "",
                "q7": user_row['email'] or "",
                "q9": user_row['employment'] or "",
                "q10": user_row['financial_problem'] or "",
                "q11": user_row['social_problem'] or "",
                "q12": user_row['ecological_problem'] or "",
                "q13": user_row['passive_subscriber'] or "",
                "q14": user_row['active_partner'] or "",
                "q15": user_row['investor_trader'] or "",
                "q16": user_row['business_proposal'] or "",
                "first_name": user_row['first_name'] or "",
                "last_name": user_row['last_name'] or ""
            }

            print(f"DEBUG: Saving user {user_id} to Global DB")
            await save_global_user(
                user_id,
                user_row['username'] or "",
                (user_row['first_name'] or "") + " " + (user_row['last_name'] or ""),
                survey_data
            )
            await register_user_subscription(user_id, BOT_FOLDER_NAME)
            print(f"DEBUG: Synced existing user {user_id} to Global DB")
            
    except Exception as e:
        print(f"Error executing sync_local_to_global: {e}")
        import traceback
        traceback.print_exc()

async def import_global_user(user_id: int, username: str, first_name: str, last_name: str) -> bool:
    """
    Checks if user exists in global DB. If so, imports data to local DB,
    registers subscription, and triggers sync.
    Returns True if imported, False if not found.
    Raises Exception if limit reached.
    """
    
    # Check subscription limit first
    sub_count = await get_user_subscription_count(user_id)
    is_subbed = await is_user_subscribed(user_id, BOT_FOLDER_NAME)
    
    # Log for debug
    print(f"DEBUG: import_global_user check {user_id}: sub_count={sub_count}, is_subbed={is_subbed}, bot={BOT_FOLDER_NAME}")
    
    if sub_count >= 3 and not is_subbed:
        raise Exception("Subscription limit reached")

    # Check existing survey data
    global_survey = await get_global_user_survey(user_id)
    if not global_survey:
        print(f"DEBUG: import_global_user {user_id}: No global survey found")
        return False
        
    print(f"DEBUG: import_global_user {user_id}: Found global survey, importing...")
    
    # COPY DATA TO LOCAL DB
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO users (
                user_id, username, first_name, last_name, has_completed_survey, created_at,
                survey_date, full_name, birth_date, location, email, phone, employment,
                financial_problem, social_problem, ecological_problem, passive_subscriber,
                active_partner, investor_trader, business_proposal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                first_name,
                last_name,
                1,
                datetime.now().isoformat(),
                datetime.now().strftime("%Y-%m-%d"),
                global_survey.get("q4", ""),
                "",
                global_survey.get("q6", ""),
                global_survey.get("q7", ""),
                "",
                global_survey.get("q9", ""),
                global_survey.get("q10", ""),
                global_survey.get("q11", ""),
                global_survey.get("q12", ""),
                global_survey.get("q13", ""),
                global_survey.get("q14", ""),
                global_survey.get("q15", ""),
                global_survey.get("q16", "")
            )
        )
        
        # Copy answers
        for q_num in [3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]:
            val = global_survey.get(f"q{q_num}", "")
            if q_num == 3 and val:
                # Ensure single @ for username
                val = f"@{str(val).replace('@', '').strip()}"

            await db.execute(
                "INSERT INTO survey_answers (user_id, question_id, answer_text, answered_at) VALUES (?, ?, ?, ?)",
                (user_id, q_num, val, datetime.now().isoformat())
            )

        # Initialize bonuses (independent)
        await db.execute(
            "INSERT OR IGNORE INTO user_bonuses (user_id, bonus_total, current_balance, updated_at) VALUES (?, 0, 0, ?)",
            (user_id, datetime.now().isoformat())
        )
        await db.commit()
    
    # Register subscription
    await register_user_subscription(user_id, BOT_FOLDER_NAME)
    
    # Sync to Google Sheets
    from google_sheets import sync_db_to_google_sheets
    asyncio.create_task(sync_db_to_google_sheets())
    print(f"DEBUG: Successfully imported Global User {user_id}")
    
    return True


