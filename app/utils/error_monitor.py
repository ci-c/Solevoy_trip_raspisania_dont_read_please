# Copyright (c) 2024 SZGMU Bot Project

"""Система мониторинга и предотвращения runtime ошибок."""

import asyncio
import traceback
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, TypeVar

from app.utils.logger import logger

T = TypeVar("T")


@dataclass
class ErrorInfo:
    """Информация об ошибке."""

    timestamp: datetime
    function_name: str
    error_type: str
    error_message: str
    traceback: str
    context: dict[str, Any]


class ErrorMonitor:
    """Монитор ошибок для предотвращения повторных сбоев."""

    def __init__(self, max_errors: int = 100, time_window: int = 300) -> None:
        self.max_errors = max_errors
        self.time_window = timedelta(seconds=time_window)
        self.errors: deque[ErrorInfo] = deque(maxlen=max_errors)
        self.error_counts: defaultdict[str, int] = defaultdict(int)
        self.function_blacklist: set[str] = set()

    def record_error(
        self,
        function_name: str,
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Записать информацию об ошибке."""
        error_info = ErrorInfo(
            timestamp=datetime.now(tz=UTC),
            function_name=function_name,
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            context=context or {},
        )

        self.errors.append(error_info)
        self.error_counts[function_name] += 1

        # Если функция падает слишком часто, добавляем в черный список
        if self.error_counts[function_name] > 5:
            self.function_blacklist.add(function_name)
            logger.warning(
                f"Function {function_name} added to blacklist due to repeated errors",
            )

    def is_function_blacklisted(self, function_name: str) -> bool:
        """Проверить, находится ли функция в черном списке."""
        return function_name in self.function_blacklist

    def get_recent_errors(self, function_name: str | None = None) -> list[ErrorInfo]:
        """Получить недавние ошибки."""
        now = datetime.now(tz=UTC)
        recent_errors = [
            error for error in self.errors if now - error.timestamp <= self.time_window
        ]

        if function_name:
            return [
                error for error in recent_errors if error.function_name == function_name
            ]

        return recent_errors

    def should_skip_function(self, function_name: str) -> bool:
        """Определить, следует ли пропустить выполнение функции."""
        if self.is_function_blacklisted(function_name):
            return True

        recent_errors = self.get_recent_errors(function_name)
        return (
            len(recent_errors) > 3
        )  # Пропускаем если больше 3 ошибок за последние 5 минут


# Глобальный монитор ошибок
error_monitor = ErrorMonitor()


def safe_execute(
    func: Callable[..., T],
    *args,
    default: T | None = None,
    error_message: str = "Operation failed",
    context: dict[str, Any] | None = None,
    **kwargs,
) -> T | None:
    """Безопасное выполнение функции с мониторингом ошибок."""
    function_name = f"{func.__module__}.{func.__name__}"

    # Проверяем, не следует ли пропустить функцию
    if error_monitor.should_skip_function(function_name):
        logger.warning(f"Skipping {function_name} due to recent errors")
        return default

    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_monitor.record_error(function_name, e, context)
        logger.error(f"{error_message} in {function_name}: {e}")
        return default


async def safe_execute_async(
    func: Callable[..., T],
    *args,
    default: T | None = None,
    error_message: str = "Async operation failed",
    context: dict[str, Any] | None = None,
    **kwargs,
) -> T | None:
    """Безопасное выполнение асинхронной функции с мониторингом ошибок."""
    function_name = f"{func.__module__}.{func.__name__}"

    # Проверяем, не следует ли пропустить функцию
    if error_monitor.should_skip_function(function_name):
        logger.warning(f"Skipping {function_name} due to recent errors")
        return default

    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)
    except Exception as e:
        error_monitor.record_error(function_name, e, context)
        logger.error(f"{error_message} in {function_name}: {e}")
        return default


def error_handler(
    default_return: Any = None,
    error_message: str = "Function failed",
    log_traceback: bool = True,
):
    """Декоратор для обработки ошибок в функциях."""

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T | None:
            function_name = f"{func.__module__}.{func.__name__}"

            if error_monitor.should_skip_function(function_name):
                logger.warning(f"Skipping {function_name} due to recent errors")
                return default_return

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_monitor.record_error(
                    function_name, e, {"args": args, "kwargs": kwargs},
                )
                logger.error(f"{error_message} in {function_name}: {e}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")
                return default_return

        return wrapper

    return decorator


def async_error_handler(
    default_return: Any = None,
    error_message: str = "Async function failed",
    log_traceback: bool = True,
):
    """Декоратор для обработки ошибок в асинхронных функциях."""

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T | None:
            function_name = f"{func.__module__}.{func.__name__}"

            if error_monitor.should_skip_function(function_name):
                logger.warning(f"Skipping {function_name} due to recent errors")
                return default_return

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_monitor.record_error(
                    function_name, e, {"args": args, "kwargs": kwargs},
                )
                logger.error(f"{error_message} in {function_name}: {e}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")
                return default_return

        return wrapper

    return decorator


def get_error_stats() -> dict[str, Any]:
    """Получить статистику ошибок."""
    return {
        "total_errors": len(error_monitor.errors),
        "function_error_counts": dict(error_monitor.error_counts),
        "blacklisted_functions": list(error_monitor.function_blacklist),
        "recent_errors_count": len(error_monitor.get_recent_errors()),
    }
