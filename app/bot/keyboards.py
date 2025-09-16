"""
Генераторы клавиатур для Telegram бота.

Зона ответственности:
- Создание инлайн-клавиатур для различных состояний бота
- Генерация главного меню в зависимости от статуса пользователя
- Формирование клавиатур для выбора группы и подтверждения
- Создание интерфейса для настройки профиля пользователя
- Обработка клавиатур ошибок и повторных попыток
- Адаптивная структура кнопок под размер экрана
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import MenuCallback, ProfileCallback, GroupSearchCallback
from app.models.user import User


def get_main_menu_keyboard(user_profile: Optional[User] = None) -> InlineKeyboardMarkup:
    """Создать главное меню."""
    builder = InlineKeyboardBuilder()

    if user_profile:
        # Персонализированное меню
        builder.button(
            text="📅 Мое расписание", callback_data=MenuCallback(action="my_schedule")
        )
        builder.button(
            text="📊 Экспорт (Excel/iCal)", callback_data=MenuCallback(action="export")
        )
        builder.button(
            text="📝 Заявления", callback_data=MenuCallback(action="applications")
        )
        builder.button(
            text="📊 Мой дневник", callback_data=MenuCallback(action="diary")
        )
        builder.button(
            text="📚 Аттестация", callback_data=MenuCallback(action="attestation")
        )
        builder.button(
            text="🔢 Мои ОСБ/КНЛ/КНС", callback_data=MenuCallback(action="grades")
        )
        builder.button(
            text="🔔 Напоминания", callback_data=MenuCallback(action="reminders")
        )
        builder.button(
            text="⚙️ Настройки", callback_data=MenuCallback(action="settings")
        )
        builder.adjust(2)
    else:
        # Меню для новых пользователей - упрощенный выбор группы
        builder.button(
            text="🎓 Выбрать группу", callback_data=MenuCallback(action="select_group")
        )
        builder.adjust(1)

    return builder.as_markup()


def get_group_selection_keyboard(faculties: List[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора группы с автоопределением."""
    builder = InlineKeyboardBuilder()

    if faculties:
        # Показываем факультеты как есть (без хардкода)
        for faculty in faculties[:10]:  # Ограничиваем количество
            # Сокращаем длинные названия для callback data
            short_faculty = faculty[:10] if len(faculty) > 10 else faculty
            builder.button(
                text=f"🏛️ {faculty}",
                callback_data=GroupSearchCallback(
                    action="select_faculty", value=short_faculty
                ),
            )
        builder.adjust(1)
    else:
        # Альтернативный ввод номера группы
        builder.button(
            text="✍️ Ввести номер группы",
            callback_data=GroupSearchCallback(action="manual_input"),
        )

    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    return builder.as_markup()


def get_group_confirmation_keyboard(group_info: dict) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения выбора группы."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=GroupSearchCallback(
            action="confirm_group", group_id=str(group_info.get("id", ""))
        ),
    )
    builder.button(
        text="🔄 Выбрать другую", callback_data=MenuCallback(action="select_group")
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(1)
    return builder.as_markup()


def get_profile_setup_keyboard(
    step: str, options: List[str] = None
) -> InlineKeyboardMarkup:
    """Клавиатура настройки профиля."""
    builder = InlineKeyboardBuilder()

    if options:
        for option in options:
            builder.button(
                text=option, callback_data=ProfileCallback(action=step, value=option)
            )
        builder.adjust(2)

    return builder.as_markup()


def get_error_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ошибок."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Попробовать снова", callback_data=MenuCallback(action="retry")
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_simple_group_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура для настройки группы."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✍️ Ввести номер группы", 
        callback_data="group_setup:enter_manually"
    )
    builder.button(
        text="📋 Выбрать из списка", 
        callback_data="group_setup:select_from_list"
    )
    builder.button(
        text="❌ Отмена", 
        callback_data="group_setup:cancel"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_keyboard(confirm_action: str, cancel_action: str = "cancel") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить", 
        callback_data=f"group_setup:{confirm_action}"
    )
    builder.button(
        text="❌ Отмена", 
        callback_data=f"group_setup:{cancel_action}"
    )
    builder.adjust(2)
    return builder.as_markup()
