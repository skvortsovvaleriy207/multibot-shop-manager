# Обновление функционала: Заказы, Заявки и Google Sheets

Этот документ описывает ключевые изменения, внесенные в бота (ветка `investmentsbot`), которые необходимо перенести в другие боты для корректной работы системы заказов, синхронизации с таблицами и стабильности интерфейса.

## 1. Логика оформления заказа (cart.py)

**Файл:** `investmentsbot/cart.py`
**Функция:** `cart_order_confirm`

*   **Изменение:** Теперь при оформлении заказа из корзины создаются записи в таблице `orders` (для каждого товара отдельно), а не одна общая запись в `order_requests`.
*   **Определение типа:** Добавлена логика определения `order_type` ('product', 'service', 'offer') на основе данных из исходной заявки (`order_requests.item_type`).
*   **Связь с продавцом:** Добавлен поиск `seller_id` (через `order_requests`) и отправка уведомления продавцу (`messages_system.send_system_message`).
*   **Обновление статуса:** Исходная заявка в `order_requests` помечается статусом `'processing'` (В обработке), чтобы показать, что процесс запущен.
*   **Синхронизация:** Вызывается новая функция `sync_orders_to_sheets()` для мгновенной отправки заказа в Google Таблицу "Заказы".
*   **Исправления:** Добавлен импорт `from messages_system import send_system_message`.

## 2. Интеграция с Google Sheets (google_sheets.py)

**Файл:** `investmentsbot/google_sheets.py`

*   **Разделение таблиц:**
    *   `SHEET_REQUESTS` (бывший `SHEET_ORDERS`) -> Лист "Заявки" (исходные объявления/карточки).
    *   `SHEET_REAL_ORDERS` -> Лист "Заказы" (фактические сделки/покупки).
*   **Новая функция синхронизации заказов:**
    *   Добавлена `sync_orders_to_sheets()`: выгружает таблицу `orders` в лист "Заказы".
    *   Поля: ID заказа, Дата, Тип, Товар, Покупатель, Продавец, Статус, Сумма и др.
*   **Исправления в импорте (sync_requests_from_sheets_to_db):**
    *   Исправлен заголовок столбца для поиска ID: с "ID заявки" на "ID заказа" (так как в таблице "Заявки" первый столбец часто называется ID заказа/заявки).
    *   Заменены устаревшие ссылки на `SHEET_ORDERS` -> `SHEET_REQUESTS`.
*   **Статусы:**
    *   В `sync_order_requests_to_sheets` добавлен статус `'processing'` -> "В обработке".

## 3. Оптимизация Callback Data (Кнопки категорий)

Telegram имеет лимит 64 байта на `callback_data`. Длинные названия категорий вызывали ошибку `BUTTON_DATA_INVALID`.

**Файлы:** `investmentsbot/shop.py`, `investmentsbot/order_request_system.py`

*   **Отправка ID вместо Имени:**
    *   В `shop.py` (`product_catalog`, `service_catalog`) кнопки теперь передают ID категории: `product_card_form|{id}` вместо `product_card_form|{name}`.
    *   То же самое для навигации (`show_..._category_items`): `product_cat_{id}`.
*   **Обратное разрешение (Resolution):**
    *   В `order_request_system.py` (`product_card_form_start`, `service_card_form_start`) добавлена проверка: если переданное значение — число, делается запрос в БД (`product_purposes` / `service_purposes`) для получения названия категории.

## 4. Стабильность сети (main.py)

**Файл:** `investmentsbot/main.py`

*   **Timeout:** В `dp.start_polling(bot)` добавлен параметр `polling_timeout=60` для предотвращения частых ошибок `Request timeout error` при нестабильном соединении.

---

### Инструкция по применению изменений:

1.  **БД:** Убедиться, что таблицы `orders`, `product_purposes`, `service_purposes` существуют и имеют столбец `id`.
2.  **Код:** Перенести изменения в файлы `cart.py`, `google_sheets.py`, `shop.py`, `order_request_system.py` по аналогии.
3.  **Импорты:** Проверить наличие `send_system_message` там, где отправляются уведомления.
4.  **Google Sheets:** Убедиться, что сервисный аккаунт имеет доступ к таблице и структура листов ("Заявки", "Заказы") соответствует ожиданиям скрипта.
