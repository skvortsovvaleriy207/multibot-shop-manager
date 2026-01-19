class Paginator:
    def __init__(self, items_per_page=3):
        self.items_per_page = items_per_page

    def calculate_pages(self, total_items, current_page):
        """Рассчитать общее количество страниц"""
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page

        if current_page > total_pages:
            current_page = total_pages
        if current_page < 1:
            current_page = 1

        return total_pages, current_page

    def get_offset(self, page):
        """Получить смещение для SQL запроса"""
        return (page - 1) * self.items_per_page

    def create_navigation_buttons(self, current_page, total_pages, prefix="cart_page"):
        """Создать кнопки навигации"""
        buttons = []

        if total_pages > 1:
            if current_page > 1:
                buttons.append(types.InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"{prefix}_{current_page - 1}"
                ))

            buttons.append(types.InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data=f"{prefix}_info"
            ))

            if current_page < total_pages:
                buttons.append(types.InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=f"{prefix}_{current_page + 1}"
                ))

        return buttons