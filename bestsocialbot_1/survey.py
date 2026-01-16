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
from filters import is_valid_email, is_valid_phone
from utils import check_blocked_user
from handler_integration import handle_besthome_integration_callback, handle_autoavia_integration_callback

class SurveyStates(StatesGroup):
    START = State()
    Q1 = State()
    Q2 = State()
    Q3 = State()
    Q4 = State()
    Q5 = State()
    Q6 = State()
    Q7 = State()
    Q8 = State()
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
    1: "1. ГГ-ММ-ДД опроса подписчика",
    2: "2. Телеграм ID подписчика",
    3: "3. Телеграм @username подписчика",
    4: "4. ФИО подписчика",
    5: "5. ГГ-ММ-ДД рождения подписчика",
    6: "6. Место жительства: область, район, город, поселок",
    7: "7. Действующая эл. почта подписчика",
    8: "8. Мобильный телефон подписчика",
    9: "9. Текущая занятость подписчика (учеба, свой бизнес, работа по найму, ИП, ООО, самозанятый, пенсионер, иное - пояснить)",
    10: "10. Cамая важная финансовая проблема (долги, текущие расходы, убытки бизнеса, нужны инвесторы или долевые партнеры, иное - пояснить)",
    11: "11. Самая важная социальная проблема (улучшение семьи, здоровья, жилья, образования, иное - пояснить)",
    12: "12. Самая важная экологическая проблема в вашем регионе (загрязнения, пожары, наводнения, качество воды, загазованность, иное - пояснить)",
    13: "13. Вы будете пассивным подписчиком в нашем ТГ сообществе для выполнения в контенте просмотров, реакций, комментариев, опросов? - Вы получаете по 1,0 бонусу-монете в месяц",
    14: "14. Вы будете активным партнером - предпринимателем для развития и роста ТГ сообщества? - Вы получаете по 2,0 бонуса-монеты в месяц",
    15: "15. Вы будете инвестором или биржевым трейдером по продажам цифровым активов в сообществе? - Вы получаете по 3,0 бонуса-монеты в месяц",
    16: "16. У вас есть свое бизнес-предложение сотрудничества в сообществе? - Оцените здесь его полезность для вас в бонусах-монетах в месяц"
}

SURVEY_FINISH = """
Уважаемый подписчик! 
В опросе вы заявили свою самую важную проблему - она может быть не только личной, но и общей также и для других подписчиков, партнеров и инвесторов. С целью взаимодействия с ними вы можете выбрать здесь в меню ТОЛЬКО ОДНУ КНОПКУ Телеграм сообщества, которое наиболее соответствует вашей проблеме, и перейти в его чат-бот, где будет создан ваш личный профиль с учётом ваших данных, активности и баланса бонусов. 
ЖЕЛАЕМ ВАМ УСПЕШНОГО РЕШЕНИЯ ВАШИХ ПРОБЛЕМ В КЛУБЕ ПО ОБЩИМ ИНТЕРЕСАМ!
"""

from datetime import datetime


from db import check_account_status




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
            await callback.answer("Вы уже проходили опрос.", show_alert=True)
            return

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="СТАРТ", callback_data="start_survey"))

    await callback.message.answer(SURVEY_GREETING, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "start_survey")
async def start_survey(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return

    await state.set_state(SurveyStates.Q1)
    await callback.message.answer(SURVEY_QUESTIONS[1])
    await callback.answer()

from filters import IsBadWord

from filters import IsBadWord

async def check_bad_words(message: Message, state: FSMContext) -> bool:
    filter_instance = IsBadWord()
    is_bad = await filter_instance(message)
    if is_bad:
        await message.delete()
        await message.answer("❌ Использование нецензурной лексики запрещено в нашем сообществе!")
        return True
    return False



@dp.message(SurveyStates.Q1)
async def process_q1(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    try:
        datetime.strptime(message.text, "%y-%m-%d")
    except ValueError:
        await message.answer("Пожалуйста, введите дату в формате ГГ-ММ-ДД (например, 90-05-15)")
        return

    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q1=message.text)
    await message.answer(SURVEY_QUESTIONS[2])
    await state.set_state(SurveyStates.Q2)

@dp.message(IsBadWord(), SurveyStates.Q2)
async def process_q2_badword(message: Message, state: FSMContext):
    await message.delete()
    await message.answer("❌ Использование нецензурной лексики запрещено в нашем сообществе!")
    return

@dp.message(SurveyStates.Q2)
async def process_q2(message: Message, state: FSMContext):
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите числовой Telegram ID.")
        return

    await state.update_data(q2=message.text)
    await message.answer(SURVEY_QUESTIONS[3])
    await state.set_state(SurveyStates.Q3)

@dp.message(IsBadWord(), SurveyStates.Q3)
async def process_q3_badword(message: Message, state: FSMContext):
    await message.delete()
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
    await message.answer(SURVEY_QUESTIONS[5])
    await state.set_state(SurveyStates.Q5)

@dp.message(SurveyStates.Q5)
async def process_q5(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    try:
        datetime.strptime(message.text, "%y-%m-%d")
    except ValueError:
        await message.answer("Пожалуйста, введите дату в формате ГГ-ММ-ДД (например, 90-05-15)")
        return

    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q5=message.text)
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
    await message.answer(SURVEY_QUESTIONS[8])
    await state.set_state(SurveyStates.Q8)

@dp.message(SurveyStates.Q8)  # Телефон
async def process_q8(message: Message, state: FSMContext):
    if await check_bad_words(message, state):
        return
    if not is_valid_phone(message.text):
        await message.answer("Пожалуйста, введите корректный номер телефона (например, +79991234567)")
        return
    if len(message.text) > 150:
        await message.answer("Ответ должен содержать не более 150 символов.")
        return

    await state.update_data(q8=message.text)
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
    await message.delete()
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
                data.get("q1", ""),
                data.get("q4", ""),
                data.get("q5", ""),
                data.get("q6", ""),
                data.get("q7", ""),
                data.get("q8", ""),
                data.get("q9", ""),
                data.get("q10", ""),
                data.get("q11", ""),
                data.get("q12", ""),
                data.get("q13", ""),
                data.get("q14", ""),
                data.get("q15", ""),
                data.get("q16", "")
            )
        )

        # Сохраняем ответы на вопросы
        for q_num in range(1, 17):
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

    from google_sheets import sync_db_to_google_sheets
    asyncio.create_task(sync_db_to_google_sheets())

    await message.answer(
        """Уважаемый подписчик! 
В опросе вы заявили свою самую важную проблему - она может быть не только личной, но и общей также и для других подписчиков, партнеров и инвесторов. С целью взаимодействия с ними вы можете выбрать здесь в меню ТОЛЬКО ОДНУ КНОПКУ Телеграм сообщества, которое наиболее соответствует вашей проблеме, и перейти в его чат-бот, где будет создан ваш личный профиль с учётом ваших данных, активности и баланса бонусов. 
ЖЕЛАЕМ ВАМ УСПЕШНОГО РЕШЕНИЯ ВАШИХ ПРОБЛЕМ В КЛУБЕ ПО ОБЩИМ ИНТЕРЕСАМ!"""
    )
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Дом/Жилье",
        callback_data="handle_besthome_integration"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Автотехника",
        callback_data="handle_autoavia_integration_callback"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Здоровье/Медицина",
        url="https://t.me/gifthealthbot"
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
        text="Бизнес/Партнерство",
        url="https://t.me/OurSocialBot"
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
        url="https://t.me/+vz7-Ko4rDy03Yjhi"
    ))


    builder.adjust(1, 1, 1)



    await message.answer(
        text="Выберите в меню и нажмите кнопку по вашей главной проблеме для перехода в свое целевое сообщество⏬",
        reply_markup=builder.as_markup()
    )


    await state.clear()



from dispatcher import dp

@dp.callback_query(F.data == "end_surrey")
async def end_surrey(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Дом/Жилье",
        callback_data="handle_besthome_integration"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Автотехника ",
        callback_data="handle_autoavia_integration_callback"
    ))
    builder.add(types.InlineKeyboardButton(
        text="Здоровье/Медицина",
        url="https://t.me/gifthealthbot"
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
        text="Бизнес/Партнерство",
        url="https://t.me/OurSocialBot"
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
        url="https://t.me/+vz7-Ko4rDy03Yjhi"
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


