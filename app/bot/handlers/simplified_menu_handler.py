"""Упрощенный обработчик главного меню без поиска расписаний."""


from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import MenuCallback
from app.bot.keyboards import get_group_selection_keyboard, get_main_menu_keyboard
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserService


async def handle_menu_action(
    callback: types.CallbackQuery, callback_data: MenuCallback, state: FSMContext,
) -> None:
    """Обработчик действий главного меню."""
    await callback.answer()
    action = callback_data.action
    user_id = callback.from_user.id

    try:
        user_service = UserService()
        user_profile = await user_service.get_user_profile(user_id)

        if action == "home":
            await show_main_menu(callback.message, user_profile)

        elif action == "select_group":
            await show_group_selection(callback.message, state)

        elif action == "my_schedule":
            if user_profile:
                await show_user_schedule(callback.message, user_profile, state)
            else:
                await callback.message.edit_text(
                    "❌ Сначала настройте профиль - выберите группу!",
                    reply_markup=get_main_menu_keyboard(),
                )

        elif action == "export":
            if user_profile:
                await handle_export_schedule(callback.message, user_profile, state)
            else:
                await callback.message.edit_text(
                    "❌ Сначала настройте профиль - выберите группу!",
                    reply_markup=get_main_menu_keyboard(),
                )

        elif action == "settings":
            await show_settings_menu(callback.message, user_profile)

        else:
            # Заглушки для других функций
            await callback.message.edit_text(
                f"🚧 Функция '{action}' в разработке.\n\n"
                "Основные функции:\n"
                "• Просмотр расписания\n"
                "• Экспорт в Excel/iCal\n"
                "• Настройки профиля",
                reply_markup=get_main_menu_keyboard(user_profile),
            )

    except Exception as e:
        logger.error(f"Error handling menu action {action}: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при обработке запроса. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def show_main_menu(
    message: types.Message, user_profile: dict | None = None,
) -> None:
    """Показать главное меню."""
    if user_profile:
        group_info = user_profile.get("group_name", "Не указана")
        text = (
            f"🎓 **Добро пожаловать!**\n\n"
            f"👤 Ваша группа: **{group_info}**\n\n"
            f"📚 Доступные функции:"
        )
    else:
        text = (
            "👋 **Добро пожаловать в бот расписаний СЗГМУ!**\n\n"
            "🚀 Для начала работы выберите вашу группу.\n"
            "Бот автоматически определит факультет, курс и поток."
        )

    keyboard = get_main_menu_keyboard(user_profile)

    try:
        await message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await message.answer(text, reply_markup=keyboard)


async def show_group_selection(message: types.Message, state: FSMContext) -> None:
    """Показать меню выбора группы."""
    try:
        # Получаем список доступных факультетов из БД
        from app.services.schedule_service import ScheduleService

        schedule_service = ScheduleService()
        faculties_data = await schedule_service.get_available_faculties()
        faculties = [faculty["name"] for faculty in faculties_data]

        if faculties:
            text = (
                "🏛️ **Выберите факультет:**\n\n"
                "Бот автоматически определит курс и поток по номеру группы."
            )
            keyboard = get_group_selection_keyboard(faculties)
        else:
            text = (
                "✍️ **Введите номер вашей группы:**\n\n"
                "Примеры: `103а`, `204б`, `301в`\n\n"
                "Бот автоматически определит:\n"
                "• Факультет\n"
                "• Курс\n"
                "• Поток"
            )
            keyboard = get_group_selection_keyboard()

        await message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error showing group selection: {e}")
        await message.edit_text(
            "❌ Ошибка при загрузке списка групп.\n\n✍️ Введите номер группы вручную:",
            reply_markup=get_group_selection_keyboard(),
        )


async def show_user_schedule(
    message: types.Message, user_profile: dict, state: FSMContext,
) -> None:
    """Показать расписание пользователя из БД."""
    try:
        schedule_service = ScheduleService()
        user_id = user_profile["user_id"]

        # Получаем расписание на текущую неделю
        from datetime import date, timedelta

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        schedule = await schedule_service.get_user_schedule(
            user_id, week_start, week_end,
        )

        if schedule:
            # Форматируем расписание
            schedule_text = format_user_schedule(schedule, user_profile["group_name"])
        else:
            schedule_text = (
                f"📅 **Расписание группы {user_profile['group_name']}**\n\n"
                "❌ Нет данных на текущую неделю.\n\n"
                "🔄 Расписание обновляется автоматически.\n"
                "Если данных долго нет - обратитесь к администратору."
            )

        # Добавляем дисклеймер
        disclaimer = (
            "⚠️ Информация может быть неактуальной. "
            "Уточняйте расписание в официальных источниках."
        )
        full_text = f"{schedule_text}\n\n{disclaimer}"

        await message.edit_text(
            full_text, reply_markup=get_main_menu_keyboard(user_profile),
        )

    except Exception as e:
        logger.error(f"Error showing user schedule: {e}")
        await message.edit_text(
            "❌ Ошибка при получении расписания.\n\n"
            "Попробуйте позже или обновите профиль.",
            reply_markup=get_main_menu_keyboard(user_profile),
        )


async def handle_export_schedule(
    message: types.Message, user_profile: dict, state: FSMContext,
) -> None:
    """Обработка экспорта расписания."""
    await message.edit_text(
        f"📊 **Экспорт расписания группы {user_profile['group_name']}**\n\n"
        "🚧 Функция экспорта в разработке.\n\n"
        "Планируются форматы:\n"
        "• 📑 Excel (.xlsx)\n"
        "• 📅 iCalendar (.ics)\n"
        "• 📱 Google Calendar\n"
        "• 🔗 Публичная ссылка",
        reply_markup=get_main_menu_keyboard(user_profile),
    )


async def show_settings_menu(
    message: types.Message, user_profile: dict | None,
) -> None:
    """Показать меню настроек."""
    if user_profile:
        text = (
            f"⚙️ **Настройки профиля**\n\n"
            f"👤 Группа: {user_profile['group_name']}\n"
            f"🏛️ Факультет: {user_profile.get('faculty', 'Не указан')}\n"
            f"📚 Курс: {user_profile.get('course', 'Не указан')}\n\n"
            "🚧 Редактирование профиля в разработке."
        )
    else:
        text = "❌ Сначала настройте профиль - выберите группу!"

    await message.edit_text(text, reply_markup=get_main_menu_keyboard(user_profile))


def format_user_schedule(schedule: list[dict], group_name: str) -> str:
    """Форматировать расписание пользователя."""
    if not schedule:
        return f"📅 **Расписание группы {group_name}**\n\nНет занятий на эту неделю."

    text = f"📅 **Расписание группы {group_name}**\n\n"

    # Группируем по дням
    days_schedule = {}
    for lesson in schedule:
        day = lesson["day_of_week"]
        if day not in days_schedule:
            days_schedule[day] = []
        days_schedule[day].append(lesson)

    # Названия дней недели
    day_names = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
        7: "Воскресенье",
    }

    for day_num in sorted(days_schedule.keys()):
        day_name = day_names.get(day_num, f"День {day_num}")
        text += f"📘 **{day_name}**\n"

        for lesson in sorted(days_schedule[day_num], key=lambda x: x["lesson_number"]):
            time_info = ""
            if lesson.get("start_time") and lesson.get("end_time"):
                time_info = f" ({lesson['start_time']}-{lesson['end_time']})"

            room_info = ""
            if lesson.get("room_number"):
                room_info = f" • {lesson['room_number']}"
                if lesson.get("building"):
                    room_info += f" ({lesson['building']})"

            teacher_name = lesson.get(
                'teacher_name', 'Преподаватель не указан'
            )
            text += (
                f"{lesson['lesson_number']}.{time_info} "
                f"**{lesson['subject_name']}**\n"
                f"   {lesson.get('lesson_type', 'Занятие')} • "
                f"{teacher_name}{room_info}\n"
            )

        text += "\n"

    return text.strip()


async def register_simplified_menu_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков упрощенного меню."""
    dp.callback_query.register(handle_menu_action, MenuCallback.filter())
