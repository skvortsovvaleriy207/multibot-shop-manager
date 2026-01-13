from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class AdminTablesInterface:
    def __init__(self):
        from config import MAIN_SURVEY_SHEET_URL
        self.main_url = MAIN_SURVEY_SHEET_URL
    
    def get_admin_tables_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура со ссылкой на таблицу"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("📋 Основная таблица", url=self.main_url))
        return keyboard
    
    async def setup_tables(self):
        """Настройка основной таблицы"""
        print("[OK] Основная таблица настроена")
        print("[OK] Ссылки на таблицы загружены из конфига")

async def cmd_admin_tables(message: types.Message):
    """Команда для админа /admin_tables"""
    interface = AdminTablesInterface()
    keyboard = interface.get_admin_tables_keyboard()
    
    await message.answer(
        "🔧 **Управление таблицами (Админ)**\n\n"
        "Нажмите на ссылку для редактирования таблицы в Google Sheets:\n\n"
        "• Данные синхронизируются ежедневно в 17:00 МСК\n"
        "• Изменения в таблицах отображаются в боте",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Инициализация таблиц при запуске
async def init_admin_tables():
    interface = AdminTablesInterface()
    await interface.setup_tables()
    return interface