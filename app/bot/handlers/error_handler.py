"""
Обработчик ошибок с уровнями доступа.
"""

from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from ...services.user_service import UserService
from ...utils.logger import get_error_details_for_user, log_security_event
from ...models.user import AccessLevel
from ..keyboards import get_error_keyboard


async def global_error_handler(event: types.ErrorEvent, state: FSMContext) -> None:
    """Глобальный обработчик ошибок."""
    exception = event.exception
    update = event.update

    # Получаем информацию о пользователе
    user_id = None
    chat_id = None

    if update.message:
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
    elif update.callback_query and update.callback_query.from_user:
        user_id = update.callback_query.from_user.id
        chat_id = update.callback_query.message.chat.id

    # Логируем ошибку
    logger.error(
        f"Global error for user {user_id}: {type(exception).__name__}: {exception}"
    )

    if not chat_id:
        return

    try:
        # Получаем информацию о пользователе для определения уровня доступа
        user_service = UserService()
        user = None
        access_level = AccessLevel.GUEST

        if user_id:
            try:
                user = await user_service.get_user_by_telegram_id(user_id)
                if user:
                    access_level = AccessLevel(user.access_level)
            except Exception as e:
                logger.warning(f"Could not get user info for error handler: {e}")

        # Логируем событие безопасности для критических ошибок
        if isinstance(exception, (PermissionError, ValueError, KeyError)):
            log_security_event(
                user_id or 0,
                access_level,
                "CRITICAL_ERROR",
                f"{type(exception).__name__}: {str(exception)[:100]}",
            )

        # Получаем сообщение об ошибке в зависимости от уровня доступа
        error_message = get_error_details_for_user(exception, access_level)

        # Добавляем базовую информацию
        if access_level in [AccessLevel.ADMIN, AccessLevel.TESTER]:
            error_message = f"⚠️ **Системная ошибка**\n\n{error_message}"
        else:
            error_message = f"❌ {error_message}"

        # Отправляем сообщение пользователю
        bot = event.bot

        await bot.send_message(
            chat_id=chat_id,
            text=error_message,
            reply_markup=get_error_keyboard()
            if access_level != AccessLevel.GUEST
            else None,
        )

        # Очищаем состояние при критических ошибках
        if isinstance(exception, (RuntimeError, MemoryError, ConnectionError)):
            await state.clear()
            logger.info(f"Cleared state for user {user_id} due to critical error")

    except Exception as handler_error:
        logger.critical(f"Error in error handler: {handler_error}")

        # Последняя попытка отправить простое сообщение
        try:
            bot = event.bot
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Произошла критическая ошибка. Перезапустите бота командой /start",
            )
        except Exception:
            logger.critical("Could not send any error message to user")


async def handle_timeout_error(message: types.Message, error: Exception):
    """Обработка ошибок тайм-аута."""
    logger.warning(f"Timeout error for user {message.from_user.id}: {error}")

    await message.answer(
        "⏱️ **Превышено время ожидания**\n\n"
        "Операция заняла слишком много времени.\n\n"
        "💡 **Попробуйте:**\n"
        "• Повторить запрос позже\n"
        "• Использовать более простые параметры поиска\n"
        "• Проверить интернет-соединение",
        reply_markup=get_error_keyboard(),
    )


async def handle_api_error(message: types.Message, error: Exception):
    """Обработка ошибок API."""
    logger.error(f"API error for user {message.from_user.id}: {error}")

    await message.answer(
        "🔌 **Ошибка подключения к серверам СЗГМУ**\n\n"
        "Не удается получить данные с официальных серверов.\n\n"
        "💡 **Возможные причины:**\n"
        "• Технические работы на серверах СЗГМУ\n"
        "• Временная перегрузка системы\n"
        "• Проблемы с сетевым подключением\n\n"
        "Попробуйте через несколько минут.",
        reply_markup=get_error_keyboard(),
    )


async def handle_database_error(message: types.Message, error: Exception):
    """Обработка ошибок базы данных."""
    logger.error(f"Database error for user {message.from_user.id}: {error}")

    await message.answer(
        "💾 **Ошибка базы данных**\n\n"
        "Временная проблема с сохранением данных.\n\n"
        "Ваши данные в безопасности. Попробуйте операцию еще раз.",
        reply_markup=get_error_keyboard(),
    )


async def register_error_handler(dp: Dispatcher):
    """Регистрация обработчика ошибок."""
    dp.error.register(global_error_handler, StateFilter("*"))
