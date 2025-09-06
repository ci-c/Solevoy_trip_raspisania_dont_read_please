"""
Система логирования с ротацией и уровнями доступа.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from ..models.user import AccessLevel


class LoggingConfig:
    """Конфигурация логирования."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def setup_logging(self):
        """Настроить систему логирования."""
        # Удаляем стандартный обработчик
        logger.remove()

        # Консольный вывод для разработки
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level="INFO",
            colorize=True,
        )

        # Общий лог файл с ротацией
        logger.add(
            self.logs_dir / "bot.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
        )

        # Лог ошибок
        logger.add(
            self.logs_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="50 MB",
            retention="60 days",
            compression="zip",
            encoding="utf-8",
        )

        # Лог действий пользователей
        logger.add(
            self.logs_dir / "user_actions.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[user_id]} | {extra[action]} | {message}",
            level="INFO",
            rotation="200 MB",
            retention="90 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: "user_action" in record["extra"],
        )

        # Лог API запросов
        logger.add(
            self.logs_dir / "api_requests.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[request_type]} | {extra[duration_ms]}ms | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="14 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: "api_request" in record["extra"],
        )

        # Лог безопасности и доступа
        logger.add(
            self.logs_dir / "security.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[user_id]} | {extra[access_level]} | {message}",
            level="WARNING",
            rotation="50 MB",
            retention="365 days",  # Долгое хранение для аудита
            compression="zip",
            encoding="utf-8",
            filter=lambda record: "security" in record["extra"],
        )


def log_user_action(user_id: int, action: str, details: str = ""):
    """Логирование действий пользователя."""
    logger.bind(user_action=True, user_id=user_id, action=action).info(details)


def log_api_request(request_type: str, duration_ms: int, details: str = ""):
    """Логирование API запросов."""
    logger.bind(
        api_request=True, request_type=request_type, duration_ms=duration_ms
    ).debug(details)


def log_security_event(
    user_id: int, access_level: AccessLevel, event: str, details: str = ""
):
    """Логирование событий безопасности."""
    logger.bind(
        security=True, user_id=user_id, access_level=access_level.value
    ).warning(f"{event}: {details}")


def get_error_details_for_user(error: Exception, user_access_level: AccessLevel) -> str:
    """Получить детали ошибки в зависимости от уровня доступа пользователя."""
    base_message = "Произошла ошибка в работе бота"

    if user_access_level in [AccessLevel.ADMIN, AccessLevel.TESTER]:
        # Расширенная информация для админов и тестеров
        error_type = type(error).__name__
        error_msg = str(error)

        return (
            f"🔧 **Техническая информация:**\n"
            f"• Тип ошибки: `{error_type}`\n"
            f"• Сообщение: `{error_msg[:300]}{'...' if len(error_msg) > 300 else ''}`\n"
            f"• Время: `{logger._core.get_time().isoformat()}`\n\n"
            f"💡 Данная информация доступна только администраторам."
        )

    elif user_access_level == AccessLevel.BASIC:
        # Базовая информация для обычных пользователей
        return (
            f"{base_message}. Попробуйте позже или обратитесь к администратору.\n\n"
            f"Если проблема повторяется, сообщите об этом в поддержку."
        )

    else:  # GUEST
        # Минимальная информация для гостей
        return f"{base_message}. Попробуйте позже."


def log_bot_startup():
    """Логирование запуска бота."""
    logger.info("=" * 50)
    logger.info("SZGMU Schedule Bot is starting up")
    logger.info("=" * 50)


def log_bot_shutdown():
    """Логирование остановки бота."""
    logger.info("=" * 50)
    logger.info("SZGMU Schedule Bot is shutting down")
    logger.info("=" * 50)
