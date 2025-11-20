"""Обработчики событий бота."""

from aiogram import Dispatcher

from app.bot.handlers.error_handler import register_error_handler
from app.bot.handlers.grade_handler import register_grade_handlers
from app.bot.handlers.group_selection_handler import register_group_selection_handlers
from app.bot.handlers.group_setup_handler import register_group_setup_handlers
from app.bot.handlers.invitation_handler import register_invitation_handlers
from app.bot.handlers.main_menu_handler import register_main_menu_handlers
from app.bot.handlers.profile_handler import register_profile_handlers
from app.bot.handlers.simplified_menu_handler import register_simplified_menu_handlers
from app.bot.handlers.start_handler import register_start_handlers


async def register_handlers(dp: Dispatcher) -> None:
    """Регистрация всех обработчиков."""
    await register_start_handlers(dp)
    await register_main_menu_handlers(dp)
    await register_simplified_menu_handlers(dp)
    await register_group_selection_handlers(dp)
    await register_group_setup_handlers(dp)
    await register_profile_handlers(dp)
    await register_grade_handlers(dp)
    await register_invitation_handlers(dp)
    await register_error_handler(dp)
