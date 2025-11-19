# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Обработчики главного меню бота.

Зона ответственности:
- Обработка команд главного меню (ReplyKeyboardMarkup)
- Навигация между разделами бота
- Обработка неизвестных команд и сообщений
- Управление состоянием пользователя
"""

from aiogram import types
from loguru import logger

from app.bot.keyboards import get_main_menu_reply_keyboard


async def handle_schedule_command(message: types.Message) -> None:
    """Обработка команды 'Расписание'."""
    try:
        # Показываем что запрос получен
        await message.answer("⏳ Загружаю расписание...")

        text = (
            "📅 Расписание\n\n"
            "Выберите период:\n"
            "• Сегодня\n"
            "• Завтра\n"
            "• Эта неделя\n"
            "• Следующая неделя\n\n"
            "Или введите дату в формате ДД.ММ"
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling schedule command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при получении расписания")


async def handle_grades_command(message: types.Message) -> None:
    """Обработка команды 'Оценки'."""
    try:
        text = (
            "📊 **Оценки**\n\n"
            "• Просмотр оценок по предметам\n"
            "• Добавление новых оценок\n"
            "• Статистика успеваемости\n"
            "• КНЛ/КНС баллы\n\n"
            "Выберите действие:"
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling grades command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при получении оценок")


async def handle_attendance_command(message: types.Message) -> None:
    """Обработка команды 'Посещаемость'."""
    try:
        text = (
            "📝 **Посещаемость**\n\n"
            "• Отметить присутствие\n"
            "• Просмотр статистики\n"
            "• Заявления на пропуски\n\n"
            "Выберите действие:"
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling attendance command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при работе с посещаемостью")


async def handle_settings_command(message: types.Message) -> None:
    """Обработка команды 'Настройки'."""
    try:
        text = (
            "⚙️ **Настройки**\n\n"
            "• Сменить группу\n"
            "• Уведомления\n"
            "• Язык интерфейса\n"
            "• Экспорт данных\n\n"
            "Выберите настройку:"
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling settings command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при открытии настроек")


async def handle_group_command_menu(message: types.Message) -> None:
    """Обработка команды 'Группа' из главного меню."""
    try:
        from app.bot.keyboards import get_simple_group_keyboard

        text = "📚 Настройка группы\n\nВыберите способ настройки:"

        await message.answer(text, reply_markup=get_simple_group_keyboard())

    except Exception as e:
        logger.error(f"Error handling group command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при работе с группой")


async def handle_notifications_command(message: types.Message) -> None:
    """Обработка команды 'Уведомления'."""
    try:
        text = (
            "🔔 **Уведомления**\n\n"
            "• Настройка напоминаний\n"
            "• Уведомления о занятиях\n"
            "• Уведомления об оценках\n\n"
            "Выберите тип уведомлений:"
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling notifications command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при настройке уведомлений")


async def handle_help_command_menu(message: types.Message) -> None:
    """Обработка команды 'Помощь' из главного меню."""
    try:
        text = (
            "❓ Помощь\n\n"
            "Основные команды:\n"
            "• /start - Главное меню\n"
            "• /group - Настройка группы\n"
            "• /clean - Очистить диалог\n"
            "• /help - Эта справка\n\n"
            "Функции бота:\n"
            "• 📅 Просмотр расписания\n"
            "• 📊 Отслеживание оценок\n"
            "• 📝 Учет посещаемости\n"
            "• 🔔 Уведомления\n\n"
            "Поддержка:\n"
            "Если возникли проблемы, обратитесь к администратору."
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling help command: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при получении справки")


async def handle_unknown_message(message: types.Message) -> None:
    """Обработчик по умолчанию для неизвестных сообщений."""
    try:
        logger.info(f"Unknown message from user {message.from_user.id}: {message.text}")

        text = (
            "🤔 Не понимаю эту команду.\n\n"
            "Используйте кнопки меню ниже или команды:\n"
            "• /start - Главное меню\n"
            "• /help - Справка\n\n"
            "Если проблема повторяется, обратитесь в поддержку."
        )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except Exception as e:
        logger.error(f"Error handling unknown message: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


async def register_main_menu_handlers(dp) -> None:
    """Регистрация обработчиков главного меню."""
    # Обработчики текстовых команд из ReplyKeyboard
    dp.message.register(handle_schedule_command, lambda m: m.text == "📅 Расписание")
    dp.message.register(handle_grades_command, lambda m: m.text == "📊 Оценки")
    dp.message.register(
        handle_attendance_command, lambda m: m.text == "📝 Посещаемость"
    )
    dp.message.register(handle_settings_command, lambda m: m.text == "⚙️ Настройки")
    dp.message.register(handle_group_command_menu, lambda m: m.text == "📚 Группа")
    dp.message.register(
        handle_notifications_command, lambda m: m.text == "🔔 Уведомления"
    )
    dp.message.register(handle_help_command_menu, lambda m: m.text == "❓ Помощь")

    # Обработчик по умолчанию для неизвестных сообщений
    dp.message.register(handle_unknown_message)
