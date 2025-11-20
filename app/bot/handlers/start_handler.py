"""Обработчик команды /start и базового меню."""

from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.handlers.group_setup_handler import (
    handle_group_command,
    handle_help_command,
)
from app.bot.keyboards import get_main_menu_reply_keyboard
from app.bot.states import MainMenu
from app.services.user_service import UserService
from app.utils.error_handling import DatabaseError, ErrorHandler
from app.utils.validation import ValidationError, validate_user_input


async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    if not message.from_user:
        logger.info("Unknown user started the bot")
        await message.answer("Error: Could not identify user.")
        return

    # Rate limiting
    from app.utils.rate_limiter import check_rate_limit_manual

    is_allowed, error_message = check_rate_limit_manual(message.from_user.id, "start")
    if not is_allowed:
        await message.answer(f"⏱️ {error_message}")
        return

    logger.info(f"User {message.from_user.id} started the bot")
    await state.clear()

    try:
        user_service = UserService()

        # Валидация входных данных
        username = None
        full_name = None

        if message.from_user.username:
            try:
                username = validate_user_input(
                    "username", message.from_user.username, required=False,
                )
            except ValidationError as e:
                logger.warning(f"Invalid username for user {message.from_user.id}: {e}")

        if message.from_user.full_name:
            try:
                full_name = validate_user_input(
                    "name", message.from_user.full_name, required=False,
                )
            except ValidationError as e:
                logger.warning(
                    f"Invalid full_name for user {message.from_user.id}: {e}",
                )
                full_name = f"User {message.from_user.id}"

        # Получаем или создаем пользователя
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if not user:
            user = await user_service.create_user(
                telegram_id=message.from_user.id,
                telegram_username=username,
                full_name=full_name,
            )
            logger.info(f"Created new user: {user.id}")

        # Обновляем активность
        if user and user.id:
            await user_service.update_user_activity(user.id)

        # Получаем профиль студента
        user_profile = await user_service.get_user_profile(user.id)

        await state.set_state(MainMenu.home)

        # Всегда показываем главное меню
        if user_profile:
            # Пользователь с профилем
            text = (
                f"👋 Добро пожаловать, {user.full_name}!\n\n"
                f"🎓 Ваш профиль: Группа {user_profile.group_id}\n\n"
                f"Я помогу вам с расписанием, оценками и посещаемостью. Выберите действие:"
            )
        else:
            # Новый пользователь
            text = (
                "👋 Добро пожаловать в бот СЗГМУ!\n\n"
                "Я помогу вам с расписанием, оценками и посещаемостью.\n\n"
                "Для начала настройте группу или выберите действие:"
            )

        await message.answer(text, reply_markup=get_main_menu_reply_keyboard())

    except ValidationError as e:
        await ErrorHandler.handle_validation_error(e, message)
    except DatabaseError as e:
        await ErrorHandler.handle_database_error(e, message)
    except Exception as e:
        await ErrorHandler.handle_unknown_error(e, message)


async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /cancel."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    logger.info(f"User {message.from_user.id} cancelled action")
    await state.clear()
    await message.answer("✅ Действие отменено. Чтобы начать заново, введите /start")


async def cmd_clean(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /clean - очистка диалога."""
    try:
        logger.info(f"User {message.from_user.id} requested dialog cleanup")

        # Очищаем состояние
        await state.clear()

        # Отправляем сообщение об очистке
        await message.answer(
            "🧹 Диалог очищен!\n\nВсе предыдущие сообщения скрыты. Выберите действие:",
            reply_markup=get_main_menu_reply_keyboard(),
        )

    except Exception as e:  # noqa: BLE001  - catch all for bot command error handling
        logger.error(f" in cmd_clean: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        await message.answer("❌ Ошибка при очистке диалога")


async def register_start_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков старта."""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(handle_help_command, Command("help"))
    dp.message.register(handle_group_command, Command("group"))
    dp.message.register(cmd_cancel, Command("cancel"))
    dp.message.register(cmd_clean, Command("clean"))
