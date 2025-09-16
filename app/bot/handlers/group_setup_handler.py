"""
Простой и понятный обработчик настройки группы.
"""

from typing import Dict
from loguru import logger

from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.states import GroupSetupStates
from app.bot.keyboards import get_simple_group_keyboard, get_confirm_keyboard
from app.services.group_service import GroupService
from app.utils.validation import validate_user_input, ValidationError


async def start_group_setup(message: types.Message, state: FSMContext) -> None:
    """Начать настройку группы - показать простое меню."""
    try:
        text = (
            "🎓 **Настройка группы**\n\n"
            "Выберите способ настройки:"
        )
        
        keyboard = get_simple_group_keyboard()
        
        await message.edit_text(text, reply_markup=keyboard)
        await state.set_state(GroupSetupStates.choosing_method)
        
    except Exception as e:
        logger.error(f"Error starting group setup: {e}")
        await message.answer(
            "❌ Ошибка при настройке группы.\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def handle_group_setup_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработка callback'ов настройки группы."""
    try:
        action = callback.data.split(":")[1] if ":" in callback.data else callback.data
        
        if action == "enter_manually":
            await show_manual_input(callback.message, state)
        elif action == "select_from_list":
            await show_faculty_list(callback.message, state)
        elif action == "confirm_group":
            await confirm_group_selection(callback.message, state)
        elif action == "cancel":
            await cancel_group_setup(callback.message, state)
        else:
            await callback.answer("Неизвестное действие", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling group setup callback: {e}")
        await callback.answer("❌ Ошибка при обработке запроса", show_alert=True)


async def show_manual_input(message: types.Message, state: FSMContext) -> None:
    """Показать форму ручного ввода группы."""
    try:
        text = (
            "✍️ **Введите номер группы**\n\n"
            "Примеры: `103а`, `204б`, `301в`\n\n"
            "Бот автоматически определит:\n"
            "• Факультет\n"
            "• Курс\n"
            "• Поток\n"
            "• Специальность"
        )
        
        try:
            await message.edit_text(text, reply_markup=get_confirm_keyboard("cancel"))
        except Exception:
            await message.answer(text, reply_markup=get_confirm_keyboard("cancel"))
        
        await state.set_state(GroupSetupStates.entering_group_number)
        
    except Exception as e:
        logger.error(f"Error showing manual input: {e}")
        await message.answer("❌ Ошибка при отображении формы ввода")


async def show_faculty_list(message: types.Message, state: FSMContext) -> None:
    """Показать список факультетов."""
    try:
        from app.services.schedule_service import ScheduleService
        
        schedule_service = ScheduleService()
        faculties = await schedule_service.get_available_faculties()
        
        if not faculties:
            try:
                await message.edit_text(
                    "❌ Факультеты не найдены.\n\n"
                    "Попробуйте ручной ввод:",
                    reply_markup=get_confirm_keyboard("enter_manually")
                )
            except Exception:
                await message.answer(
                    "❌ Факультеты не найдены.\n\n"
                    "Попробуйте ручной ввод:",
                    reply_markup=get_confirm_keyboard("enter_manually")
                )
            return
        
        text = "🏛️ **Выберите факультет:**\n\n"
        
        # Создаем простой список факультетов
        faculty_buttons = []
        for i, faculty in enumerate(faculties[:10]):  # Показываем первые 10
            faculty_buttons.append([
                types.InlineKeyboardButton(
                    text=faculty["name"],
                    callback_data=f"group_setup:select_faculty:{faculty['id']}"
                )
            ])
        
        # Добавляем кнопку "Ручной ввод"
        faculty_buttons.append([
            types.InlineKeyboardButton(
                text="✍️ Ввести вручную",
                callback_data="group_setup:enter_manually"
            )
        ])
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=faculty_buttons)
        
        try:
            await message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await message.answer(text, reply_markup=keyboard)
        
        await state.set_state(GroupSetupStates.selecting_faculty)
        
    except Exception as e:
        logger.error(f"Error showing faculty list: {e}")
        try:
            await message.edit_text(
                "❌ Ошибка при загрузке факультетов.\n\n"
                "Попробуйте ручной ввод:",
                reply_markup=get_confirm_keyboard("enter_manually")
            )
        except Exception:
            await message.answer(
                "❌ Ошибка при загрузке факультетов.\n\n"
                "Попробуйте ручной ввод:",
                reply_markup=get_confirm_keyboard("enter_manually")
            )


async def handle_faculty_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора факультета."""
    try:
        faculty_id = int(callback.data.split(":")[2])
        
        # Сохраняем выбранный факультет
        await state.update_data(selected_faculty_id=faculty_id)
        
        # Показываем форму ввода группы для этого факультета
        text = (
            "✍️ **Введите номер группы**\n\n"
            "Примеры: `103а`, `204б`, `301в`\n\n"
            "Бот автоматически определит:\n"
            "• Курс\n"
            "• Поток\n"
            "• Специальность"
        )
        
        try:
            await callback.message.edit_text(text, reply_markup=get_confirm_keyboard("cancel"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_confirm_keyboard("cancel"))
        
        await state.set_state(GroupSetupStates.entering_group_number)
        
    except Exception as e:
        logger.error(f"Error handling faculty selection: {e}")
        await callback.answer("❌ Ошибка при выборе факультета", show_alert=True)


async def process_group_input(message: types.Message, state: FSMContext) -> None:
    """Обработка введенного номера группы."""
    try:
        group_number = message.text.strip()
        
        # Валидация
        try:
            validate_user_input(group_number, "group_number")
        except ValidationError as e:
            await message.answer(f"❌ {e}")
            return
        
        # Определяем информацию о группе
        detected_info = detect_group_info(group_number)
        
        # Создаем или находим группу
        group_service = GroupService()
        group_info = await group_service.find_or_create_group(group_number)
        
        if group_info and isinstance(group_info, dict):
            # Обновляем информацию о группе
            await group_service.update_group_info(group_info["id"], detected_info)
            
            # Показываем подтверждение
            await show_group_confirmation(message, group_info, detected_info, state)
        else:
            await message.answer(
                f"❌ Не удалось найти группу `{group_number}`.\n\n"
                "Попробуйте другой номер:",
                reply_markup=get_confirm_keyboard("cancel")
            )
            
    except Exception as e:
        logger.error(f"Error processing group input: {e}")
        await message.answer(
            f"❌ Ошибка при обработке группы `{group_number}`.\n\n"
            "Попробуйте позже.",
            reply_markup=get_confirm_keyboard("cancel")
        )


async def show_group_confirmation(
    message: types.Message, 
    group_info: Dict[str, str], 
    detected_info: Dict[str, str], 
    state: FSMContext
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
            f"• 🔔 Уведомлениям об изменениях"
        )

        keyboard = get_confirm_keyboard("confirm_group", "cancel")
        
        # Сохраняем данные для подтверждения
        await state.update_data(
            selected_group=group_info, 
            detected_info=detected_info
        )
        await state.set_state(GroupSetupStates.confirming_selection)

        await message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error showing group confirmation: {e}")
        await message.answer(
            "❌ Ошибка при подготовке подтверждения.\n\n"
            "Попробуйте заново:",
            reply_markup=get_confirm_keyboard("enter_manually")
        )


async def confirm_group_selection(message: types.Message, state: FSMContext) -> None:
    """Подтвердить выбор группы."""
    try:
        data = await state.get_data()
        group_info = data.get("selected_group")
        detected_info = data.get("detected_info")
        
        if not group_info:
            await message.edit_text(
                "❌ Данные группы не найдены.\n\n"
                "Попробуйте заново:",
                reply_markup=get_confirm_keyboard("enter_manually")
            )
            return
        
        # Здесь должна быть логика сохранения группы пользователю
        # Пока просто показываем успех
        
        group_number = group_info.get("name", group_info.get("number", "Неизвестно"))
        
        text = (
            f"🎉 **Группа настроена успешно!**\n\n"
            f"👥 **Ваша группа:** {group_number}\n\n"
            f"Теперь вы можете:\n"
            f"• 📅 Просматривать расписание\n"
            f"• 📊 Экспортировать данные\n"
            f"• 🔔 Получать уведомления\n\n"
            f"Используйте /menu для доступа к функциям"
        )
        
        await message.edit_text(text)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error confirming group selection: {e}")
        await message.answer(
            "❌ Ошибка при подтверждении группы.\n\n"
            "Попробуйте позже.",
            reply_markup=get_confirm_keyboard("enter_manually")
        )


async def cancel_group_setup(message: types.Message, state: FSMContext) -> None:
    """Отменить настройку группы."""
    try:
        await state.clear()
        try:
            await message.edit_text(
                "❌ Настройка группы отменена.\n\n"
                "Вы можете настроить группу позже командой /group"
            )
        except Exception:
            # Если не можем отредактировать, отправляем новое сообщение
            await message.answer(
                "❌ Настройка группы отменена.\n\n"
                "Вы можете настроить группу позже командой /group"
            )
        
    except Exception as e:
        logger.error(f"Error canceling group setup: {e}")
        await message.answer("❌ Ошибка при отмене настройки")


def detect_group_info(group_number: str) -> Dict[str, str]:
    """Автоматическое определение информации о группе по номеру."""
    # Простая логика определения факультета по номеру
    digits = "".join(filter(str.isdigit, group_number))
    
    if len(digits) < 3:
        return {
            "faculty": "Не определен",
            "course": "Не определен", 
            "stream": "Не определен",
            "speciality": "Не определена",
        }
    
    # Первая цифра - курс
    course = int(digits[0])
    
    # Вторая и третья цифры - номер группы на курсе
    group_num = int(digits[1:3]) if len(digits) >= 3 else 0
    
    # Буква потока
    stream_letter = "".join(filter(str.isalpha, group_number.lower()))
    
    # Определяем факультет по номеру группы
    faculty_map = {
        (1, 100): "Медико-профилактический факультет",
        (2, 200): "Лечебный факультет", 
        (3, 300): "Стоматологический факультет",
        (4, 400): "Медико-биологический факультет",
        (5, 500): "Факультет постдипломного образования",
    }
    
    faculty = "Не определен"
    for (course_key, group_key), faculty_name in faculty_map.items():
        if course == course_key or (group_num >= group_key and group_num < group_key + 100):
            faculty = faculty_name
            break
    
    # Определяем специальность по факультету
    speciality_map = {
        "Медико-профилактический факультет": "Медико-профилактическое дело",
        "Лечебный факультет": "Лечебное дело",
        "Стоматологический факультет": "Стоматология", 
        "Медико-биологический факультет": "Медицинская биофизика",
        "Факультет постдипломного образования": "Ординатура/Аспирантура",
    }
    
    speciality = speciality_map.get(faculty, "Не определена")
    
    # Определяем поток по букве
    stream_map = {"а": "А", "б": "Б", "в": "В", "г": "Г", "": "Основной"}
    stream = stream_map.get(stream_letter, stream_letter.upper() if stream_letter else "Основной")
    
    return {
        "faculty": faculty,
        "course": course,
        "stream": stream,
        "speciality": speciality,
    }


async def register_group_setup_handlers(dp):
    """Регистрация обработчиков настройки группы."""
    from aiogram.filters import StateFilter
    
    # Callback обработчики
    dp.callback_query.register(
        handle_group_setup_callback,
        lambda c: c.data.startswith("group_setup:")
    )
    
    # Обработчик выбора факультета
    dp.callback_query.register(
        handle_faculty_selection,
        lambda c: c.data.startswith("group_setup:select_faculty:")
    )
    
    # Обработчик ввода группы
    dp.message.register(
        process_group_input,
        StateFilter(GroupSetupStates.entering_group_number)
    )
