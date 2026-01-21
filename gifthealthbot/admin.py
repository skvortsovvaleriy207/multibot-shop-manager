from aiogram import F, types
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_ID, TELETHON_API_ID, TELETHON_API_HASH, TELETHON_PHONE_NUMBER
from config import COMMON_EXPORT_SHEET_URL, CREDENTIALS_FILE, INVESTORS_SHEET_URL, PARTNERS_SHEET_URL, \
    PARSING_USERS_GOOGLE_SHEET_URL
from dispatcher import dp
from bot_instance import bot
import aiosqlite
from utils import check_blocked_user
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
import pandas as pd
import os
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telethon.sessions import StringSession
import asyncio
from telethon.errors import FloodWaitError
import pytz
from datetime import datetime, time, timedelta
from aiogram.filters import Command



class ParsingStates(StatesGroup):
    waiting_for_links = State()

class Admin2FAStates(StatesGroup):
    waiting_for_code = State()

class AdminCaptchaStates(StatesGroup):
    waiting_for_captcha = State()

admin_2fa_codes = {}
admin_captcha_answers = {}

RU_NUMBERS = {
    0: "ноль", 1: "один", 2: "два", 3: "три", 4: "четыре", 5: "пять", 6: "шесть", 7: "семь", 8: "восемь", 9: "девять",
    10: "десять", 11: "одиннадцать", 12: "двенадцать", 13: "тринадцать", 14: "четырнадцать", 15: "пятнадцать", 16: "шестнадцать", 17: "семнадцать", 18: "восемнадцать", 19: "девятнадцать", 20: "двадцать",
    30: "тридцать", 40: "сорок", 50: "пятьдесят", 60: "шестьдесят", 70: "семьдесят", 80: "восемьдесят", 90: "девяносто", 100: "сто"
}

def number_to_russian_word(n):
    if n in RU_NUMBERS:
        return RU_NUMBERS[n]
    elif n < 100:
        tens = (n // 10) * 10
        ones = n % 10
        return f"{RU_NUMBERS[tens]} {RU_NUMBERS[ones]}"
    else:
        return str(n)

@dp.callback_query(F.data == "admin_panel")
async def admin_captcha_entry_callback(callback: CallbackQuery, state: FSMContext):
    if await check_blocked_user(callback):
        return
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    import random
    number = random.randint(0, 100)
    word = number_to_russian_word(number)
    admin_captcha_answers[user_id] = number
    await callback.message.answer(f"Для входа в админ-панель введите цифрами число: {word}")
    await state.set_state(AdminCaptchaStates.waiting_for_captcha)

@dp.message(AdminCaptchaStates.waiting_for_captcha)
async def admin_captcha_check(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    answer = admin_captcha_answers.get(user_id)
    try:
        if answer is not None and int(message.text.strip()) == answer:
            await message.answer("✅ Капча пройдена! Теперь введите 6-значный код для входа в админ-панель.")
            # Переходим к 2FA
            from random import choices
            import string
            code = ''.join(choices(string.digits, k=6))
            admin_2fa_codes[user_id] = code
            await bot.send_message(user_id, f"Ваш код для входа в админ-панель: {code}")
            await state.set_state(Admin2FAStates.waiting_for_code)
            admin_captcha_answers.pop(user_id, None)
        else:
            await message.answer("❌ Неверный ответ. Попробуйте ещё раз.")
    except Exception:
        await message.answer("❌ Введите число.")

@dp.message(Admin2FAStates.waiting_for_code)
async def admin_2fa_check(message: types.Message, state: FSMContext):
    code = admin_2fa_codes.get(message.from_user.id)
    if code and message.text.strip() == code:
        await message.answer("✅ Доступ к админ-панели разрешён!")
        # Показываем админ-панель после успешной 2FA
        await show_admin_panel(message)
        await state.clear()
        admin_2fa_codes.pop(message.from_user.id, None)
    else:
        await message.answer("❌ Неверный код. Попробуйте ещё раз.")

async def show_admin_panel(message_or_callback):
    builder = InlineKeyboardBuilder()
    # builder.add(types.InlineKeyboardButton(text="📢 Управление контентом", callback_data="admin_content")) # New button (Hidden)
    builder.add(types.InlineKeyboardButton(text="📚 Управление каталогом", callback_data="admin_catalog_manager"))
    builder.add(types.InlineKeyboardButton(text="📋 Основная таблица", callback_data="data_table"))
    builder.add(types.InlineKeyboardButton(text="🏪 Магазин", callback_data="main_shop_page"))
    # builder.add(types.InlineKeyboardButton(text="👤 пассивные подписчики", callback_data="partners_passive"))
    # builder.add(types.InlineKeyboardButton(text="📊 Партнеры", callback_data="partners"))
    # builder.add(types.InlineKeyboardButton(text="💰 Инвесторы", callback_data="investors"))
    # builder.add(types.InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral"))
    builder.add(types.InlineKeyboardButton(text="📤 Парсинг", callback_data="parsing"))
    builder.add(types.InlineKeyboardButton(text="📬 Рассылка", callback_data="mailing"))
    builder.add(types.InlineKeyboardButton(text="🔗 Инвайт", callback_data="invite"))
    builder.add(types.InlineKeyboardButton(text="📊 Планы и отчеты", callback_data="plans_reports"))
    builder.add(types.InlineKeyboardButton(text="💬 Сообщения", callback_data="messages"))
    builder.add(types.InlineKeyboardButton(text="📈 Статистика", callback_data="stats"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_personal_account"))
    builder.adjust(1)
    
    if hasattr(message_or_callback, 'message'):
        msg = message_or_callback.message
        if msg.content_type == types.ContentType.PHOTO:
            await msg.edit_caption(caption="Админ-панель:", reply_markup=builder.as_markup())
        else:
            await msg.edit_text(text="Админ-панель:", reply_markup=builder.as_markup())
    else:
        await message_or_callback.answer("Админ-панель:", reply_markup=builder.as_markup())




# --- Legacy Catalog Management Removed ---
# Use admin_catalog_manager.py instead
# ---------------------------------------


@dp.callback_query(F.data == "data_table")
async def data_table(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    from config import MAIN_SURVEY_SHEET_URL
    url = MAIN_SURVEY_SHEET_URL

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Открыть основную таблицу подписчиков",
        url=url
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_admin"
    ))
    builder.adjust(1)

    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="Основная таблица подписчиков бота:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="Основная таблица подписчиков бота:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()

from aiogram.fsm.context import FSMContext

from aiogram.fsm.context import FSMContext

from aiogram.fsm.context import FSMContext


from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    await show_admin_panel(callback)
    try:
        await callback.answer()
    except:
        pass





@dp.message(F.text, StateFilter(ParsingStates.waiting_for_links))
async def admin_parsing_links_handler(message: types.Message, state: FSMContext):
    links = [message.text.strip()]
    await message.answer("Начинаю парсинг...")
    try:
        all_participants = await process_channel_for_admin(message, links)
    except Exception as e:
        await message.answer(f"Ошибка при парсинге: {e}")
        await state.clear()
        return
    if all_participants is None:
        await message.answer("Произошла неизвестная ошибка при парсинге. Попробуйте позже или проверьте ссылку.")
        await state.clear()
        return
    if not all_participants:
        await message.answer("Не удалось найти ни одного участника. Возможно, у бота нет доступа или чат пустой.")
        await state.clear()
        return
    url = PARSING_USERS_GOOGLE_SHEET_URL
    if not url:
        await message.answer("Ссылка на Google-таблицу для парсинга не указана в config.py!")
        await state.clear()
        return
    df = pd.DataFrame(list(all_participants.values()))
    df.drop_duplicates(subset=['ID'], inplace=True)
    try:
        import gspread
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open_by_url(url)
        worksheet = sh.sheet1
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        for email in ALLOWED_GOOGLE_SHEET_ACCOUNTS:
            try:
                sh.share(email, perm_type='user', role='writer')
            except Exception as e:
                print(f"Ошибка при раздаче прав {email}: {e}")
        await message.answer(f"Готово! Данные сразу сохранены в Google-таблицу: {url}")
    except Exception as e:
        await message.answer(f"Ошибка загрузки в Google-таблицу: {e}")
    await state.clear()

@dp.message(F.document, StateFilter(ParsingStates.waiting_for_links))
async def admin_parsing_file_handler(message: types.Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.endswith('.txt'):
        await message.answer("Пожалуйста, отправьте .txt файл.")
        return
    file_path = f"temp_{message.from_user.id}.txt"
    await doc.download(destination_file=file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f.readlines() if 't.me/' in line or line.strip().startswith('-')]
    os.remove(file_path)
    if not links:
        await message.answer("Не найдено ни одной валидной ссылки или ID в файле.")
        await state.clear()
        return
    await message.answer(f"Найдено {len(links)} ссылок/ID. Начинаю парсинг...")
    try:
        all_participants = await process_channel_for_admin(message, links)
    except Exception as e:
        await message.answer(f"Ошибка при парсинге: {e}")
        await state.clear()
        return
    if all_participants is None:
        await message.answer("Произошла неизвестная ошибка при парсинге. Попробуйте позже или проверьте ссылку.")
        await state.clear()
        return
    if not all_participants:
        await message.answer("Не удалось найти ни одного участника. Возможно, у бота нет доступа или чат пустой.")
        await state.clear()
        return
    url = PARSING_USERS_GOOGLE_SHEET_URL
    if not url:
        await message.answer("Ссылка на Google-таблицу для парсинга не указана в config.py!")
        await state.clear()
        return
    try:
        import gspread
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open_by_url(url)
        worksheet = sh.sheet1
        df = pd.DataFrame(list(all_participants.values()))
        df.drop_duplicates(subset=['ID'], inplace=True)
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        for email in ALLOWED_GOOGLE_SHEET_ACCOUNTS:
            try:
                sh.share(email, perm_type='user', role='writer')
            except Exception as e:
                print(f"Ошибка при раздаче прав {email}: {e}")
        await message.answer(f"Готово! Данные сразу сохранены в Google-таблицу: {url}")
    except Exception as e:
        await message.answer(f"Ошибка загрузки в Google-таблицу: {e}")
    await state.clear()

async def get_entity_safe(client, identifier):
    try:
        if isinstance(identifier, str) and identifier.startswith('-'):
            id_variants = [
                int(identifier),
                int(identifier[1:]),
                int('-100' + identifier[1:]) if not identifier.startswith('-100') else None,
                int(identifier[4:]) if identifier.startswith('-100') else None
            ]
            for id_var in id_variants:
                if id_var is not None:
                    try:
                        return await client.get_entity(id_var)
                    except:
                        continue
            return await client.get_entity(identifier)
        else:
            return await client.get_entity(identifier)
    except Exception as e:
        raise Exception(f"Не удалось получить entity для {identifier}: {str(e)}")

async def get_comments_participants(client, entity, post_id=None):
    participants = {}
    try:
        if post_id is None:
            posts = await client.get_messages(entity, limit=20)
            for post in posts:
                try:
                    async for comment in client.iter_messages(entity, reply_to=post.id):
                        if comment.sender_id and comment.sender_id not in participants:
                            try:
                                user = await client.get_entity(comment.sender_id)
                                participants[user.id] = {
                                    'ID': user.id,
                                    'Username': user.username or "—",
                                    'Телефон': user.phone or "—",
                                    'Имя': f'{user.first_name or ""} {user.last_name or ""}'.strip() or "—",
                                    'Источник': f"Комментарии к посту {post.id}",
                                    'Тип чата': 'Комментарии'
                                }
                            except:
                                continue
                except Exception as e:
                    print(f"⚠️ Ошибка при получении комментариев к посту {post.id}: {e}")
        else:
            async for comment in client.iter_messages(entity, reply_to=post_id):
                if comment.sender_id and comment.sender_id not in participants:
                    try:
                        user = await client.get_entity(comment.sender_id)
                        participants[user.id] = {
                            'ID': user.id,
                            'Username': user.username or "—",
                            'Телефон': user.phone or "—",
                            'Имя': f'{user.first_name or ""} {user.last_name or ""}'.strip() or "—",
                            'Источник': f"Комментарии к посту {post_id}",
                            'Тип чата': 'Комментарии'
                        }
                    except:
                        continue
    except Exception as e:
        print(f"⚠️ Ошибка при парсинге комментариев: {e}")
    return participants

user_client = TelegramClient('user_session', TELETHON_API_ID, TELETHON_API_HASH)

async def process_channel_for_admin(msg, links):
    try:
        await user_client.start(phone=TELETHON_PHONE_NUMBER)
    except Exception as e:
        await msg.answer(f"Ошибка авторизации в Telegram: {e}")
        return None
    all_participants = {}
    for url in links:
        try:
            entity = await get_entity_safe(user_client, url)
            participants = {}
            flood_wait_reported = False
            if hasattr(entity, 'broadcast') and entity.broadcast:
                try:
                    full_channel = await user_client(GetFullChannelRequest(channel=entity))
                    if getattr(full_channel.full_chat, 'participants_count', 0) == 0:
                        await msg.answer(f"Канал {url} не имеет участников или они скрыты. Парсим комментарии...")
                    else:
                        async for user in user_client.iter_participants(entity, aggressive=True, limit=100000):
                            participants[user.id] = {
                                'ID': user.id,
                                'Username': user.username or "—",
                                'Телефон': user.phone or "—",
                                'Имя': f'{user.first_name or ""} {user.last_name or ""}'.strip() or "—",
                                'Источник': url,
                                'Тип чата': 'Канал'
                            }
                    comments_participants = await get_comments_participants(user_client, entity)
                    participants.update(comments_participants)
                except Exception as e:
                    await msg.answer(f"Ошибка при парсинге участников канала {url}: {e}")
            elif hasattr(entity, 'megagroup') and entity.megagroup:
                try:
                    async for user in user_client.iter_participants(entity, aggressive=True, limit=100000):
                        participants[user.id] = {
                            'ID': user.id,
                            'Username': user.username or "—",
                            'Телефон': user.phone or "—",
                            'Имя': f'{user.first_name or ""} {user.last_name or ""}'.strip() or "—",
                            'Источник': url,
                            'Тип чата': 'Супергруппа'
                        }
                except Exception as e:
                    await msg.answer(f"Ошибка при парсинге участников супергруппы {url}: {e}")
            elif hasattr(entity, 'chat_id'):
                try:
                    full_chat = await user_client(GetFullChatRequest(chat_id=entity.id))
                    if getattr(full_chat.full_chat, 'participants_count', 0) == 0:
                        await msg.answer(f"Чат {url} не имеет участников.")
                    else:
                        for participant in full_chat.full_chat.participants.participants:
                            user = await user_client.get_entity(participant.user_id)
                            participants[user.id] = {
                                'ID': user.id,
                                'Username': user.username or "—",
                                'Телефон': user.phone or "—",
                                'Имя': f'{user.first_name or ""} {user.last_name or ""}'.strip() or "—",
                                'Источник': url,
                                'Тип чата': 'Чат'
                            }
                except Exception as e:
                    await msg.answer(f"Ошибка при парсинге участников чата {url}: {e}")
            try:
                async for message in user_client.iter_messages(entity, limit=10000):
                    if message.sender_id and message.sender_id not in participants:
                        try:
                            user = await user_client.get_entity(message.sender_id)
                            participants[user.id] = {
                                'ID': user.id,
                                'Username': user.username or "—",
                                'Телефон': user.phone or "—",
                                'Имя': f'{user.first_name or ""} {user.last_name or ""}'.strip() or "—",
                                'Источник': url,
                                'Тип чата': 'Из сообщений'
                            }
                        except FloodWaitError as fw:
                            if not flood_wait_reported:
                                await msg.answer(f"Слишком много запросов к Telegram. Попробуйте позже. (flood wait: {fw.seconds} сек)")
                                flood_wait_reported = True
                            break
                        except Exception as e:
                            if not flood_wait_reported and 'A wait of' in str(e):
                                await msg.answer(f"Слишком много запросов к Telegram. Попробуйте позже.")
                                flood_wait_reported = True
                            continue
            except Exception as e:
                await msg.answer(f"Не удалось получить сообщения из {url}: {e}")
            all_participants.update(participants)
        except Exception as e:
            await msg.answer(f"Ошибка при парсинге {url}: {str(e)}")
            continue
    return all_participants

@dp.callback_query(F.data == "parsing")
async def parsing_menu_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Открыть таблицу парсинга чужих пользователей",
        url=PARSING_USERS_GOOGLE_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(
        text="Начать парсинг пользователей",
        callback_data="start_parsing_users"
    ))
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_admin"
    ))
    builder.adjust(1)
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="Парсинг чужих пользователей (не подписчики бота):\n\nВыберите действие:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="Парсинг чужих пользователей (не подписчики бота):\n\nВыберите действие:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "start_parsing_users")
async def start_parsing_users_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    await state.set_state(ParsingStates.waiting_for_links)
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="Введите ссылку на канал/группу, ID группы или загрузите .txt файл со списками.")
    else:
        await callback.message.edit_text(text="Введите ссылку на канал/группу, ID группы или загрузите .txt файл со списками.")

@dp.callback_query(F.data == "mailing")
async def mailing_menu_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    from config import MAILING_ADDRESSES_SHEET_URL
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Сделать рассылку", callback_data="do_mailing"))
    builder.add(types.InlineKeyboardButton(text="Таблица рассылки (10 адресатов)", url=MAILING_ADDRESSES_SHEET_URL))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(
            caption="Рассылка по чужим пользователям (не подписчики бота):\n\nВыберите действие:",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            text="Рассылка по чужим пользователям (не подписчики бота):\n\nВыберите действие:",
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "do_mailing")
async def do_mailing_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("Начинаю рассылку по шаблону для первых 10 пользователей с российскими именами из таблицы парсинга...")
    import re
    import gspread
    from config import PARSING_USERS_GOOGLE_SHEET_URL, CREDENTIALS_FILE, INVITE_EXPORT_SHEET_URL, MAILING_ADDRESSES_SHEET_URL
    from datetime import datetime
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL)
    worksheet = sh.sheet1
    users = worksheet.get_all_records()
    russian_names = re.compile(r"^[А-ЯЁ][а-яё]+$")
    filtered_users = []
    for u in users:
        name = str(u.get("Имя") or "").strip()
        first_name = name.split()[0] if name else ""
        if russian_names.match(first_name):
            filtered_users.append(u)
    filtered_users = filtered_users[:10]
    count = 0
    errors = 0
    showcase_photo_url = "https://autonet.bug.hr/img/tko-kupi-овай-бугатти-на-поклон-добива--rolls-ройс_NByTb_.jpg"
    dst_gc = gspread.service_account(filename=CREDENTIALS_FILE)
    dst_sh = dst_gc.open_by_url(INVITE_EXPORT_SHEET_URL)
    dst_ws = dst_sh.sheet1
    invite_headers = [
        "User ID", "Имя:", "Фото:", "Истории:", "Пол:", "Номер телефона", "Дата парсинга", "ТГ ресурс для парсинга", "Дата рассылки / результат", "Дата подписки в ТГ канал / результат", "Дата инвайта в ТГ бот / результат", "Примечание"
    ]
    if not dst_ws.get_all_values():
        dst_ws.append_row(invite_headers)
    try:
        mailing_gc = gspread.service_account(filename=CREDENTIALS_FILE)
        mailing_sh = mailing_gc.open_by_url(MAILING_ADDRESSES_SHEET_URL)
        mailing_ws = mailing_sh.sheet1
        mailing_ws.clear()
        if filtered_users:
            mailing_ws.update([list(filtered_users[0].keys())] + [list(u.values()) for u in filtered_users])
    except Exception as e:
        print(f"Ошибка при обновлении листа 10 адресатов: {e}")
    for user in filtered_users:
        user_id = user.get("ID")
        full_name = user.get("Имя") or user.get("Full Name") or "друг"
        invite_text = f"Здравствуйте, {full_name}!\n" \
            "Данное сообщение - это ваше персональное приглашение в чат-бот Телеграм группы https://t.me/+-f-UEXHQlLRmOGMy и канала https://t.me/+7c-jajcT1RdkNDAy.\n" \
            "Подписчики, деловые партнеры и инвесторы получают за активность в нашем сообществе airdrop и bounty ценных цифровых монет.\n" \
            "Владельцы монет имеют право продать или еще купить монеты, а также нужные товары и услуги в бот-магазине сообщества, который служит для:\n" \
            "\nопроса наиболее важных проблем подписчиков, учета и выполнения заявок подписчиков в магазине чат-бота,\n" \
            "ежемесячного поощрения активности каждого подписчика, партнера, инвестора ценными бонусами-монетами,\n" \
            "сотрудничества подписчиков, партнеров и инвесторов сообщества для конвертации-продажи своих накопленных бонусов-монет,\n" \
            "поддержки создания и развития региональных ИП, ООО, потребительских кооперативов и фондов участников,\n" \
            "совместного роста капиталов участников с целью решения их заявленных при опросе проблем, улучшения их здоровья, авто-техники, жилья, образоваания.\n" \
            "Если же таких социальных, финансовых и иных проблем у вас нет и не будет, тогда, пожалуйста, просто проигнорируйте это сообщение."
        result = "OK"
        try:
            await bot.send_photo(user_id, showcase_photo_url, caption=invite_text)
            count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            errors += 1
            result = f"Ошибка: {e}"
        invite_row = [
            user.get("ID", ""),
            user.get("Имя", ""),
            user.get("Фото", ""),
            user.get("Истории", ""),
            user.get("Пол", ""),
            user.get("Номер телефона", ""),
            user.get("Дата парсинга", ""),
            user.get("ТГ ресурс для парсинга", ""),
            str(datetime.now().date()) + " / " + result,
            "",  # Дата подписки в ТГ канал / результат
            "",  # Дата инвайта в ТГ бот / результат
            ""   # Примечание
        ]
        dst_ws.append_row(invite_row)
    await callback.message.answer(f"Рассылка завершена. Успешно отправлено: {count}, ошибок: {errors}. Только 10 адресатов с российскими именами.")

@dp.callback_query(F.data == "invite")
async def invite_menu_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    from config import INVITE_EXPORT_SHEET_URL
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Открыть таблицу инвайта", url=INVITE_EXPORT_SHEET_URL))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="Инвайт чужих пользователей (не подписчики бота):", reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text="Инвайт чужих пользователей (не подписчики бота):", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "invite_200")
async def invite_200_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message.content_type == types.ContentType.PHOTO:
        await callback.message.edit_caption(caption="Начинаю инвайт первых 200 пользователей...")
    else:
        await callback.message.edit_text(text="Начинаю инвайт первых 200 пользователей...")
    import gspread
    from config import PARSING_USERS_GOOGLE_SHEET_URL
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL)
    worksheet = sh.sheet1
    users = worksheet.get_all_records()
    count = 0
    errors = 0
    showcase_photo_url = "https://autonet.bug.hr/img/tko-kupi-овай-бугатти-на-поклон-добива--rolls-ройс_NByTb_.jpg"
    from config import INVITE_EXPORT_SHEET_URL
    dst_gc = gspread.service_account(filename=CREDENTIALS_FILE)
    dst_sh = dst_gc.open_by_url(INVITE_EXPORT_SHEET_URL)
    dst_ws = dst_sh.sheet1
    invite_headers = [
        "User ID", "Имя:", "Фото:", "Истории:", "Пол:", "Номер телефона", "Дата парсинга", "ТГ ресурс для парсинга", "Дата рассылки / результат", "Дата подписки в ТГ канал / результат", "Дата инвайта в ТГ бот / результат", "Примечание"
    ]
    if not dst_ws.get_all_values():
        dst_ws.append_row(invite_headers)
    for user in users[:200]:
        user_id = user.get("ID")
        full_name = user.get("Имя") or user.get("Full Name") or "друг"
        text = f"Здравствуйте, {full_name}!\n" \
               "Это сообщение - ваше персональное приглашение в чат-бот Телеграм группы https://t.me/+-f-UEXHQlLRmOGMy и канала Авто и Авиа | Внедорожники https://t.me/+7c-jajcT1RdkNDAy.\n" \
               "Кроме передачи новостной тематической информации, авто-сообщество создается и служит для:\n" \
               "* опроса наиболее важных проблем, учета и выполнения заявок подписчиков-автовладельцев в магазине чат-бота, \n" \
               "* ежемесячного поощрения активности каждого подписчика, партнера, инвестора ценными бонусами-монетами, \n" \
               "* сотрудничества подписчиков, партнеров и инвесторов сообщества для конвертации-продажи своих накопленных бонусов-монет, \n" \
               "* поддержки создания и развития региональных ИП, ООО, потребительских кооперативов и фондов участников,\n" \
               "* совместного роста капиталов участников с целью приобретения своей качественной техники, обеспечения автосервиса и безопасности. \n" \
               "Если авто-, социальных, финансовых и иных проблем у вас нет и не будет, тогда пожалуйста просто проигнорируйте это сообщение."
        result = "OK"
        try:
            await bot.send_photo(user_id, showcase_photo_url, caption=text)
            count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            errors += 1
            result = f"Ошибка: {e}"
        invite_row = [
            user.get("ID", ""),
            user.get("Имя", ""),
            user.get("Фото", ""),
            user.get("Истории", ""),
            user.get("Пол", ""),
            user.get("Номер телефона", ""),
            user.get("Дата парсинга", ""),
            user.get("ТГ ресурс для парсинга", ""),
            str(datetime.now().date()) + " / " + result,
            "",  # Дата подписки в ТГ канал / результат
            "",  # Дата инвайта в ТГ бот / результат
            ""   # Примечание
        ]
        dst_ws.append_row(invite_row)
    await callback.message.answer(f"Инвайт завершён. Успешно отправлено: {count}, ошибок: {errors}.")

@dp.message(StateFilter("waiting_for_invite_confirm"), Command("go"))
async def invite_go(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Инвайт завершён.")

@dp.message(StateFilter("waiting_for_invite_confirm"), Command("cancel"))
async def invite_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Инвайт отменён.")

async def export_column_to_sheet(source_url, dest_url, column_index, header, run_time):
    import gspread
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    src = gc.open_by_url(source_url).sheet1
    dst = gc.open_by_url(dest_url).sheet1
    data = src.get_all_values()
    if not data or len(data[0]) <= column_index:
        return False
    export_data = [[header]] + [[row[column_index]] for row in data[1:] if row[column_index]]
    dst.clear()
    dst.update('A1', export_data)
    return True

async def export_users_by_column_with_flag(source_url, dest_url, column_index):
    import gspread
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    src = gc.open_by_url(source_url).sheet1
    dst = gc.open_by_url(dest_url).sheet1
    data = src.get_all_values()
    if not data or len(data[0]) <= column_index:
        return False
    headers = data[0]
    export_headers = headers[:9] + [headers[column_index]]
    filtered_rows = [row[:9] + [row[column_index]] for row in data[1:] if len(row) > column_index and row[column_index]]
    dst.clear()
    if filtered_rows:
        dst.update(values=[export_headers] + filtered_rows, range_name='A1')
    else:
        dst.update(values=[export_headers], range_name='A1')
    return True

async def scheduled_exports():
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        await export_users_by_column_with_flag(PARSING_USERS_GOOGLE_SHEET_URL, PARTNERS_SHEET_URL, 13)
        await export_users_by_column_with_flag(PARSING_USERS_GOOGLE_SHEET_URL, INVESTORS_SHEET_URL, 14)



async def scheduled_merge():
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        next_run = now.replace(hour=17, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

@dp.callback_query(F.data == "partners_sheet")
async def partners_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Открыть Google Таблицу Партнеры",
        url=PARTNERS_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    await callback.message.edit_text(
        text="Таблица партнеров:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "investors_sheet")
async def investors_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Открыть Google Таблицу Инвесторы",
        url=INVESTORS_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    await callback.message.edit_text(
        text="Таблица инвесторов:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()



@dp.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    
    from config import STATISTICS_SHEET_URL, CUMULATIVE_STATS_SHEET_URL
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📊 Текущая статистика", url=STATISTICS_SHEET_URL))
    builder.add(types.InlineKeyboardButton(text="📈 Накопительная статистика", url=CUMULATIVE_STATS_SHEET_URL))
    builder.add(types.InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="update_stats"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(
        text="📊 **Статистика согласно ТЗ №2 п.4-5**\n\n"
             "• Текущая статистика участников и заказов\n"
             "• Накопительная статистика за периоды\n"
             "• Автоматическое обновление в 17:00 МСК",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "update_stats")
async def update_stats_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    
    await callback.message.edit_text("🔄 Обновляю статистику...")
    
    try:
        from statistics_system import export_statistics_to_sheets, export_cumulative_statistics_to_sheets
        
        success1 = await export_statistics_to_sheets()
        success2 = await export_cumulative_statistics_to_sheets()
        
        if success1 and success2:
            text = "✅ **Статистика обновлена!**\n\nВсе данные успешно выгружены в Google Sheets."
        else:
            text = "⚠️ **Частичная ошибка**\n\nНе все данные удалось обновить. Проверьте логи."
    except Exception as e:
        text = f"❌ **Ошибка!**\n\n{str(e)}"
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="stats"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "plans_reports")
async def plans_reports_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    
    try:
        from plans_reports import show_plans_reports_menu
        await show_plans_reports_menu(callback)
    except ImportError:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
        await callback.message.edit_text(
            text="📊 **Планы и отчеты**\n\nМодуль планов и отчетов не найден.",
            reply_markup=builder.as_markup()
        )
    await callback.answer()

@dp.callback_query(F.data == "invite_export")
async def invite_export_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    await callback.message.edit_text("Начинаю экспорт данных для инвайта...")
    import gspread
    from config import PARSING_USERS_GOOGLE_SHEET_URL, INVITE_EXPORT_SHEET_URL, CREDENTIALS_FILE
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    src = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL).sheet1
    dst = gc.open_by_url(INVITE_EXPORT_SHEET_URL).sheet1
    data = src.get_all_records()
    if not data:
        await callback.message.answer("Нет данных для экспорта.")
        return
    headers = [
        "Username", "User ID", "Имя", "Фото", "Истории", "Пол", "Номер телефона", "Дата рассылки / результат", "Дата подписки в ТГ канал / результат", "Дата инвайта в ТГ бот / результат", "Примечание"
    ]
    export_rows = []
    for row in data:
        export_rows.append([
            row.get("Username", ""),
            row.get("ID", ""),
            row.get("Имя", ""),
            row.get("Фото", ""),
            row.get("Истории", ""),
            row.get("Пол", ""),
            row.get("Номер телефона", ""),
            row.get("Дата рассылки / результат", ""),
            row.get("Дата подписки в ТГ канал / результат", ""),
            row.get("Дата инвайта в ТГ бот / результат", ""),
            row.get("Примечание", "")
        ])
    dst.clear()
    dst.update([headers] + export_rows)
    await callback.message.answer(f"Экспорт завершён. Данные выгружены в Google-таблицу: {INVITE_EXPORT_SHEET_URL}")

async def scheduled_invite_export():
    import pytz
    from datetime import datetime, timedelta
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        try:
            import gspread
            from config import PARSING_USERS_GOOGLE_SHEET_URL, INVITE_EXPORT_SHEET_URL, CREDENTIALS_FILE
            gc = gspread.service_account(filename=CREDENTIALS_FILE)
            src = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL).sheet1
            dst = gc.open_by_url(INVITE_EXPORT_SHEET_URL).sheet1
            data = src.get_all_records()
            if not data:
                continue
            headers = [
                "User ID", "Имя:", "Фото:", "Истории:", "Пол:", "Номер телефона:", "Дата парсинга", "ТГ ресурс для парсинга", "Дата рассылки / результат", "Дата подписки в ТГ канал / результат", "Дата инвайта в ТГ бот / результат", "Примечание"
            ]
            export_rows = []
            for row in data:
                export_rows.append([
                    row.get("ID", ""),
                    row.get("Имя", ""),
                    row.get("Фото", ""),
                    row.get("Истории", ""),
                    row.get("Пол", ""),
                    row.get("Номер телефона", ""),
                    row.get("Дата парсинга", ""),
                    row.get("ТГ ресурс для парсинга", ""),
                    row.get("Дата рассылки / результат", ""),
                    row.get("Дата подписки в ТГ канал / результат", ""),
                    row.get("Дата инвайта в ТГ бот / результат", ""),
                    row.get("Примечание", "")
                ])
            dst = gc.open_by_url(COMMON_EXPORT_SHEET_URL).sheet1
            dst.clear()
            dst.update([headers] + export_rows)
        except Exception as e:
            print(f"Ошибка при ежедневной выгрузке для инвайта: {e}")

async def scheduled_common_exports():
    import pytz
    from datetime import datetime, timedelta
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        next_9 = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= next_9:
            next_9 += timedelta(days=1)
        await asyncio.sleep((next_9 - now).total_seconds())
        try:
            import gspread
            from config import PARSING_USERS_GOOGLE_SHEET_URL, INVITE_EXPORT_SHEET_URL, COMMON_EXPORT_SHEET_URL, CREDENTIALS_FILE
            gc = gspread.service_account(filename=CREDENTIALS_FILE)
            parsing_data = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL).sheet1.get_all_records()
            mailing_data = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL).sheet1.get_all_records()
            all_data = parsing_data + mailing_data
            headers = [
                "User ID", "Имя:", "Фото:", "Истории:", "Пол:", "Номер телефона:", "Дата парсинга", "ТГ ресурс для парсинга", "Дата рассылки / результат", "Дата подписки в ТГ канал / результат", "Дата инвайта в ТГ бот / результат", "Примечание"
            ]
            export_rows = []
            for row in all_data:
                export_rows.append([
                    row.get("ID", ""),
                    row.get("Имя", ""),
                    row.get("Фото", ""),
                    row.get("Истории", ""),
                    row.get("Пол", ""),
                    row.get("Номер телефона", ""),
                    row.get("Дата парсинга", ""),
                    row.get("ТГ ресурс для парсинга", ""),
                    row.get("Дата рассылки / результат", ""),
                    row.get("Дата подписки в ТГ канал / результат", ""),
                    row.get("Дата инвайта в ТГ бот / результат", ""),
                    row.get("Примечание", "")
                ])
            dst = gc.open_by_url(COMMON_EXPORT_SHEET_URL).sheet1
            dst.clear()
            dst.update([headers] + export_rows)
        except Exception as e:
            print(f"Ошибка при выгрузке в общую таблицу: {e}")
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        next_17 = now.replace(hour=17, minute=0, second=0, microsecond=0)
        if now >= next_17:
            next_17 += timedelta(days=1)
        await asyncio.sleep((next_17 - now).total_seconds())
        print("Выгрузка в основную таблицу подписчиков отключена по требованию заказчика")

async def update_invite_table_with_channel_subs():
    import gspread
    from config import INVITE_EXPORT_SHEET_URL, CHANNEL_ID, CREDENTIALS_FILE, TELETHON_API_ID, TELETHON_API_HASH, TELETHON_PHONE_NUMBER
    from datetime import datetime
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        ws = gc.open_by_url(INVITE_EXPORT_SHEET_URL).sheet1
    except Exception as e:
        print(f"Error accessing Google Sheets: {e}")
        return
    all_rows = ws.get_all_values()
    if not all_rows or len(all_rows) < 2:
        return
    headers = all_rows[0]
    user_id_idx = headers.index("Telegram ID")
    sub_col_idx = headers.index("Дата подписки в ТГ канал / результат")
    # Проверяем наличие нужного столбца, иначе ищем похожий
    if "Дата подписки в ТГ канал / результат" in headers:
        sub_col_idx = headers.index("Дата подписки в ТГ канал / результат")
    else:
        # Попробуем найти столбец с похожим названием
        for idx, h in enumerate(headers):
            if "подписк" in h and "канал" in h:
                sub_col_idx = idx
                break
        else:
            sub_col_idx = None  
    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.functions.channels import GetParticipantsRequest
    from telethon.tl.types import ChannelParticipantsSearch
    from telethon import TelegramClient as AsyncTelegramClient
    async with AsyncTelegramClient('check_subs', TELETHON_API_ID, TELETHON_API_HASH) as client:
        await client.start(phone=TELETHON_PHONE_NUMBER)
        participants = await client.get_participants(CHANNEL_ID)
        participant_ids = set(str(p.id) for p in participants)
    for i, row in enumerate(all_rows[1:], start=2):
        user_id = row[user_id_idx]
        if user_id and not row[sub_col_idx] and user_id in participant_ids:
            ws.update_cell(i, sub_col_idx + 1, str(datetime.now().date()) + " / OK")

async def update_invite_table_with_bot_joins(user_id):
    import gspread
    from config import INVITE_EXPORT_SHEET_URL, CREDENTIALS_FILE
    from datetime import datetime
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        ws = gc.open_by_url(INVITE_EXPORT_SHEET_URL).sheet1
    except Exception as e:
        print(f"Error accessing Google Sheets for user {user_id}: {e}")
        return
    all_rows = ws.get_all_values()
    if not all_rows or len(all_rows) < 2:
        return
    headers = all_rows[0]
    # Поиск индекса user_id
    user_id_idx = None
    for idx, h in enumerate(headers):
        if h.strip().lower() in ["user id", "telegram id", "id"]:
            user_id_idx = idx
            break
    if user_id_idx is None:
        # Если не найдено — логируем и выходим
        print("[ERROR] Не найден столбец User ID/Telegram ID/ID в Google Sheet!")
        return
    sub_col_idx = None
    for idx, h in enumerate(headers):
        if "подписк" in h.lower() and "канал" in h.lower():
            sub_col_idx = idx
            break
    if sub_col_idx is None:
        print("[ERROR] Не найден столбец 'Дата подписки в ТГ канал / результат' в Google Sheet!")
        return
    for i, row in enumerate(all_rows[1:], start=2):
        if row[user_id_idx] == str(user_id) and not row[sub_col_idx]:
            ws.update_cell(i, sub_col_idx + 1, str(datetime.now().date()) + " / OK")
            break

@dp.callback_query(F.data == "mailing_addresses")
async def mailing_addresses_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Доступ запрещен.", show_alert=True)
        return
    from config import MAILING_ADDRESSES_SHEET_URL
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Открыть лист 10 адресатов рассылки",
        url=MAILING_ADDRESSES_SHEET_URL
    ))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin"))
    builder.adjust(1)
    await callback.message.edit_text(
        text="Лист с последними 10 адресатами рассылки:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def scheduled_common_export():
    import gspread
    import pytz
    from datetime import datetime, timedelta
    from config import MAILING_ADDRESSES_SHEET_URL, PARSING_USERS_GOOGLE_SHEET_URL, COMMON_EXPORT_SHEET_URL, CREDENTIALS_FILE
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        try:
            gc = gspread.service_account(filename=CREDENTIALS_FILE)
            mailing_ws = gc.open_by_url(MAILING_ADDRESSES_SHEET_URL).sheet1
            parsing_ws = gc.open_by_url(PARSING_USERS_GOOGLE_SHEET_URL).sheet1
            common_ws = gc.open_by_url(COMMON_EXPORT_SHEET_URL).sheet1
            mailing_data = mailing_ws.get_all_values()
            parsing_data = parsing_ws.get_all_values()
            headers = mailing_data[0] if mailing_data else (parsing_data[0] if parsing_data else [])
            all_rows = []
            if mailing_data:
                all_rows += mailing_data[1:]
            if parsing_data:
                all_rows += parsing_data[1:]
            common_ws.clear()
            if headers:
                common_ws.update([headers] + all_rows)
        except Exception as e:
            print(f"Ошибка при ежедневной выгрузке в общую таблицу: {e}")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """
    Команда /admin для входа в админ-панель.
    Доступна только администратору.
    """
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return

    await show_admin_panel(message)
