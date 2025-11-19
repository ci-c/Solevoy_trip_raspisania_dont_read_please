"""
Простой и понятный обработчик настройки группы.
"""

from loguru import logger

from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.callbacks import GroupSearchCallback
from app.bot.states import GroupSetupStates
from app.services.group_service import GroupService


async def handle_group_command(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /group."""
    await start_group_setup(message, state)


async def handle_help_command(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /help."""
    try:
        text = (
            "🤖 Помощь по боту СЗГМУ\n\n"
            "Доступные команды:\n"
            "• /start - Главное меню\n"
            "• /group - Настройка группы\n"
            "• /clean - Очистить диалог\n"
            "• /help - Эта справка\n\n"
            "Функции бота:\n"
            "• 📅 Просмотр расписания\n"
            "• 📊 Отслеживание оценок\n"
            "• 📝 Учет посещаемости\n"
            "• 🔔 Уведомления\n\n"
            "Для начала работы настройте группу командой /group"
        )

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error in help handler: {e}")
        await message.answer("❌ Ошибка при показе справки")


async def start_group_setup(message: types.Message, state: FSMContext) -> None:
    """Начать настройку группы - показать список факультетов."""
    try:
        await show_faculty_list(message, state)

    except Exception as e:
        logger.error(f"Error starting group setup: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при настройке группы. Попробуйте позже.")


async def handle_group_setup_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработка callback'ов настройки группы."""
    try:
        logger.info(f"Received callback: {callback.data}")

        # Проверяем что это наш callback
        if not callback.data.startswith("group_setup:"):
            logger.info(f"Ignoring callback: {callback.data}")
            return

        action = (
            callback.data.split(":", 1)[1] if ":" in callback.data else callback.data
        )
        logger.info(f"Action: {action}")

        if action == "select_from_list":
            await show_faculty_list(callback.message, state)
        elif action.startswith("select_faculty:"):
            faculty_id = action.split(":")[1]
            logger.info(f"Processing faculty selection: {faculty_id}")
            await show_faculty_groups(callback, state, faculty_id)
        elif action.startswith("select_group:"):
            group_id = action.split(":")[1]
            await select_group(callback, state, group_id)
        elif action.startswith("schedule:"):
            await handle_schedule_callback(callback, action)
        elif action.startswith("grades:"):
            await handle_grades_callback(callback, action)
        elif action.startswith("settings:"):
            await handle_settings_callback(callback, action)
        elif action == "back_to_start":
            try:
                await callback.message.edit_text(
                    "🏛️ **Настройка группы**\n\n"
                    "Выберите факультет для поиска вашей группы:",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="📚 Выбрать из списка",
                                    callback_data=GroupSearchCallback(
                                        action="select_from_list"
                                    ).pack(),
                                )
                            ]
                        ]
                    ),
                )
            except Exception as edit_error:
                logger.warning(f"Failed to edit message, sending new one: {edit_error}")
                await callback.message.answer(
                    "🏛️ **Настройка группы**\n\n"
                    "Выберите факультет для поиска вашей группы:",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="📚 Выбрать из списка",
                                    callback_data=GroupSearchCallback(
                                        action="select_from_list"
                                    ).pack(),
                                )
                            ]
                        ]
                    ),
                )
            await state.clear()
        else:
            await callback.answer("Неизвестное действие", show_alert=True)

    except Exception as e:
        logger.error(f"Error handling group setup callback: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await callback.answer("❌ Ошибка при обработке запроса", show_alert=True)
        # Ошибка обрабатывается в middleware


async def select_group(
    callback: types.CallbackQuery, state: FSMContext, group_id: str
) -> None:
    """Выбрать группу и завершить настройку."""
    try:
        from app.services.user_service import UserService

        group_service = GroupService()
        group = await group_service.get_group_by_id(int(group_id))

        if not group:
            await callback.answer("❌ Группа не найдена", show_alert=True)
            return

        # Сохраняем группу пользователю
        user_service = UserService()
        user_id = callback.from_user.id

        # Обновляем группу пользователя
        await user_service.update_user_group(user_id, int(group_id))

        # Показываем успех с кнопками
        text = (
            f"🎉 Группа настроена успешно!\n\n"
            f"👥 Ваша группа: {group['name']}\n"
            f"📚 Курс: {group['course']}\n\n"
            f"Выберите действие:"
        )

        # Создаем кнопки для расписания
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="📅 Расписание на сегодня", callback_data="schedule:today"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="📅 Расписание на неделю", callback_data="schedule:week"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="📊 Мои оценки", callback_data="grades:view"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="⚙️ Настройки", callback_data="settings:main"
                    )
                ],
            ]
        )

        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except Exception as edit_error:
            logger.warning(f"Failed to edit message, sending new one: {edit_error}")
            await callback.message.answer(text, reply_markup=keyboard)
        await state.clear()
        await callback.answer("✅ Группа настроена!")

    except Exception as e:
        logger.error(f"Error selecting group: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await callback.answer("❌ Ошибка при выборе группы", show_alert=True)


async def show_faculty_list(message: types.Message, state: FSMContext) -> None:
    """Показать список факультетов."""
    try:
        from app.services.schedule_service import ScheduleService

        schedule_service = ScheduleService()
        logger.info("Attempting to get faculties from database...")
        faculties = await schedule_service.get_available_faculties()

        logger.info(f"Retrieved {len(faculties) if faculties else 0} faculties")

        if not faculties:
            logger.warning("No faculties found in database")
            await message.answer("❌ Факультеты не найдены. Попробуйте позже.")
            return

        text = "🏛️ Выберите факультет:\n\n"

        # Создаем простой список факультетов (ограничиваем до 6)
        faculty_buttons = []
        for i, faculty in enumerate(faculties[:6]):  # Показываем первые 6
            faculty_buttons.append(
                [
                    types.InlineKeyboardButton(
                        text=faculty["name"],
                        callback_data=GroupSearchCallback(
                            action="select_faculty", value=str(faculty["id"])
                        ).pack(),
                    )
                ]
            )

        # Добавляем кнопку "Назад"
        faculty_buttons.append(
            [
                types.InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=GroupSearchCallback(action="back_to_start").pack(),
                )
            ]
        )

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=faculty_buttons)

        try:
            await message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await message.answer(text, reply_markup=keyboard)

        await state.set_state(GroupSetupStates.selecting_faculty)

    except Exception as e:
        logger.error(f"Error showing faculty list: {e}")
        await message.answer("❌ Ошибка при загрузке факультетов. Попробуйте позже.")


async def handle_schedule_callback(callback: types.CallbackQuery, action: str) -> None:
    """Обработка callback'ов расписания."""
    try:
        if action == "schedule:today":
            text = "📅 **Расписание на сегодня**\n\nЗдесь будет расписание на сегодня"
        elif action == "schedule:week":
            text = "📅 **Расписание на неделю**\n\nЗдесь будет расписание на неделю"
        else:
            text = "📅 **Расписание**\n\nВыберите период:"

        try:
            await callback.message.edit_text(text)
        except Exception as edit_error:
            logger.warning(f"Failed to edit message, sending new one: {edit_error}")
            await callback.message.answer(text)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling schedule callback: {e}")
        await callback.answer("❌ Ошибка при получении расписания", show_alert=True)


async def handle_grades_callback(callback: types.CallbackQuery, action: str) -> None:
    """Обработка callback'ов оценок."""
    try:
        if action == "grades:view":
            text = "📊 **Мои оценки**\n\nЗдесь будут ваши оценки"
        else:
            text = "📊 **Оценки**\n\nВыберите действие:"

        try:
            await callback.message.edit_text(text)
        except Exception as edit_error:
            logger.warning(f"Failed to edit message, sending new one: {edit_error}")
            await callback.message.answer(text)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling grades callback: {e}")
        await callback.answer("❌ Ошибка при получении оценок", show_alert=True)


async def handle_settings_callback(callback: types.CallbackQuery, action: str) -> None:
    """Обработка callback'ов настроек."""
    try:
        if action == "settings:main":
            text = "⚙️ **Настройки**\n\nЗдесь будут настройки"
        else:
            text = "⚙️ **Настройки**\n\nВыберите настройку:"

        try:
            await callback.message.edit_text(text)
        except Exception as edit_error:
            logger.warning(f"Failed to edit message, sending new one: {edit_error}")
            await callback.message.answer(text)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling settings callback: {e}")
        await callback.answer("❌ Ошибка при открытии настроек", show_alert=True)


async def register_group_setup_handlers(dp):
    """Регистрация обработчиков настройки группы."""
    # Callback обработчики
    dp.callback_query.register(handle_group_setup_callback)


async def show_faculty_groups(
    callback: types.CallbackQuery, state: FSMContext, faculty_id: str
) -> None:
    """Показать группы выбранного факультета."""
    try:
        logger.info(f"Showing groups for faculty {faculty_id}")
        from app.services.schedule_service import ScheduleService

        # Получаем информацию о факультете
        schedule_service = ScheduleService()
        faculties = await schedule_service.get_available_faculties()

        faculty_name = "Неизвестный факультет"
        for faculty in faculties:
            if str(faculty["id"]) == faculty_id:
                faculty_name = faculty["name"]
                break

        # Получаем группы для факультета
        from app.services.group_service import GroupService

        group_service = GroupService()
        groups = await group_service.get_groups_by_faculty(int(faculty_id))

        logger.info(
            f"Found {len(groups) if groups else 0} groups for faculty {faculty_id}"
        )

        text = f"🏛️ **{faculty_name}**\n\n"

        if groups:
            text += f"📚 **Доступные группы ({len(groups)}):**\n\n"

            # Создаем кнопки для групп
            group_buttons = []
            for group in groups:
                group_buttons.append(
                    [
                        types.InlineKeyboardButton(
                            text=f"{group['name']} (курс {group['course']})",
                            callback_data=GroupSearchCallback(
                                action="select_group", group_id=int(group["id"])
                            ).pack(),
                        )
                    ]
                )

            # Добавляем кнопку "Назад"
            group_buttons.append(
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Назад к факультетам",
                        callback_data=GroupSearchCallback(
                            action="select_from_list"
                        ).pack(),
                    )
                ]
            )

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=group_buttons)
        else:
            text += "❌ Группы не найдены.\n\n"
            text += "Группы создаются автоматически из расписаний.\n"
            text += "Сейчас идет синхронизация с API СЗГМУ..."

            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="🔄 Обновить",
                            callback_data=GroupSearchCallback(
                                action="select_faculty", value=faculty_id
                            ).pack(),
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="⬅️ Назад к факультетам",
                            callback_data=GroupSearchCallback(
                                action="select_from_list"
                            ).pack(),
                        )
                    ],
                ]
            )

        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except Exception as edit_error:
            logger.warning(f"Failed to edit message, sending new one: {edit_error}")
            await callback.message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error showing faculty groups: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await callback.message.answer("❌ Ошибка при загрузке групп. Попробуйте позже.")
