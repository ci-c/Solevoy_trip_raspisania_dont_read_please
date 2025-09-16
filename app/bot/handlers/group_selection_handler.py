"""
Упрощенный обработчик выбора группы без поиска расписаний.
Группа выбирается один раз, расписание берется из БД.
"""

from typing import Dict, Any
from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import GroupSearchCallback
from app.bot.keyboards import (
    get_group_selection_keyboard,
    get_group_confirmation_keyboard,
    get_main_menu_keyboard,
)
from app.bot.states import GroupSearchStates
from app.bot.utils import validate_group_number
from app.services.user_service import UserService
from app.services.group_service import GroupService


def detect_group_info(group_number: str) -> Dict[str, Any]:
    """Автоматическое определение информации о группе по номеру."""
    # Простая логика определения факультета по номеру
    if group_number.startswith(('1', '2')):
        faculty = "ЛФ"  # Лечебный факультет
    elif group_number.startswith(('3', '4')):
        faculty = "ПФ"  # Педиатрический факультет
    elif group_number.startswith(('5', '6')):
        faculty = "МПФ"  # Медико-профилактический факультет
    else:
        faculty = "ЛФ"  # По умолчанию
    
    # Определяем курс по первой цифре
    course = int(group_number[0]) if group_number[0].isdigit() else 1
    
    # Определяем поток по последней букве
    stream = group_number[-1] if group_number[-1].isalpha() else "а"
    
    return {
        "faculty": faculty,
        "course": course,
        "stream": stream,
        "number": group_number
    }


async def handle_group_selection(
    callback: types.CallbackQuery, callback_data: GroupSearchCallback, state: FSMContext
) -> None:
    """Обработчик выбора группы."""
    await callback.answer()
    action = callback_data.action
    user_id = callback.from_user.id

    try:
        if action == "manual_input":
            await state.set_state(GroupSearchStates.entering_group_number)

            await callback.message.edit_text(
                "✍️ **Введите номер вашей группы:**\n\n"
                "Примеры: `103а`, `204б`, `301в`\n\n"
                "📋 Бот автоматически определит:\n"
                "• 🏛️ Факультет\n"
                "• 📚 Курс\n"
                "• 👥 Поток\n\n"
                "После подтверждения группы вы получите доступ к расписанию из базы данных.",
                reply_markup=get_group_selection_keyboard(),
            )

        elif action == "select_faculty":
            faculty = callback_data.value
            await show_faculty_groups(callback.message, faculty, state)

        elif action == "confirm_group":
            group_id = callback_data.group_id
            if group_id:
                await confirm_group_selection(
                    callback.message, int(group_id), user_id, state
                )
            else:
                await callback.message.edit_text(
                    "❌ Ошибка при подтверждении группы. Попробуйте заново.",
                    reply_markup=get_group_selection_keyboard(),
                )

    except Exception as e:
        logger.error(f"Error in group selection handler: {e}")
        try:
            await callback.message.edit_text(
                "❌ Ошибка при выборе группы. Попробуйте позже.",
                reply_markup=get_group_selection_keyboard(),
            )
        except Exception as edit_error:
            logger.error(f"Could not edit message: {edit_error}")
            await callback.message.answer(
                "❌ Ошибка при выборе группы. Попробуйте позже.",
                reply_markup=get_group_selection_keyboard(),
            )


async def process_manual_group_input(message: types.Message, state: FSMContext) -> None:
    """Обработка ручного ввода номера группы."""
    group_number = message.text.strip()

    # Валидация номера группы
    is_valid, error_msg = validate_group_number(group_number)
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\nВведите корректный номер (например: 103а, 204б):",
            reply_markup=get_group_selection_keyboard(),
        )
        return

    try:
        # Нормализуем номер группы
        normalized_group = group_number.lower()

        # Ищем или создаем группу в БД
        group_service = GroupService()
        group_info = await group_service.find_or_create_group({"number": normalized_group})

        if group_info:
            # Автоматически определяем факультет, курс, поток
            detected_info = detect_group_info(normalized_group)

            # Обновляем информацию о группе
            await group_service.update_group_info(group_info["id"], detected_info)

            # Показываем подтверждение
            await show_group_confirmation(message, group_info, detected_info, state)
        else:
            await message.answer(
                f"❌ Не удалось найти или создать группу `{group_number}`.\n\n"
                "Возможные причины:\n"
                "• Неверный формат номера\n"
                "• Группа не существует\n"
                "• Временная ошибка системы\n\n"
                "Попробуйте еще раз:",
                reply_markup=get_group_selection_keyboard(),
            )

    except Exception as e:
        logger.error(f"Error processing manual group input: {e}")
        try:
            await message.edit_text(
                f"❌ Ошибка при обработке номера группы `{group_number}`.\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_group_selection_keyboard(),
            )
        except Exception as edit_error:
            logger.error(f"Could not edit message: {edit_error}")
            await message.answer(
                f"❌ Ошибка при обработке номера группы `{group_number}`.\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_group_selection_keyboard(),
            )


async def show_faculty_groups(
    message: types.Message, faculty: str, state: FSMContext
) -> None:
    """Показать группы выбранного факультета."""
    try:
        group_service = GroupService()
        groups = await group_service.get_groups_by_faculty(faculty)

        if groups:
            # Группируем по курсам
            courses = {}
            for group in groups:
                course = group.get("course", 1)
                if course not in courses:
                    courses[course] = []
                courses[course].append(group)

            text = f"🏛️ **Факультет: {faculty}**\n\n"
            text += "📚 Выберите курс и группу:\n\n"

            for course_num in sorted(courses.keys()):
                text += f"**{course_num} курс:**\n"
                course_groups = sorted(courses[course_num], key=lambda x: x["number"])

                for group in course_groups[:5]:  # Показываем первые 5 групп курса
                    text += f"• {group['number']}\n"

                if len(course_groups) > 5:
                    text += f"• ... и еще {len(course_groups) - 5} групп\n"

                text += "\n"

            text += "✍️ Введите номер вашей группы из списка выше:"

            await state.set_state(GroupSearchStates.entering_group_number)
            
            # Проверяем, изменился ли текст
            current_text = message.text or ""
            if text != current_text:
                try:
                    await message.edit_text(text, reply_markup=get_group_selection_keyboard())
                except Exception as edit_error:
                    logger.error(f"Could not edit message: {edit_error}")
                    await message.answer(text, reply_markup=get_group_selection_keyboard())
            else:
                # Сообщение не изменилось, ничего не делаем
                pass

        else:
            await message.edit_text(
                f"❌ Группы факультета `{faculty}` не найдены.\n\n"
                "✍️ Введите номер группы вручную:",
                reply_markup=get_group_selection_keyboard(),
            )

    except Exception as e:
        logger.error(f"Error showing faculty groups: {e}")
        await message.edit_text(
            "❌ Ошибка при загрузке групп факультета.\n\nПопробуйте ручной ввод:",
            reply_markup=get_group_selection_keyboard(),
        )


async def show_group_confirmation(
    message: types.Message,
    group_info: Dict[str, Any],
    detected_info: Dict[str, Any],
    state: FSMContext,
) -> None:
    """Показать подтверждение выбора группы."""
    try:
        group_number = group_info.get("name", group_info.get("number", "Неизвестно"))
        faculty = detected_info.get("faculty", "Не определен")
        course = detected_info.get("course", "Не определен")
        stream = detected_info.get("stream", "Не определен")
        speciality = detected_info.get("speciality", "Не определена")

        text = (
            f"✅ **Подтвердите выбор группы:**\n\n"
            f"👥 **Группа:** {group_number}\n"
            f"🏛️ **Факультет:** {faculty}\n"
            f"📚 **Курс:** {course}\n"
            f"👥 **Поток:** {stream}\n"
            f"🎓 **Специальность:** {speciality}\n\n"
            f"После подтверждения вы получите доступ к:\n"
            f"• 📅 Персональному расписанию\n"
            f"• 📊 Экспорту в Excel/iCal\n"
            f"• 🔔 Уведомлениям об изменениях\n"
            f"• 📚 Дополнительным сервисам\n\n"
            f"⚠️ Группу можно будет изменить в настройках."
        )

        keyboard = get_group_confirmation_keyboard(group_info)

        # Сохраняем в состояние для подтверждения
        await state.update_data(selected_group=group_info, detected_info=detected_info)
        await state.set_state(GroupSearchStates.confirming_selection)

        try:
            await message.edit_text(text, reply_markup=keyboard)
        except Exception as edit_error:
            logger.error(f"Could not edit message: {edit_error}")
            await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error showing group confirmation: {e}")
        try:
            await message.edit_text(
                "❌ Ошибка при подготовке подтверждения.\n\n"
                "Попробуйте выбрать группу заново:",
                reply_markup=get_group_selection_keyboard(),
            )
        except Exception as edit_error:
            logger.error(f"Could not edit error message: {edit_error}")
            await message.answer(
                "❌ Ошибка при подготовке подтверждения.\n\n"
                "Попробуйте выбрать группу заново:",
                reply_markup=get_group_selection_keyboard(),
            )


async def confirm_group_selection(
    message: types.Message, group_id: int, user_id: int, state: FSMContext
) -> None:
    """Подтвердить выбор группы и создать/обновить профиль пользователя."""
    try:
        # Получаем данные из состояния
        state_data = await state.get_data()
        group_info = state_data.get("selected_group")
        detected_info = state_data.get("detected_info")

        if not group_info:
            await message.edit_text(
                "❌ Данные группы потеряны. Выберите группу заново.",
                reply_markup=get_group_selection_keyboard(),
            )
            return

        # Создаем или обновляем пользователя
        user_service = UserService()
        user_profile = await user_service.create_or_update_user_profile(
            telegram_id=user_id,
            group_id=group_id,
            group_name=group_info["number"],
            faculty=detected_info.get("faculty"),
            course=detected_info.get("course"),
            stream=detected_info.get("stream"),
            speciality=detected_info.get("speciality"),
        )

        if user_profile:
            # Очищаем состояние
            await state.clear()

            # Показываем успешное подтверждение
            await message.edit_text(
                f"✅ **Профиль настроен!**\n\n"
                f"👥 Ваша группа: **{group_info['number']}**\n"
                f"🏛️ Факультет: {detected_info.get('faculty', 'Не определен')}\n\n"
                f"🎉 Теперь вам доступны все функции бота!\n"
                f"📅 Расписание будет обновляться автоматически.",
                reply_markup=get_main_menu_keyboard(user_profile),
            )

            logger.info(f"User {user_id} confirmed group {group_info['number']}")

        else:
            await message.edit_text(
                "❌ Ошибка при сохранении профиля.\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_group_selection_keyboard(),
            )

    except Exception as e:
        logger.error(f"Error confirming group selection: {e}")
        await message.edit_text(
            "❌ Ошибка при подтверждении группы.\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            reply_markup=get_group_selection_keyboard(),
        )




async def register_group_selection_handlers(dp: Dispatcher):
    """Регистрация обработчиков выбора группы."""
    dp.callback_query.register(handle_group_selection, GroupSearchCallback.filter())

    dp.message.register(
        process_manual_group_input, StateFilter(GroupSearchStates.entering_group_number)
    )
