from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from table_interface import TableInterface
from datetime import datetime

class TableStates(StatesGroup):
    waiting_search_query = State()
    waiting_add_data = State()

class TableHandlers:
    """Обработчики для работы с таблицами"""
    
    def __init__(self, dp):
        self.dp = dp
        self.interface = TableInterface()
        self.register_handlers()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        # Команда для открытия таблиц
        self.dp.register_message_handler(
            self.cmd_tables, 
            commands=['tables'], 
            state='*'
        )
        
        # Обработчики callback'ов
        self.dp.register_callback_query_handler(
            self.process_tables_callback,
            lambda c: c.data.startswith(('table_', 'tables_', 'create_table')),
            state='*'
        )
        
        # Обработчик поиска
        self.dp.register_message_handler(
            self.process_search_query,
            state=TableStates.waiting_search_query
        )
        
        # Обработчик добавления данных
        self.dp.register_message_handler(
            self.process_add_data,
            state=TableStates.waiting_add_data
        )
    
    async def cmd_tables(self, message: types.Message):
        """Команда /tables - показать список таблиц"""
        keyboard = self.interface.get_tables_keyboard()
        await message.answer(
            "📊 **Управление таблицами**\n\n"
            "Выберите таблицу для работы:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def process_tables_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработка callback'ов таблиц"""
        data = callback.data
        
        if data == "tables_list":
            # Возврат к списку таблиц
            keyboard = self.interface.get_tables_keyboard()
            await callback.message.edit_text(
                "📊 **Управление таблицами**\n\n"
                "Выберите таблицу для работы:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data.startswith("table_view_"):
            # Просмотр таблицы
            table_name = data.replace("table_view_", "")
            keyboard = self.interface.get_table_actions_keyboard(table_name)
            display_name = self.interface.get_table_display_name(table_name)
            
            await callback.message.edit_text(
                f"📋 **Таблица: {display_name}**\n\n"
                "Выберите действие:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data.startswith("table_show_"):
            # Показать содержимое таблицы
            table_name = data.replace("table_show_", "")
            table_data = self.interface.format_table_data(table_name)
            keyboard = self.interface.get_table_actions_keyboard(table_name)
            
            await callback.message.edit_text(
                table_data,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data.startswith("table_stats_"):
            # Показать статистику таблицы
            table_name = data.replace("table_stats_", "")
            stats = self.interface.get_table_stats(table_name)
            keyboard = self.interface.get_table_actions_keyboard(table_name)
            
            await callback.message.edit_text(
                stats,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data.startswith("table_search_"):
            # Начать поиск в таблице
            table_name = data.replace("table_search_", "")
            await state.update_data(search_table=table_name)
            await TableStates.waiting_search_query.set()
            
            await callback.message.answer(
                f"🔍 **Поиск в таблице: {self.interface.get_table_display_name(table_name)}**\n\n"
                "Введите поисковый запрос:"
            )
        
        elif data.startswith("table_add_"):
            # Добавить запись в таблицу
            table_name = data.replace("table_add_", "")
            fields = self.interface.get_add_form_fields(table_name)
            
            if fields:
                await state.update_data(add_table=table_name, add_fields=fields, add_data={})
                await TableStates.waiting_add_data.set()
                
                field_list = "\n".join([f"• {desc}" for _, desc in fields])
                await callback.message.answer(
                    f"➕ **Добавление записи в: {self.interface.get_table_display_name(table_name)}**\n\n"
                    f"Поля для заполнения:\n{field_list}\n\n"
                    "Отправьте данные в формате:\n"
                    "поле1: значение1\n"
                    "поле2: значение2\n"
                    "..."
                )
        
        await callback.answer()
    
    async def process_search_query(self, message: types.Message, state: FSMContext):
        """Обработка поискового запроса"""
        data = await state.get_data()
        table_name = data.get('search_table')
        
        if not table_name:
            await message.answer("❌ Ошибка: таблица не выбрана")
            await state.finish()
            return
        
        search_query = message.text.strip()
        results = self.interface.search_in_table(table_name, search_query)
        keyboard = self.interface.get_table_actions_keyboard(table_name)
        
        await message.answer(
            results,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        await state.finish()
    
    async def process_add_data(self, message: types.Message, state: FSMContext):
        """Обработка добавления данных"""
        data = await state.get_data()
        table_name = data.get('add_table')
        fields = data.get('add_fields', [])
        
        if not table_name:
            await message.answer("❌ Ошибка: таблица не выбрана")
            await state.finish()
            return
        
        # Парсим данные из сообщения
        lines = message.text.strip().split('\n')
        row_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Ищем соответствующее поле
                for field_key, field_desc in fields:
                    if key in field_desc.lower() or field_key.lower() in key:
                        row_data[field_key] = value
                        break
        
        if not row_data:
            await message.answer(
                "❌ Не удалось распознать данные.\n"
                "Используйте формат:\n"
                "название поля: значение"
            )
            return
        
        # Добавляем служебные поля
        row_data['status'] = 'active'
        row_data['created_at'] = datetime.now().isoformat()
        
        try:
            self.interface.tm.add_row(table_name, row_data)
            
            keyboard = self.interface.get_table_actions_keyboard(table_name)
            await message.answer(
                f"✅ **Запись успешно добавлена в таблицу: {self.interface.get_table_display_name(table_name)}**\n\n"
                f"Добавленные данные:\n" + 
                "\n".join([f"• {k}: {v}" for k, v in row_data.items()]),
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при добавлении записи: {str(e)}")
        
        await state.finish()

# Функция для инициализации таблиц при запуске бота
def init_tables():
    """Инициализация таблиц при запуске"""
    from table_manager import create_automarket_tables
    
    try:
        tm = create_automarket_tables()
        print("✅ Таблицы инициализированы успешно")
        return tm
    except Exception as e:
        print(f"❌ Ошибка инициализации таблиц: {e}")
        return None