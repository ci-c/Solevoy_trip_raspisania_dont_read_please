"""
Обработчик команды /start и базового меню.
"""

from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.keyboards import get_main_menu_keyboard
from app.bot.states import MainMenu
from app.services.user_service import UserService


async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    if not message.from_user:
        logger.info("Unknown user started the bot")
        await message.answer("Error: Could not identify user.")
        return

    logger.info(f"User {message.from_user.id} started the bot")
    await state.clear()

    try:
        user_service = UserService()

        # Получаем или создаем пользователя
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if not user:
            user = await user_service.create_user(
                telegram_id=message.from_user.id,
                telegram_username=message.from_user.username,
                full_name=message.from_user.full_name,
            )
            logger.info(f"Created new user: {user.id}")

        # Обновляем активность
        await user_service.update_user_activity(user.id)

        # Получаем профиль студента
        user_profile = await user_service.get_user_profile(user.id)

        await state.set_state(MainMenu.home)

        if user_profile:
            # Пользователь с профилем
            await message.answer(
                f"👋 Добро пожаловать, {user.full_name}!\n\n"
                f"🎓 Ваш профиль: Группа {user_profile.group_id}\n\n"
                f"Что вас интересует?",
                reply_markup=get_main_menu_keyboard(user),
            )
        else:
            # Новый пользователь
            await message.answer(
                "👋 Добро пожаловать в СЗГМУ Schedule Bot!\n\n"
                "🤖 Я помогу вам с расписанием занятий, оценками и документами.\n\n"
                "Для начала настройте свой профиль или воспользуйтесь поиском:",
                reply_markup=get_main_menu_keyboard(),
            )

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при запуске бота.\n\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )


async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    """Обработчик команды /cancel."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    logger.info(f"User {message.from_user.id} cancelled action")
    await state.clear()
    await message.answer("✅ Действие отменено. Чтобы начать заново, введите /start")


async def register_start_handlers(dp: Dispatcher):
    """Регистрация обработчиков старта."""
    dp.message.register(cmd_start, Command("start", "help"))
    dp.message.register(cmd_cancel, Command("cancel"))
