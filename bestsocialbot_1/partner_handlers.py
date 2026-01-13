from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from datetime import datetime

router = Router()

class PartnerManager:

    def add_partner_product(self, category, data):
        return True

partner_manager = PartnerManager()

class PartnerRegistration(StatesGroup):
    category = State()
    company = State()
    foundation_year = State()
    location = State()
    email = State()
    phone = State()
    products_services = State()
    problems = State()
    business_proposal = State()
    manager = State()
    conditions = State()

@router.callback_query(F.data == "become_partner")
async def start_partner_registration(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Автотехника", callback_data="partner_auto")],
        [InlineKeyboardButton(text="🔧 Автоуслуги", callback_data="partner_services")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    
    await callback.message.edit_text(
        "🤝 <b>Регистрация партнера</b>\n\n"
        "Выберите категорию для партнерства:",
        reply_markup=keyboard
    )
    await state.set_state(PartnerRegistration.category)

@router.callback_query(F.data.in_(["partner_auto", "partner_services"]))
async def select_category(callback: CallbackQuery, state: FSMContext):

    category = "автотехника" if callback.data == "partner_auto" else "услуги"
    await state.update_data(category=category)
    
    await callback.message.edit_text(
        f"📝 <b>Регистрация партнера - {category.title()}</b>\n\n"
        "Введите название вашей компании:"
    )
    await state.set_state(PartnerRegistration.company)

@router.message(PartnerRegistration.company)
async def get_company(message: Message, state: FSMContext):
    """Получить название компании"""
    await state.update_data(company=message.text)
    await message.answer("📅 Введите год основания компании:")
    await state.set_state(PartnerRegistration.foundation_year)

@router.message(PartnerRegistration.foundation_year)
async def get_foundation_year(message: Message, state: FSMContext):
    """Получить год основания"""
    await state.update_data(foundation_year=message.text)
    await message.answer("📍 Введите местонахождение компании:")
    await state.set_state(PartnerRegistration.location)

@router.message(PartnerRegistration.location)
async def get_location(message: Message, state: FSMContext):
    """Получить местонахождение"""
    await state.update_data(location=message.text)
    await message.answer("📧 Введите email для связи:")
    await state.set_state(PartnerRegistration.email)

@router.message(PartnerRegistration.email)
async def get_email(message: Message, state: FSMContext):
    """Получить email"""
    await state.update_data(email=message.text)
    await message.answer("📱 Введите телефон для связи:")
    await state.set_state(PartnerRegistration.phone)

@router.message(PartnerRegistration.phone)
async def get_phone(message: Message, state: FSMContext):
    """Получить телефон"""
    await state.update_data(phone=message.text)
    
    data = await state.get_data()
    category = data.get("category")
    
    if category == "автотехника":
        await message.answer("🛒 Опишите ваши товары (автотехника):")
    else:
        await message.answer("🔧 Опишите ваши услуги:")
    
    await state.set_state(PartnerRegistration.products_services)

@router.message(PartnerRegistration.products_services)
async def get_products_services(message: Message, state: FSMContext):
    """Получить товары/услуги"""
    await state.update_data(products_services=message.text)
    
    await message.answer(
        "⚠️ Опишите проблемы, которые решают ваши товары/услуги:\n"
        "• Экономические проблемы\n"
        "• Социальные проблемы\n" 
        "• Экологические проблемы\n"
        "• Другие проблемы"
    )
    await state.set_state(PartnerRegistration.problems)

@router.message(PartnerRegistration.problems)
async def get_problems(message: Message, state: FSMContext):
    """Получить описание проблем"""
    await state.update_data(problems=message.text)
    await message.answer("💼 Опишите ваше бизнес-предложение:")
    await state.set_state(PartnerRegistration.business_proposal)

@router.message(PartnerRegistration.business_proposal)
async def get_business_proposal(message: Message, state: FSMContext):
    """Получить бизнес-предложение"""
    await state.update_data(business_proposal=message.text)
    await message.answer("👨‍💼 Укажите руководителя/менеджера проекта:")
    await state.set_state(PartnerRegistration.manager)

@router.message(PartnerRegistration.manager)
async def get_manager(message: Message, state: FSMContext):
    """Получить менеджера"""
    await state.update_data(manager=message.text)
    await message.answer("📋 Опишите условия партнерства:")
    await state.set_state(PartnerRegistration.conditions)

@router.message(PartnerRegistration.conditions)
async def complete_registration(message: Message, state: FSMContext):
    """Завершить регистрацию партнера"""
    await state.update_data(conditions=message.text)
    data = await state.get_data()
    
    # Подготовка данных для сохранения
    partner_data = {
        "telegram_id": message.from_user.id,
        "username": message.from_user.username or "",
        "company": data.get("company", ""),
        "foundation_year": data.get("foundation_year", ""),
        "location": data.get("location", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "business_proposal": data.get("business_proposal", ""),
        "manager": data.get("manager", ""),
        "partnership_conditions": data.get("conditions", ""),
        "contacts": f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    }
    
    category = data.get("category")
    if category == "автотехника":
        partner_data["products"] = data.get("products_services", "")
    else:
        partner_data["services"] = data.get("products_services", "")
    
    # Обработка проблем
    problems_text = data.get("problems", "")
    partner_data.update({
        "economic_problem": "Да" if "экономич" in problems_text.lower() else "Нет",
        "social_problem": "Да" if "социальн" in problems_text.lower() else "Нет", 
        "ecological_problem": "Да" if "экологич" in problems_text.lower() else "Нет",
        "other_problem": problems_text if not any(x in problems_text.lower() for x in ["экономич", "социальн", "экологич"]) else ""
    })
    
    # Сохранение в таблицу
    success = partner_manager.add_partner_product(category, partner_data)
    
    if success:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(
            "✅ <b>Регистрация завершена!</b>\n\n"
            f"Вы успешно зарегистрированы как партнер в категории <b>{category}</b>.\n"
            "Ваша заявка будет рассмотрена администратором.\n\n"
            "Спасибо за интерес к партнерству! 🤝",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при регистрации.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
    
    await state.clear()

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """Возврат в главное меню"""
    from shop import personal_account
    await personal_account(callback)

@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена операции"""
    await state.clear()
    from shop import personal_account
    await personal_account(callback)

