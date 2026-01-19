from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

storage = MemoryStorage()
dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

# Регистрация роутеров
def register_routers():
    """Регистрация всех роутеров"""
    try:
        from partner_handlers import router as partner_router
        dp.include_router(partner_router)
        print("[OK] Партнерский роутер зарегистрирован")
    except Exception as e:
        print(f"[ERROR] Ошибка регистрации партнерского роутера: {e}")

# Автоматическая регистрация при импорте
register_routers()

