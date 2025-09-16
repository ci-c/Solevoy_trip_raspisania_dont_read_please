"""
Утилиты для правильной обработки ошибок.
"""

import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps
from loguru import logger

from app.utils.validation import ValidationError


class BotError(Exception):
    """Базовый класс для ошибок бота."""
    pass


class DatabaseError(BotError):
    """Ошибка базы данных."""
    pass


class APIError(BotError):
    """Ошибка внешнего API."""
    pass


class UserError(BotError):
    """Ошибка пользователя (неправильный ввод и т.д.)."""
    pass


class SecurityError(BotError):
    """Ошибка безопасности."""
    pass


def safe_async_execute(
    error_message: str = "Произошла ошибка",
    log_error: bool = True,
    reraise: bool = False
):
    """
    Декоратор для безопасного выполнения асинхронных функций.
    
    Args:
        error_message: Сообщение об ошибке для пользователя
        log_error: Логировать ли ошибку
        reraise: Пробрасывать ли ошибку дальше
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValidationError as e:
                if log_error:
                    logger.warning(f"Validation error in {func.__name__}: {e}")
                raise UserError(str(e))
            except DatabaseError as e:
                if log_error:
                    logger.error(f"Database error in {func.__name__}: {e}")
                if reraise:
                    raise
                return None
            except APIError as e:
                if log_error:
                    logger.error(f"API error in {func.__name__}: {e}")
                if reraise:
                    raise
                return None
            except SecurityError as e:
                if log_error:
                    logger.error(f"Security error in {func.__name__}: {e}")
                if reraise:
                    raise
                return None
            except Exception as e:
                if log_error:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def handle_database_error(func: Callable) -> Callable:
    """Декоратор для обработки ошибок базы данных."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise DatabaseError(f"Ошибка базы данных: {str(e)}")
    return wrapper


def handle_api_error(func: Callable) -> Callable:
    """Декоратор для обработки ошибок API."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {e}")
            raise APIError(f"Ошибка API: {str(e)}")
    return wrapper


def format_error_for_user(error: Exception) -> str:
    """
    Форматирование ошибки для показа пользователю.
    
    Args:
        error: Исключение
        
    Returns:
        Отформатированное сообщение об ошибке
    """
    if isinstance(error, UserError):
        return f"❌ {str(error)}"
    elif isinstance(error, DatabaseError):
        return "❌ Ошибка базы данных. Попробуйте позже."
    elif isinstance(error, APIError):
        return "❌ Ошибка внешнего сервиса. Попробуйте позже."
    elif isinstance(error, SecurityError):
        return "❌ Ошибка безопасности. Обратитесь к администратору."
    else:
        return "❌ Произошла неожиданная ошибка. Попробуйте позже."


def log_error_context(
    func_name: str,
    user_id: Optional[int] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Логирование контекста ошибки.
    
    Args:
        func_name: Название функции
        user_id: ID пользователя
        additional_data: Дополнительные данные
    """
    context = {
        "function": func_name,
        "user_id": user_id,
    }
    
    if additional_data:
        context.update(additional_data)
    
    logger.error(f"Error context: {context}")


class ErrorHandler:
    """Класс для централизованной обработки ошибок."""
    
    @staticmethod
    async def handle_validation_error(error: ValidationError, message) -> None:
        """Обработка ошибки валидации."""
        await message.answer(f"❌ {str(error)}")
    
    @staticmethod
    async def handle_database_error(error: DatabaseError, message) -> None:
        """Обработка ошибки базы данных."""
        logger.error(f"Database error: {error}")
        await message.answer(
            "❌ Ошибка базы данных. Попробуйте позже или обратитесь к администратору."
        )
    
    @staticmethod
    async def handle_api_error(error: APIError, message) -> None:
        """Обработка ошибки API."""
        logger.error(f"API error: {error}")
        await message.answer(
            "❌ Ошибка внешнего сервиса. Попробуйте позже."
        )
    
    @staticmethod
    async def handle_security_error(error: SecurityError, message) -> None:
        """Обработка ошибки безопасности."""
        logger.error(f"Security error: {error}")
        await message.answer(
            "❌ Ошибка безопасности. Обратитесь к администратору."
        )
    
    @staticmethod
    async def handle_unknown_error(error: Exception, message) -> None:
        """Обработка неизвестной ошибки."""
        logger.error(f"Unknown error: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await message.answer(
            "❌ Произошла неожиданная ошибка. Попробуйте позже или обратитесь к администратору."
        )
