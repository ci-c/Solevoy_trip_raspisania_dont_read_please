"""Обработчик поиска групп с улучшенной безопасностью."""

import asyncio
from typing import Any

from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import GroupSearchCallback
from app.bot.keyboards import (
    get_error_keyboard,
    get_group_result_keyboard,
    get_group_search_keyboard,
)
from app.bot.states import GroupSearchStates
from app.bot.utils import (
    format_error_message,
    show_loading_spinner,
    validate_group_number,
)
from app.schedule.group_search import GroupSearchService
from app.schedule.semester_detector import SemesterDetector
from app.utils.error_handling import APIError, DatabaseError, ErrorHandler
from app.utils.validation import ValidationError, validate_user_input


async def handle_group_search(
    callback: types.CallbackQuery,
    callback_data: GroupSearchCallback,
    state: FSMContext,
) -> None:
    """Обработчик поиска групп."""
    # Rate limiting
    from app.utils.rate_limiter import check_rate_limit_manual

    is_allowed, error_message = check_rate_limit_manual(
        callback.from_user.id, "callback",
    )
    if not is_allowed:
        await callback.answer(f"⏱️ {error_message}", show_alert=True)
        return

    await callback.answer()
    action = callback_data.action

    if action == "quick_search":
        await state.set_state(GroupSearchStates.entering_group_number)

        try:
            semester_detector = SemesterDetector()
            current_semester = semester_detector.get_semester_display_text()
        except Exception as e:
            logger.warning(f"Failed to get semester info: {e}")
            current_semester = "Осенний семестр 2024/2025"

        await callback.message.edit_text(
            f"🔍 **Быстрый поиск группы**\n\n"
            f"📅 {current_semester}\n\n"
            f"📝 Введите номер группы:\n"
            f"Примеры: `103а`, `204б`, `301в`",
            reply_markup=get_error_keyboard(),
        )

    elif action == "detailed_search":
        await callback.message.edit_text(
            "📊 **Подробный поиск**\n\n"
            "🚧 В разработке...\n"
            "Пока используйте быстрый поиск по номеру группы.",
            reply_markup=get_group_search_keyboard(),
        )

    elif action == "show_schedule":
        week = callback_data.week

        # Получаем данные группы из состояния
        data = await state.get_data()
        group_info = data.get("current_group_info")

        if not group_info:
            await callback.message.edit_text(
                "❌ Данные группы не найдены. Попробуйте поиск заново.",
                reply_markup=get_group_search_keyboard(),
            )
            return

        await show_group_schedule_safe(callback.message, group_info, week, state)

    elif action == "export":
        await callback.answer("🚧 Экспорт в разработке", show_alert=True)


async def process_group_number(message: types.Message, state: FSMContext) -> None:
    """Обработка введенного номера группы."""
    # Rate limiting
    from app.utils.rate_limiter import check_rate_limit_manual

    is_allowed, error_message = check_rate_limit_manual(message.from_user.id, "search")
    if not is_allowed:
        await message.answer(f"⏱️ {error_message}")
        return

    group_number = message.text.strip()

    # Дополнительная валидация ввода
    try:
        group_number = validate_user_input("group_number", group_number, required=True)
    except ValidationError as e:
        await message.answer(
            f"❌ {e}\n\nВведите корректный номер (например: 103а, 204б):",
            reply_markup=get_error_keyboard(),
        )
        return

    # Валидация ввода (существующая)
    is_valid, error_msg = validate_group_number(group_number)
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\nВведите корректный номер (например: 103а, 204б):",
            reply_markup=get_error_keyboard(),
        )
        return

    # Показываем спиннер
    loading_msg = await message.answer("🔍 Начинаю поиск группы...")

    try:
        # Создаем сервис поиска
        group_search_service = GroupSearchService()

        # Запускаем поиск и спиннер параллельно
        search_task = asyncio.create_task(
            group_search_service.search_group_by_number(group_number),
        )
        spinner_task = asyncio.create_task(
            show_loading_spinner(loading_msg, f"Поиск группы {group_number}", 15),
        )

        # Ждем завершения поиска с тайм-аутом
        try:
            groups = await asyncio.wait_for(search_task, timeout=35.0)
            spinner_task.cancel()

        except TimeoutError:
            spinner_task.cancel()
            await loading_msg.edit_text(
                f"⏱️ Поиск группы `{group_number}` занял слишком много времени.\n\n"
                f"Возможные причины:\n"
                f"• Перегрузка серверов СЗГМУ\n"
                f"• Проблемы с сетью\n\n"
                f"Попробуйте позже или проверьте номер группы.",
                reply_markup=get_group_search_keyboard(),
            )
            await state.set_state(GroupSearchStates.choosing_search_type)
            return

        except Exception as search_error:
            spinner_task.cancel()
            logger.error(f"Search task failed: {search_error}")
            raise

        if not groups:
            await loading_msg.edit_text(
                f"❌ Группа `{group_number}` не найдена.\n\n"
                f"🔍 **Возможные причины:**\n"
                f"• Неверный номер группы\n"
                f"• Группа не активна в текущем семестре\n"
                f"• Временная недоступность данных СЗГМУ\n\n"
                f"💡 **Попробуйте:**\n"
                f"• Проверить правильность номера\n"
                f"• Использовать другой формат (103а вместо 103А)\n"
                f"• Повторить поиск позже",
                reply_markup=get_group_search_keyboard(),
            )
            await state.set_state(GroupSearchStates.choosing_search_type)
            return

        # Берем первую найденную группу
        group_info = groups[0]
        logger.info(
            f"Found group: {group_info.number}, speciality: {group_info.speciality}",
        )

        # Сохраняем в состояние
        await state.update_data(current_group_info=group_info)
        await state.set_state(GroupSearchStates.viewing_schedule)

        # Показываем расписание
        await show_group_schedule_safe(loading_msg, group_info, "current", state)

    except ValidationError as e:
        await ErrorHandler.handle_validation_error(e, loading_msg)
    except APIError as e:
        await ErrorHandler.handle_api_error(e, loading_msg)
    except DatabaseError as e:
        await ErrorHandler.handle_database_error(e, loading_msg)
    except Exception as e:
        logger.error(f"Critical error searching group {group_number}: {e}")

        error_message = format_error_message(e, "поиске группы")
        error_message += f"\n\nГруппа: `{group_number}`\n\n"
        error_message += "💡 **Рекомендации:**\n"
        error_message += "• Проверьте интернет-соединение\n"
        error_message += "• Попробуйте другой номер группы\n"
        error_message += "• Повторите попытку через несколько минут"

        try:
            await loading_msg.edit_text(
                error_message, reply_markup=get_group_search_keyboard(),
            )
        except Exception as edit_error:
            logger.error(f"Could not edit error message: {edit_error}")
            await message.answer(
                "❌ Критическая ошибка. Перезапустите бота командой /start",
            )

        await state.set_state(GroupSearchStates.choosing_search_type)


async def show_group_schedule_safe(
    message: Any, group_info: Any, week: str, state: FSMContext,
) -> None:
    """Безопасное отображение расписания группы."""
    try:
        from app.schedule.group_search import GroupSearchService

        group_search_service = GroupSearchService()

        # Определяем номер недели с защитой от ошибок
        try:
            semester_info = (
                group_search_service.semester_detector.get_current_semester_info()
            )
            current_week = semester_info.current_week
        except Exception as e:
            logger.warning(f"Failed to get semester info: {e}, using default week")
            current_week = 1

        # Вычисляем номер недели
        if week == "current":
            week_number = current_week
        elif week == "prev":
            week_number = max(1, current_week - 1)
        elif week == "next":
            week_number = min(20, current_week + 1)
        else:
            week_number = current_week

        logger.info(
            f"Showing schedule for group {group_info.number}, week {week_number}",
        )

        # Форматируем расписание с защитой от ошибок
        try:
            schedule_text = group_search_service.format_group_schedule(
                group_info, week_number,
            )

            if not schedule_text or schedule_text.strip() == "":
                schedule_text = (
                    f"📅 **Расписание группы {group_info.number}**\n\n"
                    f"❌ Нет данных для недели {week_number}.\n\n"
                    f"🔄 Попробуйте другую неделю или повторите поиск."
                )

        except Exception as e:
            logger.error(f"Error formatting schedule: {e}")
            schedule_text = (
                f"📅 **Расписание группы {group_info.number}**\n\n"
                f"❌ Ошибка при обработке данных расписания.\n\n"
                f"Техническая информация: {str(e)[:150]}..."
            )

        # Добавляем дисклеймер
        disclaimer = (
            "⚠️ Информация может быть неактуальной. "
            "Уточняйте расписание в официальных источниках."
        )
        full_text = f"{schedule_text}\n\n{disclaimer}"

        # Обрезаем если слишком длинное
        if len(full_text) > 4000:
            available_length = 4000 - len(disclaimer) - 50
            truncated_schedule = (
                schedule_text[:available_length] + "\n\n... (сокращено)"
            )
            full_text = f"{truncated_schedule}\n\n{disclaimer}"

        # Создаем клавиатуру
        keyboard = get_group_result_keyboard(group_info.number)

        # Отправляем сообщение
        try:
            await message.edit_text(full_text, reply_markup=keyboard)
            logger.info(
                f"Successfully displayed schedule for group {group_info.number}",
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            await message.answer(full_text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Critical error showing group schedule: {e}")

        error_text = (
            f"❌ Критическая ошибка при отображении расписания.\n\n"
            f"Группа: {getattr(group_info, 'number', 'Unknown')}\n"
            f"Ошибка: {str(e)[:200]}...\n\n"
            f"💡 **Попробуйте:**\n"
            f"• Поиск другой группы\n"
            f"• Повторить попытку позже\n"
            f"• Обратиться к администратору"
        )

        try:
            await message.edit_text(
                error_text, reply_markup=get_group_search_keyboard(),
            )
        except Exception:
            await message.answer(
                "❌ Критическая ошибка. Перезапустите бота командой /start",
            )


async def register_group_search_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков поиска групп."""
    dp.callback_query.register(handle_group_search, GroupSearchCallback.filter())

    dp.message.register(
        process_group_number, StateFilter(GroupSearchStates.entering_group_number),
    )
