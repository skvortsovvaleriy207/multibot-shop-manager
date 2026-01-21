
import aiosqlite
import logging

async def aggregate_user_statistics():
    """
    Агрегирует статистику пользователей (заказы, товары, услуги, рефералы)
    и обновляет таблицу users для последующей выгрузки в Google Sheets.
    """
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            print("Начинаем агрегацию статистики пользователей...")

            # 1. Агрегация рефералов (если referral_system.py не обновил)
            # Примечание: referral_system.py обновляет total_referrals инкрементально,
            # но для надежности можно пересчитать.
            # Пока оставим как есть в referral_system, но убедимся, что поля синхронизированы.
            
            # 2. Агрегация покупок (Orders where user_id is buyer)
            # Примечание: в таблице orders нет поля price, берем из товаров/услуг
            # Однако цена могла измениться, но для примерной статистики пойдет текущая цена
            # Или лучше использовать order_requests? Но там сложнее связь.
            cursor = await db.execute("""
                SELECT o.user_id, COUNT(*), SUM(
                    CASE 
                        WHEN o.order_type = 'tech' THEN CAST(ap.price AS REAL)
                        WHEN o.order_type = 'service' THEN CAST(as_.price AS REAL)
                        ELSE 0
                    END
                )
                FROM orders o
                LEFT JOIN auto_products ap ON o.item_id = ap.id AND o.order_type = 'tech'
                LEFT JOIN auto_services as_ ON o.item_id = as_.id AND o.order_type = 'service'
                WHERE o.status = 'completed'
                GROUP BY o.user_id
            """)
            purchases = await cursor.fetchall()

            for user_id, count, total_sum in purchases:
                # Обновляем числовые поля
                await db.execute("""
                    UPDATE users 
                    SET purchases_count = ?, total_purchases = ?
                    WHERE user_id = ?
                """, (count, total_sum or 0, user_id))
                
                # Обновляем текстовое поле для Google Sheets (как в ТЗ)
                purchases_text = f"{count} (на {total_sum or 0})"
                await db.execute("""
                    UPDATE users SET purchases = ? WHERE user_id = ?
                """, (purchases_text, user_id))

            # 3. Агрегация продаж (Orders where seller_id is seller)
            cursor = await db.execute("""
                SELECT o.seller_id, COUNT(*), SUM(
                    CASE 
                        WHEN o.order_type = 'tech' THEN CAST(ap.price AS REAL)
                        WHEN o.order_type = 'service' THEN CAST(as_.price AS REAL)
                        ELSE 0
                    END
                )
                FROM orders o
                LEFT JOIN auto_products ap ON o.item_id = ap.id AND o.order_type = 'tech'
                LEFT JOIN auto_services as_ ON o.item_id = as_.id AND o.order_type = 'service'
                WHERE o.status = 'completed'
                GROUP BY o.seller_id
            """)
            sales = await cursor.fetchall()

            for seller_id, count, total_sum in sales:
                await db.execute("""
                    UPDATE users 
                    SET sales_count = ?, total_sales = ?
                    WHERE user_id = ?
                """, (count, total_sum or 0, seller_id))
                
                sales_text = f"{count} (на {total_sum or 0})"
                await db.execute("""
                    UPDATE users SET sales = ? WHERE user_id = ?
                """, (sales_text, seller_id))

            # 4. Агрегация товаров и услуг
            # Считаем товары
            cursor = await db.execute("""
                SELECT user_id, COUNT(*) FROM auto_products GROUP BY user_id
            """)
            products_counts = {row[0]: row[1] for row in await cursor.fetchall()}

            # Считаем услуги
            cursor = await db.execute("""
                SELECT user_id, COUNT(*) FROM auto_services GROUP BY user_id
            """)
            services_counts = {row[0]: row[1] for row in await cursor.fetchall()}

            # Объединяем и обновляем
            all_users_with_items = set(products_counts.keys()) | set(services_counts.keys())
            
            for user_id in all_users_with_items:
                p_count = products_counts.get(user_id, 0)
                s_count = services_counts.get(user_id, 0)
                
                # Формируем строку статистики
                stats_text = []
                if p_count > 0:
                    stats_text.append(f"Товары: {p_count}")
                if s_count > 0:
                    stats_text.append(f"Услуги: {s_count}")
                
                final_text = ", ".join(stats_text)
                
                await db.execute("""
                    UPDATE users SET products_services = ? WHERE user_id = ?
                """, (final_text, user_id))

            # 5. Обновление даты партнерства и shop_id
            # Если shop_id пустой, устанавливаем его равным user_id
            await db.execute("""
                UPDATE users SET shop_id = user_id WHERE shop_id IS NULL OR shop_id = ''
            """)

            # Если пользователь партнер, но дата партнерства не стоит, ставим дату регистрации или текущую
            await db.execute("""
                UPDATE users 
                SET partnership_date = created_at 
                WHERE (active_partner = 'Да' OR account_status = 'ПАРТНЕР') 
                AND (partnership_date IS NULL OR partnership_date = '')
            """)

            # 6. Агрегация заявок (Requests)
            # Считаем общее количество заявок и количество активных
            cursor = await db.execute("""
                SELECT user_id, 
                       COUNT(*) as total,
                       SUM(CASE WHEN status IN ('new', 'active') THEN 1 ELSE 0 END) as active
                FROM order_requests
                GROUP BY user_id
            """)
            requests_counts = await cursor.fetchall()
            
            for user_id, total, active in requests_counts:
                 requests_text = f"{total} / {active or 0}"
                 await db.execute("""
                    UPDATE users SET requests_text = ? WHERE user_id = ?
                 """, (requests_text, user_id))

            await db.commit()
            print("Агрегация статистики успешно завершена.")
            return True

    except Exception as e:
        logging.error(f"Ошибка агрегации статистики: {e}")
        return False
