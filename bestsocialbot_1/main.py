import asyncio
import logging
from config import BOT_TOKEN, SHOWCASE_INTERVAL, CHANNEL_ID, ADMIN_ID, MAIN_SURVEY_SHEET_URL
from db import init_db
from dispatcher import dp
from aiogram import types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from bot_instance import bot
from captcha import send_captcha, process_captcha_selection, CaptchaStates
from google_sheets import sync_db_to_google_sheets, sync_db_to_main_survey_sheet, sync_with_google_sheets, sync_requests_from_sheets_to_db #, sync_from_sheets_to_db

async def check_blocked_user(callback):
    """Проверка заблокированных пользователей"""
    try:
        user_id = callback.from_user.id
        async with aiosqlite.connect("bot_database.db") as db:
            cursor = await db.execute("SELECT account_status FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            
            if row and row[0] == 'О':
                await callback.answer("Ваш аккаунт заблокирован администратором.", show_alert=True)
                return True
        return False
    except Exception as e:
        print(f"Ошибка при проверке блокировки пользователя: {e}")
        return False

async def get_showcase_keyboard(user_id: int):
    from config import ADMIN_ID
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT account_status FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0] == 'О':
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="📝 Опрос", callback_data="blocked"))
            builder.add(types.InlineKeyboardButton(text="🏪 Магазин", callback_data="blocked"))
            builder.adjust(2)
            return builder.as_markup()
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        user_exists = await cursor.fetchone()
        cursor = await db.execute("SELECT has_completed_survey FROM users WHERE user_id = ?", (user_id,))
        survey_status = await cursor.fetchone()
    builder = InlineKeyboardBuilder()
    if user_exists:
        builder.add(types.InlineKeyboardButton(text="📝 Опрос", callback_data="survey"))
        builder.add(types.InlineKeyboardButton(text="🏪 Магазин", callback_data="shop"))
    else:
        builder.add(types.InlineKeyboardButton(text="📝 Опрос (недоступно)", callback_data="disabled"))
        builder.add(types.InlineKeyboardButton(text="🏪 Магазин (недоступно)", callback_data="disabled"))
    
    builder.adjust(2)
    
    return builder.as_markup()

@dp.message(Command("start_shop"))
async def cmd_start_shop(message: types.Message ):
    """Главная страница магазина (первый экран после входа)"""

    user_id = message.chat.id

    # Sync not imported yet, do it in main flow or inside function
    # await sync_from_sheets_to_db()

    builder = InlineKeyboardBuilder()

    # Основные разделы магазина
    builder.add(types.InlineKeyboardButton(text="📦 Каталоги", callback_data="all_catalogs"))
    builder.add(types.InlineKeyboardButton(text="🏷️ Акции", callback_data="promotions_menu"))
    builder.add(types.InlineKeyboardButton(text="📰 Новости", callback_data="news_menu"))
    builder.add(types.InlineKeyboardButton(text="⭐ Популярное", callback_data="popular_menu"))
    builder.add(types.InlineKeyboardButton(text="🆕 Новинки", callback_data="new_items"))
    builder.add(types.InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_account"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="exit_shop_menu"))
    builder.adjust(2, 2, 2, 1)

    await message.answer(
        "ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН СООБЩЕСТВА!",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, command: CommandObject):
    # Ensure state is cleared when /start is used
    await state.clear() 

    user_id = message.from_user.id
    print(f"DEBUG: /start command received from user_id={user_id}")
    
    param=command.args
    if param=="shop":
        await cmd_start_shop(message)
        return
    # Проверяем реферальную ссылку
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]
        if start_param.startswith('ref_'):
            try:
                referrer_id = int(start_param.replace('ref_', ''))
                print(f"DEBUG: Referral detected from user_id={referrer_id}")
            except ValueError:
                pass
    
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        user_exists = await cursor.fetchone()
        print(f"DEBUG: user_exists query result: {user_exists}")
    
    if not user_exists:
        print("DEBUG: New user detected, sending captcha")
        try:
            from admin import update_invite_table_with_bot_joins
            await update_invite_table_with_bot_joins(user_id)
        except Exception as e:
            logging.error(f"Error updating invite table: {e}")
        
        # Сохраняем реферера для обработки после капчи
        if referrer_id:
            await state.update_data(referrer_id=referrer_id)
        
        await send_captcha(message, state)
    else:
        print("DEBUG: Existing user detected, sending showcase keyboard")
        keyboard = await get_showcase_keyboard(user_id)
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)

from survey import *
from shop import *
# Основные модули
from admin import *
from partner_handlers import router as partner_router
from automarket import *
from add_items import *
from orders import *
from automarket_stats import *
from plans_reports import *
from daily_scheduler import start_daily_scheduler

# Новые системы согласно ТЗ №2
from referral_system import start_referral_system
from activity_system import start_activity_system
from initiatives_system import scheduled_initiatives_sync
from user_interface import *
try:
    from table_links import *
except ImportError as e:
    logging.error(f"Error importing table_links: {e}")
from order_request_system import *
import admin_catalog_manager
import admin_posts  # New module for admin content management
import user_posts   # New module for user content viewing
from admin_order_processing import *
# Категории объединены в category_manager.py

# Основные модули согласно ТЗ
print("[MAIN.PY] Importing catalog module...")
try:
    from catalog import *
    print("[MAIN.PY] Catalog module imported successfully")
except Exception as e:
    print(f"[MAIN.PY] ERROR importing catalog: {e}")
    import traceback
    traceback.print_exc()

from search_system import *
from messages_system import *
# from item_cards import *  # Закомментировано - конфликтует с catalog.py
from category_manager import *
    
try:
    from payment_info import *
except ImportError:
    logging.warning("Модуль payment_info не найден")
    
try:
    from admin_partners import *
except ImportError:
    logging.warning("Модуль admin_partners не найден")
    
try:
    from payment_messages import *
except ImportError:
    logging.warning("Модуль payment_messages не найден")
    
try:
    from search_filters import *
except ImportError:
    logging.warning("Модуль search_filters не найден")
    
# Модули заказов объединены в orders.py
    
try:
    from admin_settings import *
except ImportError:
    logging.warning("Модуль admin_settings не найден")
    
try:
    from admin_tables_interface import cmd_admin_tables, init_admin_tables
except ImportError:
    logging.warning("Модуль admin_tables_interface не найден")
    def cmd_admin_tables(message):
        pass
    async def init_admin_tables():
        pass
        
# excel_template_filler удален
async def fill_tables_from_excel():
    pass

SHOWCASE_TEXT = """
ДОБРО ПОЖАЛОВАТЬ В ЧАТ-БОТ СООБЩЕСТВА!
"""
from filters import IsBadWord, IsBlockedUser


@dp.callback_query(IsBlockedUser())
async def blocked_user_callback_handler(callback: types.CallbackQuery):
    try:
        await callback.answer("Ваш аккаунт отключен администратором.", show_alert=True)
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback заблокированного пользователя: {e}")
    return
@dp.message(IsBlockedUser())
async def blocked_user_message_handler(message: types.Message):
    await message.answer("Ваш аккаунт отключен администратором.")
    return
@dp.message(IsBadWord())
async def handle_bad_words(message: types.Message):
    await message.answer("❌ Использование нецензурной лексики запрещено в нашем сообществе!")
    await message.delete()
    print(f"User {message.from_user.id} used bad words: {message.text}")

from google_sheets import sync_with_google_sheets, sync_requests_from_sheets_to_db

import asyncio
from aiogram import Bot
from datetime import datetime
async def send_user_notification(bot: Bot, user_id: int, changes: dict):
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("""
            SELECT 
                username, full_name, birth_date, location, email, phone, employment,
                financial_problem, social_problem, ecological_problem, passive_subscriber,
                active_partner, investor_trader, business_proposal, bonus_total, current_balance
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        user_data = await cursor.fetchone()
    if not user_data:
        return
    field_names = {
        'username': 'Никнейм',
        'full_name': 'ФИО',
        'birth_date': 'Дата рождения',
        'location': 'Место жительства',
        'email': 'Email',
        'phone': 'Телефон',
        'employment': 'Занятость',
        'financial_problem': 'Финансовая проблема',
        'social_problem': 'Социальная проблема',
        'ecological_problem': 'Экологическая проблема',
        'passive_subscriber': 'Статус пассивного подписчика',
        'active_partner': 'Статус активного партнера',
        'investor_trader': 'Статус инвестора/трейдера',
        'business_proposal': 'Бизнес-предложение',
        'bonus_total': 'Общая сумма бонусов',
        'current_balance': 'Текущий баланс'
    }
    message = "🔔 Ваш профиль был обновлен. Текущие данные:\n\n"
    for i, (field, name) in enumerate(field_names.items()):
        value = user_data[i] if user_data[i] is not None else 'Не указано'
        message += f"▪️ {name}: {value}\n"
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        logging.error(f"Failed to send notification to user {user_id}: {e}")
async def periodic_sync():
    while True:
        try:
            await asyncio.sleep(5)  # Задержка перед синхронизацией
            changes = await sync_with_google_sheets()
            if changes:
                for user_id, user_changes in changes.items():
                    if user_changes:
                        await send_user_notification(bot, user_id, user_changes)
        except Exception as e:
            logging.error(f"Error in periodic sync: {e}")
        await asyncio.sleep(21600)
async def periodic_update_invite_table():
    from admin import update_invite_table_with_channel_subs
    while True:
        try:
            await update_invite_table_with_channel_subs()
        except Exception as e:
            logging.error(f"Error in periodic_update_invite_table: {e}")
        await asyncio.sleep(3600)
async def main():
    from db import init_db
    await init_db()

    # Инициализация реферальной системы
    from referral_system import init_referral_system
    await init_referral_system()

    from search_system import init_search_history_table
    await init_search_history_table()

    # Инициализация новых систем согласно ТЗ №2
    await start_referral_system()
    await start_activity_system()
    
    # Инициализация админских таблиц
    await init_admin_tables()
    
    # Заполнение таблиц из Excel примеров
    await fill_tables_from_excel()
    
    # Список фоновых задач для корректного завершения
    background_tasks = []

    # Запуск ежедневной синхронизации в 17:00 МСК
    background_tasks.append(asyncio.create_task(start_daily_scheduler()))
    

    
    # SYNC: Загружаем изменения из Google Sheets в БД
    print("[SYNC] Загрузка изменений из Google Sheets...")
    try:
        #await sync_requests_from_sheets_to_db()
        print(f"[OK] Загружено изменений для заявок")
        changes = await sync_with_google_sheets()
        if changes:
            print(f"[OK] Загружено изменений для {len(changes)} пользователей")
            for user_id, user_changes in changes.items():
                if user_changes:
                    try:
                        # Отключаем уведомления при старте, чтобы не спамить при перезапусках
                        # await send_user_notification(bot, user_id, user_changes)
                        print(f"[NOTIFY] Обнаружены изменения профиля для {user_id}: {user_changes}")
                    except Exception as notify_error:
                        print(f"[ERROR] Ошибка отправки уведомления {user_id}: {notify_error}")
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки из Google Sheets: {e}")
    
    # Полное управление через Google Sheets
    from admin_sheets_manager import start_admin_sheets_sync, export_admin_data_to_sheets
    from automarket_sheets import export_all_automarket_data
    from partner_sheets import export_all_partner_data
    
    # EXPORT: Выгружаем данные из БД в Google Sheets
    print("[EXPORT] Выгрузка данных из базы в Google Sheets...")
    
    # Проверяем данные в базе
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM auto_products")
        products_count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM auto_services")
        services_count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        orders_count = (await cursor.fetchone())[0]
        print(f"[DB] Данные в базе: товаров={products_count}, услуг={services_count}, заказов={orders_count}")
    
    try:
        # Отключено: не перезаписываем изменения из Google Sheets
        # await sync_db_to_main_survey_sheet()
        await export_all_automarket_data()
        await export_all_partner_data()
        print("[OK] Выгрузка завершена")
    except Exception as e:
        print(f"[ERROR] Ошибка выгрузки: {e}")
        print("[INFO] Проверьте URL таблиц в config.py и доступ к Google Sheets")
    
    await start_admin_sheets_sync()
    
    # Запуск периодических задач
    background_tasks.append(asyncio.create_task(periodic_showcase()))
    background_tasks.append(asyncio.create_task(periodic_sync()))
    
    # Синхронизация автомагазина
    from automarket_sheets import scheduled_automarket_sync
    background_tasks.append(asyncio.create_task(scheduled_automarket_sync()))
    
    # Синхронизация партнерских программ
    from partner_sheets import scheduled_partner_sync
    background_tasks.append(asyncio.create_task(scheduled_partner_sync()))
    
    # Синхронизация статусов заказов (функционал в orders.py)
    
    # ✅ СТАТИСТИКА СОГЛАСНО ТЗ №2 П.4-5
    from statistics_system import scheduled_statistics_export
    background_tasks.append(asyncio.create_task(scheduled_statistics_export()))
    
    # ✅ СИСТЕМА ИНИЦИАТИВ СОГЛАСНО ТЗ №2 П.1
    background_tasks.append(asyncio.create_task(scheduled_initiatives_sync()))
    
    # Запуск polling с retry логикой
    max_retries = 5
    retry_delay = 5
    
    try:
        for attempt in range(max_retries):
            try:
                print(f"Попытка подключения к Telegram API ({attempt + 1}/{max_retries})...")
                await dp.start_polling(bot)
                break
            except Exception as e:
                logging.error(f"Ошибка подключения к Telegram (попытка {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"Повторная попытка через {retry_delay} секунд...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Экспоненциальная задержка
                else:
                    print("Не удалось подключиться к Telegram API. Проверьте интернет-соединение.")
                    raise
    finally:
        print("Остановка бота... Завершение фоновых задач.")
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        print("Фоновые задачи завершены.")




async def send_showcase(chat_id: int):
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT message_id FROM showcase_messages WHERE chat_id = ?", (chat_id,))
        rows = await cursor.fetchall()
        for row in rows:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=row[0])
            except Exception:
                pass
        await db.execute("DELETE FROM showcase_messages WHERE chat_id = ?", (chat_id,))
        await db.commit()
    

    
    # Получаем информацию о боте для формирования динамической ссылки
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    photo_url = "https://i.postimg.cc/d3DLXMwT/social.jpg"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Опрос", url=f"https://t.me/{bot_username}?start=survey"))
    builder.add(types.InlineKeyboardButton(text="Магазин", url=f"https://t.me/{bot_username}?start=shop"))
    builder.adjust(2)
    
    message = await bot.send_photo(
        chat_id=chat_id,
        photo=photo_url,
        caption=SHOWCASE_TEXT,
        reply_markup=builder.as_markup()
    )
    
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("INSERT INTO showcase_messages VALUES (?, ?)", (message.message_id, chat_id))
        await db.commit()
@dp.callback_query(lambda c: c.data == "disabled")
async def disabled_button(callback: types.CallbackQuery):
    await callback.answer("Для доступа к этой функции необходимо пройти опрос.", show_alert=True)
@dp.callback_query(lambda c: c.data == "blocked")
async def blocked_button(callback: types.CallbackQuery):
    await callback.answer("Ваш аккаунт заблокирован администратором.", show_alert=True)

@dp.callback_query(lambda c: c.data == "empty")
async def empty_button(callback: types.CallbackQuery):
    await callback.answer("В данной категории пока нет предложений.", show_alert=True)
@dp.callback_query(F.data == "survey")
async def survey_button_handler(callback: types.CallbackQuery):
    await callback.answer("Вы выбрали Опрос.", show_alert=False)



@dp.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel_handler(callback: types.CallbackQuery):
    # Проверяем права администратора
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Создаем админскую клавиатуру
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📊 Админские таблицы", callback_data="admin_tables"))
    builder.add(types.InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users"))
    builder.add(types.InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats"))
    builder.add(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    builder.adjust(2, 2, 1)
    
    await callback.message.edit_text(
        "🔧 **Панель администратора**\n\nВыберите действие:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        keyboard = await get_showcase_keyboard(user_id)
        await callback.message.edit_text(
            "Добро пожаловать! Выберите действие:",
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в back_to_main_handler: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@dp.callback_query(lambda c: c.data == "admin_tables")
async def admin_tables_handler(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer("Открываю админские таблицы...")
    # Вызываем функцию из admin_tables_interface
    try:
        await cmd_admin_tables(callback.message)
    except Exception as e:
        await callback.message.answer(f"Ошибка при открытии таблиц: {e}")
@dp.message(Command("captcha"))
async def cmd_captcha(message: types.Message, state: FSMContext):
    await send_captcha(message, state)

@dp.message(Command("admin_tables"))
async def admin_tables_command(message: types.Message):
    # Проверка прав админа
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещен")
        return
    await cmd_admin_tables(message)

# Callback обработчики больше не нужны - все через прямые ссылки
@dp.callback_query(F.data.startswith("captcha_"), IsBlockedUser())
async def captcha_callback(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Ваш аккаунт заблокирован администратором. Доступ к кнопкам ограничен.", show_alert=True)
        return
    except Exception as e:
        print(f"Ошибка при ответе на callback заблокированного пользователя: {e}")
        return


@dp.callback_query(F.data.startswith("captcha_"))
async def captcha_callback(callback: CallbackQuery, state: FSMContext):
    try:
        print(f"DEBUG: Получены данные callback: {callback.data}")
        success = await process_captcha_selection(callback, state)
        print(f"DEBUG: process_captcha_selection вернул: {success}")
        data = await state.get_data()
        attempt_count = data.get("captcha_attempt_count", 0)
        if success:
            attempt_count += 1
            print(f"DEBUG: Успешная попытка #{attempt_count}")
            if attempt_count < 3:
                await callback.message.answer("✅ Вы выбрали правильный цвет!")
                await state.update_data(captcha_attempt_count=attempt_count)
                await send_captcha(callback.message, state)
            else:
                await state.clear()
                user_id = callback.from_user.id
                username = callback.from_user.username or ""
                first_name = callback.from_user.first_name or ""
                last_name = callback.from_user.last_name or ""
                try:
                    import aiosqlite
                    async with aiosqlite.connect("bot_database.db") as db:
                        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
                        exists = await cursor.fetchone()
                        if not exists:
                            await db.execute(
                                "INSERT INTO users (user_id, username, first_name, last_name, created_at, account_status) VALUES (?, ?, ?, ?, datetime('now'), ?)",
                                (user_id, username, first_name, last_name, "Р")
                            )
                            await db.commit()
                    # Обрабатываем реферала если есть
                    referrer_id = data.get("referrer_id")
                    if referrer_id:
                        from referral_system import process_referral
                        await process_referral(user_id, referrer_id)

                    # Если пользователь инициировал вход в магазин, сразу открываем ГЛАВНУЮ СТРАНИЦУ МАГАЗИНА
                    if data.get("shop_captcha_pending"):
                        from aiogram.types import CallbackQuery
                        from shop import main_shop_page
                        fake_callback = CallbackQuery(
                            id=callback.id,
                            from_user=callback.from_user,
                            chat_instance=callback.chat_instance,
                            message=callback.message,
                            data="main_shop_page"
                        )
                        # Fix identifying: Mount the fake callback to the bot instance
                        if callback.bot:
                            fake_callback.as_(callback.bot)
                        
                        await main_shop_page(fake_callback)
                    else:
                        # Только теперь формируем клавиатуру
                        keyboard = await get_showcase_keyboard(user_id)
                        
                        try:
                            # Попытка 1: через message.answer (самый стандартный способ)
                            if callback.message:
                                await callback.message.answer("✅ Капча пройдена! Добро пожаловать!", reply_markup=keyboard)
                            else:
                                raise Exception("Message object is missing")
                        except Exception as e1:
                            print(f"Failed to use message.answer: {e1}")
                            # Попытка 2: через callback.bot (гарантированно привязанный бот)
                            if callback.bot:
                                await callback.bot.send_message(
                                    chat_id=user_id,
                                    text="✅ Капча пройдена! Добро пожаловать!",
                                    reply_markup=keyboard
                                )
                            else:
                                print("CRITICAL: callback.bot is None!")
                                # Попытка 3: глобальный бот (крайний случай)
                                from bot_instance import bot as global_bot
                                await global_bot.send_message(user_id, "✅ Капча пройдена! Добро пожаловать!", reply_markup=keyboard)

                    print("SYNC CALL")
                    try:
                        from google_sheets import sync_db_to_google_sheets
                        await sync_db_to_google_sheets()
                    except Exception as sync_e:
                        print(f"⚠️ Warning: Background sync failed: {sync_e}")
                        # Don't fail the user interaction because of background sync
                except Exception as send_msg_error:
                    print(f"Ошибка при отправке сообщения: {send_msg_error}")
                    import traceback
                    traceback.print_exc()
        else:
            await state.update_data(captcha_attempt_count=0)
            await send_captcha(callback.message, state)
        try:
            await callback.answer()
        except Exception as callback_answer_error:
            print(f"Ошибка при ответе на callback: {callback_answer_error}")
    except Exception as e:
        print(f"ОШИБКА в captcha_callback: {e}")
        import traceback
        traceback.print_exc()
        try:
            await callback.answer("Произошла ошибка, попробуйте еще раз")
        except Exception as callback_answer_error:
            print(f"Ошибка при ответе на callback после исключения: {callback_answer_error}")
async def periodic_showcase():
    from aiogram.exceptions import TelegramBadRequest
    while True:
        try:
            logging.info(f"Sending showcase to channel ID: {CHANNEL_ID}")
            await send_showcase(CHANNEL_ID)
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                 logging.error(f"CRITICAL ERROR: Channel {CHANNEL_ID} not found. Please check if the bot is added to the channel and is an admin.")
            else:
                 logging.error(f"Telegram error in periodic_showcase: {e}")
        except Exception as e:
            logging.error(f"Error in periodic_showcase: {e}")
        await asyncio.sleep(SHOWCASE_INTERVAL)
if __name__ == "__main__":
    asyncio.run(main())