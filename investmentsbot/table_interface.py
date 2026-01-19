from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from table_manager import TableManager
import json

class TableInterface:
    """Интерфейс для работы с таблицами через Telegram бота"""
    
    def __init__(self):
        self.tm = TableManager()
    
    def get_tables_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура со списком таблиц"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        tables = self.tm.get_table_list()
        
        for table in tables:
            keyboard.add(InlineKeyboardButton(
                text=self.get_table_display_name(table),
                callback_data=f"table_view_{table}"
            ))
        
        keyboard.add(InlineKeyboardButton("📊 Создать новую таблицу", callback_data="create_table"))
        return keyboard
    
    def get_table_display_name(self, table_name: str) -> str:
        """Получение читаемого названия таблицы"""
        names = {
            "products": "📦 Товары",
            "auto_tech_partners": "🔧 Партнеры по автотехнике", 
            "auto_service_partners": "🚗 Партнеры по автоуслугам",
            "investors": "💰 Инвесторы",
            "statistics": "📈 Статистика",
            "subscriber_offers": "💡 Предложения подписчиков",
            "referral_system": "👥 Реферальная система"
        }
        return names.get(table_name, table_name)
    
    def get_table_actions_keyboard(self, table_name: str) -> InlineKeyboardMarkup:
        """Клавиатура с действиями для таблицы"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📋 Просмотр", callback_data=f"table_show_{table_name}"),
            InlineKeyboardButton("➕ Добавить", callback_data=f"table_add_{table_name}")
        )
        keyboard.add(
            InlineKeyboardButton("🔍 Поиск", callback_data=f"table_search_{table_name}"),
            InlineKeyboardButton("📊 Статистика", callback_data=f"table_stats_{table_name}")
        )
        keyboard.add(
            InlineKeyboardButton("⬅️ Назад к таблицам", callback_data="tables_list")
        )
        
        return keyboard
    
    def format_table_data(self, table_name: str, limit: int = 10) -> str:
        """Форматирование данных таблицы для отображения"""
        data = self.tm.get_table_data(table_name)
        
        if not data:
            return f"📋 Таблица '{self.get_table_display_name(table_name)}' пуста"
        
        # Заголовок
        result = f"📋 **{self.get_table_display_name(table_name)}**\n"
        result += f"Всего записей: {len(data)}\n\n"
        
        # Показываем первые записи
        for i, row in enumerate(data[:limit]):
            result += f"**Запись #{row.get('id', i+1)}:**\n"
            
            # Исключаем служебные поля
            display_data = {k: v for k, v in row.items() if k != 'id'}
            
            for key, value in display_data.items():
                if value:  # Показываем только непустые поля
                    result += f"• {key}: {value}\n"
            result += "\n"
        
        if len(data) > limit:
            result += f"... и еще {len(data) - limit} записей\n"
        
        return result
    
    def get_table_stats(self, table_name: str) -> str:
        """Получение статистики по таблице"""
        data = self.tm.get_table_data(table_name)
        
        if not data:
            return f"📊 Статистика таблицы '{self.get_table_display_name(table_name)}': нет данных"
        
        stats = f"📊 **Статистика: {self.get_table_display_name(table_name)}**\n\n"
        stats += f"📈 Общее количество записей: {len(data)}\n"
        
        # Анализируем поля
        if data:
            sample_row = data[0]
            stats += f"📋 Количество полей: {len(sample_row) - 1}\n"  # -1 для id
            
            # Подсчитываем заполненность полей
            field_stats = {}
            for row in data:
                for key, value in row.items():
                    if key != 'id':
                        if key not in field_stats:
                            field_stats[key] = 0
                        if value and str(value).strip():
                            field_stats[key] += 1
            
            stats += "\n**Заполненность полей:**\n"
            for field, count in field_stats.items():
                percentage = (count / len(data)) * 100
                stats += f"• {field}: {count}/{len(data)} ({percentage:.1f}%)\n"
        
        return stats
    
    def search_in_table(self, table_name: str, search_query: str) -> str:
        """Поиск в таблице"""
        all_data = self.tm.get_table_data(table_name)
        
        if not all_data:
            return f"🔍 Таблица '{self.get_table_display_name(table_name)}' пуста"
        
        # Поиск по всем полям
        results = []
        for row in all_data:
            for key, value in row.items():
                if value and search_query.lower() in str(value).lower():
                    results.append(row)
                    break
        
        if not results:
            return f"🔍 По запросу '{search_query}' ничего не найдено"
        
        result_text = f"🔍 **Результаты поиска по '{search_query}'**\n"
        result_text += f"Найдено записей: {len(results)}\n\n"
        
        for i, row in enumerate(results[:5]):  # Показываем первые 5
            result_text += f"**Запись #{row.get('id', i+1)}:**\n"
            display_data = {k: v for k, v in row.items() if k != 'id' and v}
            
            for key, value in display_data.items():
                result_text += f"• {key}: {value}\n"
            result_text += "\n"
        
        if len(results) > 5:
            result_text += f"... и еще {len(results) - 5} записей\n"
        
        return result_text
    
    def get_add_form_fields(self, table_name: str) -> list:
        """Получение полей для формы добавления записи"""
        forms = {
            "products": [
                ("name", "Название товара"),
                ("category", "Категория"),
                ("price", "Цена"),
                ("description", "Описание"),
                ("seller_id", "ID продавца")
            ],
            "auto_tech_partners": [
                ("company_name", "Название компании"),
                ("contact_person", "Контактное лицо"),
                ("phone", "Телефон"),
                ("email", "Email"),
                ("specialization", "Специализация")
            ],
            "auto_service_partners": [
                ("service_name", "Название сервиса"),
                ("contact_person", "Контактное лицо"),
                ("phone", "Телефон"),
                ("services_offered", "Предлагаемые услуги"),
                ("location", "Местоположение")
            ],
            "investors": [
                ("investor_name", "Имя инвестора"),
                ("contact_info", "Контактная информация"),
                ("investment_amount", "Сумма инвестиций"),
                ("notes", "Примечания")
            ]
        }
        
        return forms.get(table_name, [("field", "Поле")])

# Пример использования
if __name__ == "__main__":
    interface = TableInterface()
    print("Интерфейс таблиц создан!")
    print("Доступные таблицы:", interface.tm.get_table_list())