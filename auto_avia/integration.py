# integration.py
import gspread
from datetime import datetime
import logging
from typing import Dict, Any
from config import BESTHOME_SURVEY_SHEET_URL, WOND_SURVEY_SHEET_URL, AUTO_SURVEY_SHEET_URL, CREDENTIALS_FILE


class GoogleSheetsIntegrator:
    """Класс для интеграции данных только между Google Sheets разных ботов"""

    def __init__(self, source_bot: str = "autoavia"):
        self.source_bot = source_bot
        self.client = gspread.service_account(filename=CREDENTIALS_FILE)

    async def integrate_to_wond_sheets_only(self, user_id: int) -> Dict[str, Any]:
        """
        Интегрирует данные пользователя только в Google Sheets бота Wond

        Args:
            user_id: ID пользователя

        Returns:
            dict: Результат интеграции
        """
        try:
            # Получаем данные пользователя из исходной таблицы besthome
            user_data = await self._get_user_data_from_source_sheet(user_id)

            if not user_data:
                return {
                    "success": False,
                    "message": "Пользователь не найден в таблице besthome",
                    "target_bot": "wond"
                }

            # Записываем данные в таблицу Wond
            sheets_success = await self._write_to_target_sheets(user_data, "wond")

            if sheets_success:
                return {
                    "success": True,
                    "message": "Данные успешно интегрированы в Google Sheets бота Wond",
                    "user_id": user_id,
                    "target_bot": "wond",
                    "sheets_sync": True
                }
            else:
                return {
                    "success": False,
                    "message": "Ошибка интеграции в Google Sheets бота Wond",
                    "target_bot": "wond",
                    "sheets_sync": False
                }

        except Exception as e:
            logging.error(f"Ошибка интеграции в Wond Sheets: {e}")
            return {
                "success": False,
                "message": f"Ошибка интеграции: {str(e)}",
                "target_bot": "wond"
            }

    async def integrate_to_besthome_sheets_only(self, user_id: int) -> Dict[str, Any]:
        """
        Интегрирует данные пользователя только в Google Sheets бота besthome

        Args:
            user_id: ID пользователя

        Returns:
            dict: Результат интеграции
        """
        try:
            # Получаем данные пользователя из исходной таблицы besthome
            user_data = await self._get_user_data_from_source_sheet(user_id)

            if not user_data:
                return {
                    "success": False,
                    "message": "Пользователь не найден в таблице besthome",
                    "target_bot": "besthome"
                }

            # Записываем данные в таблицу besthome
            sheets_success = await self._write_to_target_sheets(user_data, "besthome")

            if sheets_success:
                return {
                    "success": True,
                    "message": "Данные успешно интегрированы в Google Sheets бота besthome",
                    "user_id": user_id,
                    "target_bot": "besthome",
                    "sheets_sync": True
                }
            else:
                return {
                    "success": False,
                    "message": "Ошибка интеграции в Google Sheets бота besthome",
                    "target_bot": "besthome",
                    "sheets_sync": False
                }

        except Exception as e:
            logging.error(f"Ошибка интеграции в besthome Sheets: {e}")
            return {
                "success": False,
                "message": f"Ошибка интеграции: {str(e)}",
                "target_bot": "besthome"
            }

    async def _get_user_data_from_source_sheet(self, user_id: int) -> Dict[str, Any]:
        """
        Получает данные пользователя из Google Sheets текущего бота

        Args:
            user_id: ID пользователя для поиска

        Returns:
            dict: Данные пользователя или пустой словарь если не найден
        """
        try:
            # Открываем таблицу besthome
            spreadsheet = self.client.open_by_url(BESTHOME_SURVEY_SHEET_URL)
            worksheet = spreadsheet.worksheet("Основная таблица")

            # Получаем все данные
            all_data = worksheet.get_all_records()

            # Ищем пользователя по Telegram ID
            for row in all_data:
                # Ищем поле с Telegram ID (может быть в разных столбцах)
                telegram_id = None

                # Пробуем разные возможные названия столбцов
                if 'Telegram ID' in row:
                    telegram_id = row['Telegram ID']
                elif 'User ID' in row:
                    telegram_id = row['User ID']
                elif 'ID' in row:
                    telegram_id = row['ID']

                # Пропускаем пустые значения
                if not telegram_id or str(telegram_id).strip() == '':
                    continue

                # Проверяем совпадение ID
                try:
                    if int(str(telegram_id).strip()) == user_id:
                        return row
                except (ValueError, TypeError):
                    continue

            return {}

        except Exception as e:
            logging.error(f"Ошибка получения данных из таблицы: {e}")
            return {}

    async def _write_to_target_sheets(self, user_data: Dict[str, Any], target_bot: str) -> bool:
        """
        Записывает данные в Google Sheets целевого бота

        Args:
            user_data: Данные пользователя из исходной таблицы
            target_bot: Название целевого бота ('wond' или 'besthome')

        Returns:
            bool: Успешность записи
        """
        try:
            # Определяем URL целевой таблицы
            if target_bot == "wond":
                sheet_url = WOND_SURVEY_SHEET_URL
            elif target_bot == "besthome":
                sheet_url = BESTHOME_SURVEY_SHEET_URL
            else:
                logging.error(f"Неизвестный целевой бот: {target_bot}")
                return False

            if not sheet_url:
                logging.error(f"Не указан URL таблицы для бота {target_bot}")
                return False

            # Открываем целевую таблицу
            spreadsheet = self.client.open_by_url(sheet_url)
            worksheet = spreadsheet.worksheet("Основная таблица")

            # Получаем существующие данные
            existing_data = worksheet.get_all_records()

            # Форматируем строку для добавления (базовые поля)
            new_row = [
                datetime.now().strftime("%d/%m/%Y"),  # Дата опроса
                user_data.get('Telegram ID') or user_data.get('User ID') or user_data.get('ID') or '',
                user_data.get('Username', '') or user_data.get('Телеграм @username', ''),
                user_data.get('ФИО', '') or user_data.get('ФИО подписчика', ''),
                user_data.get('Дата рождения', ''),
                user_data.get('Место жительства', ''),
                user_data.get('Email', ''),
                user_data.get('Мобильный телефон', '') or user_data.get('Телефон', ''),
                user_data.get('Текущая занятость', '') or user_data.get('Занятость', ''),
                user_data.get('Финансовая проблема', ''),
                user_data.get('Социальная проблема', ''),
                user_data.get('Экологическая проблема', ''),
                user_data.get('Пассивный подписчик', '') or user_data.get('Пассивный подписчик (1.0)', ''),
                user_data.get('Активный партнер', '') or user_data.get('Активный партнер (2.0)', ''),
                user_data.get('Инвестор/трейдер', '') or user_data.get('Инвестор/трейдер (3.0)', ''),
                user_data.get('Бизнес-предложение', ''),
                self._safe_float(user_data.get('ИТОГО бонусов') or user_data.get('Сумма бонусов')),
                self._safe_float(user_data.get('Корректировка бонусов')),
                self._safe_float(user_data.get('ТЕКУЩИЙ БАЛАНС') or user_data.get('Текущий баланс')),
                user_data.get('Стоимость проблем', ''),
                user_data.get('Иная информация', '') or user_data.get('Примечания', ''),
                user_data.get('ДД/ММ/ГГ партнерства', '') or user_data.get('Дата партнерства', ''),
                self._safe_int(user_data.get('Количество рефералов', 0)),
                user_data.get('Оплата за рефералов', ''),
                user_data.get('ДД/ММ/ГГ подписки', '') or user_data.get('Дата подписки', ''),
                user_data.get('Срок подписки', '') or user_data.get('Дата оплаты подписки', ''),
                user_data.get('Покупки в магазине', '') or user_data.get('Покупки', ''),
                user_data.get('Продажи в магазине', '') or user_data.get('Продажи', ''),
                user_data.get('Иная информация магазин', '') or user_data.get('Реквизиты', ''),
                user_data.get('Статус в магазине', '') or user_data.get('ID в магазине', ''),
                user_data.get('Бизнес подписчика', '') or user_data.get('Бизнес', ''),
                user_data.get('Заказы/Товары/Услуги', '') or user_data.get('Товары/услуги', ''),
                user_data.get('Статус аккаунта (Р/Б)', '') or user_data.get('Статус аккаунта', 'Р')
            ]

            # Проверяем, существует ли уже пользователь в целевой таблице
            user_exists = False
            user_row_index = None

            for i, row in enumerate(existing_data, start=2):  # начинаем с 2 строки (1 - заголовки)
                # Ищем по Telegram ID (разные возможные названия столбцов)
                target_telegram_id = None

                if 'Telegram ID' in row:
                    target_telegram_id = row['Telegram ID']
                elif 'User ID' in row:
                    target_telegram_id = row['User ID']
                elif 'ID' in row:
                    target_telegram_id = row['ID']
                elif 'ID пользователя' in row:
                    target_telegram_id = row['ID пользователя']
                elif 'ID клиента' in row:
                    target_telegram_id = row['ID клиента']

                # Получаем исходный ID
                source_telegram_id = user_data.get('Telegram ID') or user_data.get('User ID') or user_data.get('ID')

                # Пропускаем пустые значения
                if not target_telegram_id or not source_telegram_id:
                    continue

                # Сравниваем как строки
                if str(target_telegram_id).strip() == str(source_telegram_id).strip():
                    user_exists = True
                    user_row_index = i
                    break

            # Обновляем или добавляем данные
            if user_exists and user_row_index:
                # Обновляем существующую запись
                for col_idx, value in enumerate(new_row, start=1):
                    worksheet.update_cell(user_row_index, col_idx, value)
            else:
                # Добавляем новую строку
                worksheet.append_row(new_row)

            return True

        except Exception as e:
            logging.error(f"Ошибка записи в Google Sheets {target_bot}: {e}")
            return False

    def _safe_float(self, value) -> float:
        """Безопасное преобразование в float"""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value) -> int:
        """Безопасное преобразование в int"""
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0


# Функции для использования в боте bestHome
async def integrate_user_to_wond_sheets_only(user_id: int) -> Dict[str, Any]:
    """Интегрирует пользователя только в Google Sheets бота Wond"""
    integrator = GoogleSheetsIntegrator("autoavia")
    return await integrator.integrate_to_wond_sheets_only(user_id)


async def integrate_user_to_besthome_sheets_only(user_id: int) -> Dict[str, Any]:
    """Интегрирует пользователя только в Google Sheets бота besthome"""
    integrator = GoogleSheetsIntegrator("autoavia")
    return await integrator.integrate_to_besthome_sheets_only(user_id)