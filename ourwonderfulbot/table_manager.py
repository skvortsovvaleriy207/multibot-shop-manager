import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

class TableManager:
    """Менеджер таблиц - аналог Excel без файлов Excel"""
    
    def __init__(self, db_path: str = "tables.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных для хранения таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для метаданных таблиц
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_metadata (
                table_name TEXT PRIMARY KEY,
                columns TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_table(self, table_name: str, columns: List[str], data: List[Dict] = None):
        """Создание новой таблицы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем SQL для создания таблицы
        columns_sql = ", ".join([f"{col} TEXT" for col in columns])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" (id INTEGER PRIMARY KEY, {columns_sql})')
        
        # Сохраняем метаданные
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO table_metadata (table_name, columns, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (table_name, json.dumps(columns), now, now))
        
        # Добавляем данные если есть
        if data:
            self.add_rows(table_name, data)
        
        conn.commit()
        conn.close()
    
    def add_row(self, table_name: str, row_data: Dict):
        """Добавление одной строки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        columns = list(row_data.keys())
        values = list(row_data.values())
        placeholders = ", ".join(["?" for _ in values])
        columns_str = ", ".join([f'"{col}"' for col in columns])
        
        cursor.execute(f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})', values)
        
        # Обновляем время изменения
        cursor.execute('UPDATE table_metadata SET updated_at = ? WHERE table_name = ?', 
                      (datetime.now().isoformat(), table_name))
        
        conn.commit()
        conn.close()
    
    def add_rows(self, table_name: str, rows_data: List[Dict]):
        """Добавление нескольких строк"""
        for row in rows_data:
            self.add_row(table_name, row)
    
    def get_table_data(self, table_name: str) -> List[Dict]:
        """Получение всех данных таблицы"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    
    def update_row(self, table_name: str, row_id: int, updates: Dict):
        """Обновление строки по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f'"{col}" = ?' for col in updates.keys()])
        values = list(updates.values()) + [row_id]
        
        cursor.execute(f'UPDATE "{table_name}" SET {set_clause} WHERE id = ?', values)
        cursor.execute('UPDATE table_metadata SET updated_at = ? WHERE table_name = ?', 
                      (datetime.now().isoformat(), table_name))
        
        conn.commit()
        conn.close()
    
    def delete_row(self, table_name: str, row_id: int):
        """Удаление строки по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'DELETE FROM "{table_name}" WHERE id = ?', (row_id,))
        cursor.execute('UPDATE table_metadata SET updated_at = ? WHERE table_name = ?', 
                      (datetime.now().isoformat(), table_name))
        
        conn.commit()
        conn.close()
    
    def search_rows(self, table_name: str, search_column: str, search_value: str) -> List[Dict]:
        """Поиск строк по значению в колонке"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM "{table_name}" WHERE "{search_column}" LIKE ?', (f'%{search_value}%',))
        rows = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    
    def get_table_list(self) -> List[str]:
        """Получение списка всех таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT table_name FROM table_metadata')
        tables = cursor.fetchall()
        
        conn.close()
        return [table[0] for table in tables]
    
    def export_to_dict(self, table_name: str) -> Dict:
        """Экспорт таблицы в словарь (аналог Excel листа)"""
        data = self.get_table_data(table_name)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT columns FROM table_metadata WHERE table_name = ?', (table_name,))
        columns = json.loads(cursor.fetchone()[0])
        conn.close()
        
        return {
            'table_name': table_name,
            'columns': columns,
            'data': data,
            'row_count': len(data)
        }

# Создание предустановленных таблиц для автомагазина
def create_automarket_tables():
    """Создание основных таблиц для автомагазина"""
    tm = TableManager()
    
    # Основная таблица товаров
    tm.create_table("products", [
        "name", "category", "price", "description", "seller_id", 
        "status", "created_at", "views", "rating"
    ])
    
    # Таблица партнеров по автотехнике
    tm.create_table("auto_tech_partners", [
        "company_name", "contact_person", "phone", "email", 
        "specialization", "region", "rating", "status"
    ])
    
    # Таблица партнеров по автоуслугам
    tm.create_table("auto_service_partners", [
        "service_name", "contact_person", "phone", "email",
        "services_offered", "location", "rating", "status"
    ])
    
    # Таблица инвесторов
    tm.create_table("investors", [
        "investor_name", "contact_info", "investment_amount",
        "investment_date", "status", "notes"
    ])
    
    # Таблица статистики
    tm.create_table("statistics", [
        "date", "users_count", "orders_count", "revenue",
        "new_registrations", "active_sellers"
    ])
    
    # Таблица предложений подписчиков
    tm.create_table("subscriber_offers", [
        "user_id", "offer_text", "category", "status",
        "created_at", "admin_response"
    ])
    
    # Таблица реферальной системы
    tm.create_table("referral_system", [
        "referrer_id", "referred_id", "referral_date",
        "bonus_amount", "status", "level"
    ])
    
    return tm

if __name__ == "__main__":
    # Пример использования
    tm = create_automarket_tables()
    
    # Добавляем тестовые данные
    tm.add_row("products", {
        "name": "Масло моторное 5W-30",
        "category": "Автохимия",
        "price": "1500",
        "description": "Синтетическое моторное масло",
        "seller_id": "1",
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "views": "0",
        "rating": "5.0"
    })
    
    print("Таблицы созданы успешно!")
    print("Доступные таблицы:", tm.get_table_list())