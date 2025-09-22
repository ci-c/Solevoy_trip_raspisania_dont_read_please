# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Генераторы клавиатур для Telegram бота.

Зона ответственности:
- Создание инлайн-клавиатур для различных состояний бота
- Генерация главного меню в зависимости от статуса пользователя
- Формирование клавиатур для выбора группы и подтверждения
- Создание интерфейса для настройки профиля пользователя
- Обработка клавиатур ошибок и повторных попыток
- Адаптивная структура кнопок под размер экрана
"""

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.bot.callbacks import GradeCallback, GroupSearchCallback, InvitationCallback, MenuCallback, ProfileCallback
from app.models.user import User


def get_main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """Создать главное меню с ReplyKeyboardMarkup.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню.
    """
    builder = ReplyKeyboardBuilder()
    
    # Основные функции (группируем по смыслу)
    builder.button(text="📅 Расписание")
    builder.button(text="📊 Оценки")
    builder.button(text="📚 Группа")
    builder.button(text="❓ Помощь")
    
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_main_menu_keyboard(user_profile: User | None = None) -> InlineKeyboardMarkup:
    """Создать главное меню.

    Args:
        user_profile: Профиль пользователя или None для новых пользователей.

    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню.

    """
    builder = InlineKeyboardBuilder()

    if user_profile:
        # Персонализированное меню
        builder.button(
            text="📅 Мое расписание",
            callback_data=MenuCallback(action="my_schedule"),
        )
        builder.button(
            text="📊 Экспорт (Excel/iCal)",
            callback_data=MenuCallback(action="export"),
        )
        builder.button(
            text="📝 Заявления",
            callback_data=MenuCallback(action="applications"),
        )
        builder.button(
            text="📊 Мой дневник",
            callback_data=MenuCallback(action="diary"),
        )
        builder.button(
            text="📚 Аттестация",
            callback_data=MenuCallback(action="attestation"),
        )
        builder.button(
            text="🔢 Мои ОСБ/КНЛ/КНС",
            callback_data=MenuCallback(action="grades"),
        )
        builder.button(
            text="🔔 Напоминания",
            callback_data=MenuCallback(action="reminders"),
        )
        builder.button(
            text="⚙️ Настройки",
            callback_data=MenuCallback(action="settings"),
        )
        builder.adjust(2)
    else:
        # Меню для новых пользователей - упрощенный выбор группы
        builder.button(
            text="🎓 Выбрать группу",
            callback_data=MenuCallback(action="select_group"),
        )
        builder.adjust(1)

    return builder.as_markup()


def get_group_selection_keyboard(faculties: list[str] | None = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора группы с автоопределением.

    Args:
        faculties: Список факультетов для выбора или None.

    Returns:
        InlineKeyboardMarkup: Клавиатура выбора группы.

    """
    builder = InlineKeyboardBuilder()

    if faculties:
        # Показываем факультеты как есть (без хардкода)
        MAX_FACULTIES = 10
        for faculty in faculties[:MAX_FACULTIES]:  # Ограничиваем количество
            # Сокращаем длинные названия для callback data
            short_faculty = faculty[:10] if len(faculty) > 10 else faculty
            builder.button(
                text=f"🏛️ {faculty}",
                callback_data=GroupSearchCallback(
                    action="select_faculty",
                    value=short_faculty,
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
    """Клавиатура подтверждения выбора группы.

    Args:
        group_info: Информация о выбранной группе.

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения.

    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=GroupSearchCallback(
            action="confirm_group",
            group_id=str(group_info.get("id", "")),
        ),
    )
    builder.button(
        text="🔄 Выбрать другую",
        callback_data=MenuCallback(action="select_group"),
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(1)
    return builder.as_markup()


def get_profile_setup_keyboard(
    step: str,
    options: list[str] | None = None,
) -> InlineKeyboardMarkup:
    """Клавиатура настройки профиля.

    Args:
        step: Текущий шаг настройки.
        options: Список опций для выбора или None.

    Returns:
        InlineKeyboardMarkup: Клавиатура настройки профиля.

    """
    builder = InlineKeyboardBuilder()

    if options:
        for option in options:
            builder.button(
                text=option,
                callback_data=ProfileCallback(action=step, value=option),
            )
        builder.adjust(2)

    return builder.as_markup()


def get_error_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ошибок.

    Returns:
        InlineKeyboardMarkup: Клавиатура для обработки ошибок.

    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Попробовать снова",
        callback_data=MenuCallback(action="retry"),
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_simple_group_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура для настройки группы.

    Returns:
        InlineKeyboardMarkup: Простая клавиатура настройки группы.

    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📋 Выбрать из списка",
        callback_data="group_setup:select_from_list",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_keyboard(
    confirm_action: str,
    cancel_action: str = "cancel",
) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения.

    Args:
        confirm_action: Действие при подтверждении.
        cancel_action: Действие при отмене.

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения.

    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"group_setup:{confirm_action}",
    )
    builder.button(
        text="❌ Отмена",
        callback_data=f"group_setup:{cancel_action}",
    )
    builder.adjust(2)
    return builder.as_markup()


def get_grades_keyboard(subjects: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура для управления оценками.

    Args:
        subjects: Список предметов пользователя.

    Returns:
        InlineKeyboardMarkup: Клавиатура оценок.

    """
    builder = InlineKeyboardBuilder()
    
    if subjects:
        for subject in subjects[:10]:  # Ограничиваем количество предметов
            builder.button(
                text=f"📚 {subject}",
                callback_data=GradeCallback(action="view_subject", subject=subject),
            )
        builder.adjust(1)
    else:
        builder.button(
            text="➕ Добавить предмет",
            callback_data=GradeCallback(action="add_subject"),
        )
    
    builder.button(
        text="🏠 В меню",
        callback_data=MenuCallback(action="home"),
    )
    builder.adjust(1)
    
    return builder.as_markup()


def get_subject_grades_keyboard(subject: str) -> InlineKeyboardMarkup:
    """Клавиатура для работы с конкретным предметом.

    Args:
        subject: Название предмета.

    Returns:
        InlineKeyboardMarkup: Клавиатура предмета.

    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="➕ Добавить оценку",
        callback_data=GradeCallback(action="add_grade", subject=subject),
    )
    builder.button(
        text="📅 Отметить посещаемость",
        callback_data=GradeCallback(action="add_attendance", subject=subject),
    )
    builder.button(
        text="📊 Статистика",
        callback_data=GradeCallback(action="view_stats", subject=subject),
    )
    builder.button(
        text="⬅️ К списку предметов",
        callback_data=GradeCallback(action="main"),
    )
    builder.button(
        text="🏠 В меню",
        callback_data=MenuCallback(action="home"),
    )
    builder.adjust(2, 1, 1, 1)
    
    return builder.as_markup()


def get_invitation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для системы инвайтов.

    Returns:
        InlineKeyboardMarkup: Клавиатура инвайтов.

    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🎫 Использовать инвайт",
        callback_data=InvitationCallback(action="use"),
    )
    builder.button(
        text="🏠 В меню",
        callback_data=MenuCallback(action="home"),
    )
    builder.adjust(1)
    
    return builder.as_markup()


def get_admin_invitation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для администраторов системы инвайтов.

    Returns:
        InlineKeyboardMarkup: Админская клавиатура инвайтов.

    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="➕ Создать инвайт",
        callback_data=InvitationCallback(action="create"),
    )
    builder.button(
        text="📋 Мои инвайты",
        callback_data=InvitationCallback(action="list"),
    )
    builder.button(
        text="🏠 В меню",
        callback_data=MenuCallback(action="home"),
    )
    builder.adjust(1)
    
    return builder.as_markup()
