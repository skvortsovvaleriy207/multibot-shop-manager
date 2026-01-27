import aiosqlite
import gspread
from datetime import datetime, timedelta
from config import CREDENTIALS_FILE
import asyncio
import logging
from db import DB_FILE

# Максимальные бонусы за активность согласно ТЗ
MAX_DAILY_ACTIVITY_BONUS = 0.06
MAX_MONTHLY_ACTIVITY_BONUS = 1.0

# Типы активности
ACTIVITY_TYPES = {
    'orders': 'Заявки/заказы',
    'auctions': 'Аукционы партнеров', 
    'contests': 'Конкурсы',
    'surveys': 'Информационные опросы',
    'content_views': 'Просмотры контента',
    'comments': 'Комментарии и реакции'
}

async def init_activity_system():
    """Инициализация системы активности"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Таблица активности пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_date TEXT,
                points REAL DEFAULT 0,
                auto_detected BOOLEAN DEFAULT TRUE,
                user_reported BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица учета активности пользователем
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_date TEXT,
                orders_plus INTEGER DEFAULT 0,
                orders_minus INTEGER DEFAULT 0,
                auctions_plus INTEGER DEFAULT 0,
                auctions_minus INTEGER DEFAULT 0,
                contests_plus INTEGER DEFAULT 0,
                contests_minus INTEGER DEFAULT 0,
                surveys_plus INTEGER DEFAULT 0,
                surveys_minus INTEGER DEFAULT 0,
                content_plus INTEGER DEFAULT 0,
                content_minus INTEGER DEFAULT 0,
                comments_plus INTEGER DEFAULT 0,
                comments_minus INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Добавляем поля активности в users
        try:
            await db.execute("ALTER TABLE users ADD COLUMN daily_activity_points REAL DEFAULT 0")
            await db.execute("ALTER TABLE users ADD COLUMN monthly_activity_points REAL DEFAULT 0")
            await db.execute("ALTER TABLE users ADD COLUMN current_activity TEXT DEFAULT ''")
        except:
            pass
        
        await db.commit()

async def track_activity(user_id: int, activity_type: str, points: float = 0.01):
    """Отслеживание активности пользователя"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # Проверяем дневной лимит
            today = datetime.now().date().isoformat()
            cursor = await db.execute("""
                SELECT SUM(points) FROM user_activity 
                WHERE user_id = ? AND activity_date = ?
            """, (user_id, today))
            
            daily_total = (await cursor.fetchone())[0] or 0
            
            if daily_total >= MAX_DAILY_ACTIVITY_BONUS:
                return False
            
            # Добавляем активность
            await db.execute("""
                INSERT INTO user_activity (user_id, activity_type, activity_date, points)
                VALUES (?, ?, ?, ?)
            """, (user_id, activity_type, today, min(points, MAX_DAILY_ACTIVITY_BONUS - daily_total)))
            
            # Обновляем дневные очки
            await db.execute("""
                UPDATE users SET daily_activity_points = daily_activity_points + ?
                WHERE user_id = ?
            """, (points, user_id))
            
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"Error tracking activity: {e}")
        return False

async def save_user_activity_report(user_id: int, report_data: dict):
    """Сохранение отчета пользователя о своей активности"""
    try:
        today = datetime.now().date().isoformat()
        
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_activity_reports 
                (user_id, report_date, orders_plus, orders_minus, auctions_plus, auctions_minus,
                 contests_plus, contests_minus, surveys_plus, surveys_minus, 
                 content_plus, content_minus, comments_plus, comments_minus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, today,
                report_data.get('orders_plus', 0), report_data.get('orders_minus', 0),
                report_data.get('auctions_plus', 0), report_data.get('auctions_minus', 0),
                report_data.get('contests_plus', 0), report_data.get('contests_minus', 0),
                report_data.get('surveys_plus', 0), report_data.get('surveys_minus', 0),
                report_data.get('content_plus', 0), report_data.get('content_minus', 0),
                report_data.get('comments_plus', 0), report_data.get('comments_minus', 0)
            ))
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"Error saving activity report: {e}")
        return False

async def calculate_activity_score(user_id: int):
    """Расчет общего балла активности"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # Автоматически отслеженная активность
            cursor = await db.execute("""
                SELECT activity_type, SUM(points) 
                FROM user_activity 
                WHERE user_id = ? AND activity_date >= date('now', '-30 days')
                GROUP BY activity_type
            """, (user_id,))
            auto_activity = dict(await cursor.fetchall())
            
            # Активность, заявленная пользователем
            cursor = await db.execute("""
                SELECT orders_plus, auctions_plus, contests_plus, 
                       surveys_plus, content_plus, comments_plus
                FROM user_activity_reports 
                WHERE user_id = ? AND report_date >= date('now', '-30 days')
            """, (user_id,))
            user_reports = await cursor.fetchall()
            
            # Сверяем данные и рассчитываем итоговый балл
            total_score = 0
            activity_summary = []
            
            for activity_type in ACTIVITY_TYPES.keys():
                auto_points = auto_activity.get(activity_type, 0)
                user_points = sum(row[list(ACTIVITY_TYPES.keys()).index(activity_type)] for row in user_reports)
                
                # Берем минимум из автоматического и заявленного
                verified_points = min(auto_points, user_points * 0.01)  # 0.01 за каждый "+"
                total_score += verified_points
                
                if verified_points > 0:
                    activity_summary.append(f"{ACTIVITY_TYPES[activity_type]}: {verified_points:.3f}")
            
            # Обновляем в БД
            await db.execute("""
                UPDATE users SET 
                    monthly_activity_points = ?,
                    current_activity = ?
                WHERE user_id = ?
            """, (min(total_score, MAX_MONTHLY_ACTIVITY_BONUS), 
                  "; ".join(activity_summary), user_id))
            
            await db.commit()
            return total_score
            
    except Exception as e:
        logging.error(f"Error calculating activity score: {e}")
        return 0

async def export_activity_data():
    """Выгрузка данных активности в Google Sheets"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("""
                SELECT u.user_id, u.username, u.full_name, 
                       u.daily_activity_points, u.monthly_activity_points,
                       u.current_activity, u.created_at
                FROM users u
                WHERE u.monthly_activity_points > 0
                ORDER BY u.monthly_activity_points DESC
            """)
            activity_data = await cursor.fetchall()
        
        if not activity_data:
            return True
        
        # Создаем таблицу активности (используем существующую или создаем новую)
        ACTIVITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ActivityData123456789/edit?usp=sharing"
        
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_url(ACTIVITY_SHEET_URL).sheet1
        
        # Заголовки
        headers = [
            "ID пользователя", "Username", "ФИО", "Дневная активность",
            "Месячная активность", "Текущая активность", "Дата регистрации"
        ]
        
        # Данные
        data = [headers]
        for user_data in activity_data:
            data.append([
                user_data[0], user_data[1] or "", user_data[2] or "",
                user_data[3], user_data[4], user_data[5], user_data[6]
            ])
        
        sheet.clear()
        sheet.update('A1', data)
        
        logging.info("Activity data exported successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting activity data: {e}")
        return False

async def start_activity_system():
    """Запуск системы активности"""
    await init_activity_system()
    asyncio.create_task(scheduled_activity_sync())

async def scheduled_activity_sync():
    """Планировщик системы активности"""
    import pytz
    
    while True:
        try:
            moscow_tz = pytz.timezone('Europe/Moscow')
            now = datetime.now(moscow_tz)
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            
            if now >= target_time:
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            logging.info("Starting scheduled activity sync at 17:00 MSK")
            
            # Рассчитываем активность для всех пользователей
            async with aiosqlite.connect(DB_FILE) as db:
                cursor = await db.execute("SELECT user_id FROM users WHERE user_id != 0")
                users = await cursor.fetchall()
                
                for (user_id,) in users:
                    await calculate_activity_score(user_id)
            
            # Выгружаем данные
            await export_activity_data()
            
            logging.info("✅ Activity sync completed successfully")
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Error in scheduled activity sync: {e}")
        
        await asyncio.sleep(3600)