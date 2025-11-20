# Copyright (c) 2024 SZGMU Bot Project

"""Middleware для глобальной обработки ошибок в боте."""

import traceback
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from loguru import logger

from app.utils.error_monitor import error_monitor


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для обработки всех ошибок в боте."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Обработать событие с глобальной обработкой ошибок."""
        try:
            return await handler(event, data)
        except Exception as e:
            # Получаем информацию о событии
            event_info = self._get_event_info(event)

            # Записываем ошибку в монитор
            error_monitor.record_error(
                function_name=f"handler_{handler.__name__}", error=e, context=event_info,
            )

            # Логируем ошибку с полным traceback
            logger.error(f"Unhandled error in handler {handler.__name__}: {e}")
            logger.error(f"Event info: {event_info}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Пытаемся отправить пользователю понятное сообщение
            await self._handle_user_error(event, e)

            # НЕ пробрасываем ошибку дальше - бот должен продолжать работать
            return None

    def _get_event_info(self, event: TelegramObject) -> dict[str, Any]:
        """Получить информацию о событии для контекста."""
        info = {
            "event_type": type(event).__name__,
            "event_id": getattr(event, "update_id", None),
        }

        # Для сообщений
        if hasattr(event, "message") and event.message:
            info.update(
                {
                    "user_id": event.message.from_user.id
                    if event.message.from_user
                    else None,
                    "chat_id": event.message.chat.id if event.message.chat else None,
                    "message_text": event.message.text[:100]
                    if event.message.text
                    else None,
                },
            )

        # Для callback'ов
        if hasattr(event, "callback_query") and event.callback_query:
            info.update(
                {
                    "user_id": event.callback_query.from_user.id
                    if event.callback_query.from_user
                    else None,
                    "chat_id": event.callback_query.message.chat.id
                    if event.callback_query.message
                    else None,
                    "callback_data": event.callback_query.data[:100]
                    if event.callback_query.data
                    else None,
                },
            )

        return info

    async def _handle_user_error(self, event: TelegramObject, error: Exception) -> None:
        """Обработать ошибку для пользователя."""
        try:
            # Для сообщений
            if hasattr(event, "message") and event.message:
                await event.message.answer(
                    "❌ Произошла ошибка при обработке запроса.\n\n"
                    "Попробуйте позже или обратитесь к администратору.",
                )

            # Для callback'ов
            elif hasattr(event, "callback_query") and event.callback_query:
                await event.callback_query.answer(
                    "❌ Ошибка при обработке запроса", show_alert=True,
                )

                # Пытаемся отредактировать сообщение
                if event.callback_query.message:
                    try:
                        await event.callback_query.message.edit_text(
                            "❌ Произошла ошибка при обработке запроса.\n\n"
                            "Попробуйте позже или обратитесь к администратору.",
                        )
                    except Exception:
                        # Если не можем отредактировать, отправляем новое
                        await event.callback_query.message.answer(
                            "❌ Произошла ошибка при обработке запроса.\n\n"
                            "Попробуйте позже или обратитесь к администратору.",
                        )

        except Exception as user_error:
            # Если даже обработка ошибки для пользователя не удалась
            logger.error(f"Failed to handle user error: {user_error}")
            logger.error(f"Original error: {error}")
