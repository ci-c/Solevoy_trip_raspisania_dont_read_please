"""
Обработчики событий бота.
"""

from aiogram import Dispatcher

from app.bot.handlers.start_handler import register_start_handlers
from app.bot.handlers.simplified_menu_handler import register_simplified_menu_handlers
from app.bot.handlers.group_selection_handler import register_group_selection_handlers
from app.bot.handlers.group_setup_handler import register_group_setup_handlers
from app.bot.handlers.profile_handler import register_profile_handlers
from app.bot.handlers.error_handler import register_error_handler


async def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков."""
    await register_start_handlers(dp)
    await register_simplified_menu_handlers(dp)
    await register_group_selection_handlers(dp)
    await register_group_setup_handlers(dp)
    await register_profile_handlers(dp)
    await register_error_handler(dp)
