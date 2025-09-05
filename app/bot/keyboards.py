"""
Клавиатуры для Telegram бота.
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import *
from ..models.user import User


def get_main_menu_keyboard(user_profile: Optional[User] = None) -> InlineKeyboardMarkup:
    """Создать главное меню."""
    builder = InlineKeyboardBuilder()
    
    if user_profile:
        # Персонализированное меню
        builder.button(text="📅 Мое расписание", callback_data=MenuCallback(action="my_schedule"))
        builder.button(text="👥 Найти группу", callback_data=MenuCallback(action="search_group"))
        builder.button(text="📝 Заявления", callback_data=MenuCallback(action="applications"))
        builder.button(text="📊 Мой дневник", callback_data=MenuCallback(action="diary"))
        builder.button(text="📚 Аттестация", callback_data=MenuCallback(action="attestation"))
        builder.button(text="🔢 Мои ОСБ/КНЛ/КНС", callback_data=MenuCallback(action="grades"))
        builder.button(text="🔔 Напоминания", callback_data=MenuCallback(action="reminders"))
        builder.button(text="⚙️ Настройки", callback_data=MenuCallback(action="settings"))
        builder.button(text="🔍 Поиск (старый)", callback_data=MenuCallback(action="search"))
        builder.adjust(2)
    else:
        # Меню для новых пользователей
        builder.button(text="🎓 Настроить профиль", callback_data=MenuCallback(action="setup_profile"))
        builder.button(text="🔍 Разовый поиск расписания", callback_data=MenuCallback(action="search"))
        builder.adjust(1)
    
    return builder.as_markup()


def get_group_search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поиска групп."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Быстрый поиск", callback_data=GroupSearchCallback(action="quick_search"))
    builder.button(text="📊 Подробный поиск", callback_data=GroupSearchCallback(action="detailed_search"))
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_group_result_keyboard(group_number: str) -> InlineKeyboardMarkup:
    """Клавиатура результатов поиска группы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Текущая неделя", callback_data=GroupSearchCallback(action="show_schedule", group_number=group_number, week="current"))
    builder.button(text="⬅️ Предыдущая", callback_data=GroupSearchCallback(action="show_schedule", group_number=group_number, week="prev"))
    builder.button(text="➡️ Следующая", callback_data=GroupSearchCallback(action="show_schedule", group_number=group_number, week="next"))
    builder.button(text="📊 Excel", callback_data=GroupSearchCallback(action="export", group_number=group_number))
    builder.button(text="🔍 Новый поиск", callback_data=MenuCallback(action="search_group"))
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(3, 2)
    return builder.as_markup()


def get_profile_setup_keyboard(step: str, options: List[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура настройки профиля."""
    builder = InlineKeyboardBuilder()
    
    if options:
        for option in options:
            builder.button(text=option, callback_data=ProfileCallback(action=step, value=option))
        builder.adjust(2)
    
    return builder.as_markup()


def get_error_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ошибок."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Попробовать снова", callback_data=MenuCallback(action="retry"))
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()