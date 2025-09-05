"""
Обработчики событий бота.
"""

from aiogram import Dispatcher
from .start_handler import register_start_handlers
from .group_search_handler import register_group_search_handlers
from .profile_handler import register_profile_handlers
from .error_handler import register_error_handler


async def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков."""
    await register_start_handlers(dp)
    await register_group_search_handlers(dp)
    await register_profile_handlers(dp)
    await register_error_handler(dp)