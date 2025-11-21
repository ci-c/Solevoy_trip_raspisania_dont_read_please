"""Утилиты для бота."""

import asyncio

from aiogram.types import Message
from loguru import logger


async def show_loading_spinner(
    message: Message, text_prefix: str = "⏳ Загрузка", duration: int = 10,
) -> None:
    """Показать спиннер во время загрузки."""
    spinner_frames = [
        "🕐",
        "🕑",
        "🕒",
        "🕓",
        "🕔",
        "🕕",
        "🕖",
        "🕗",
        "🕘",
        "🕙",
        "🕚",
        "🕛",
    ]

    steps = [
        "Подключение к API...",
        "Поиск в базе расписаний...",
        "Обработка данных...",
        "Объединение лекций и семинаров...",
        "Завершение...",
    ]

    frames_per_step = max(1, duration // len(steps))

    for step_idx, step_text in enumerate(steps):
        for i in range(frames_per_step):
            frame = spinner_frames[i % len(spinner_frames)]
            try:
                progress = f"{step_idx + 1}/{len(steps)}"
                await message.edit_text(
                    f"{frame} {text_prefix}\n📊 {progress} | {step_text}",
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Could not update spinner: {e}")
                break


def validate_group_number(group_number: str) -> tuple[bool, str]:
    """Валидировать номер группы."""
    if not group_number:
        return False, "Номер группы не может быть пустым"

    if len(group_number) > 10:
        return False, "Номер группы слишком длинный"

    if not any(c.isdigit() for c in group_number):
        return False, "Номер группы должен содержать цифры"

    return True, ""


def truncate_text(
    text: str, max_length: int = 4000, suffix: str = "... (сокращено)",
) -> str:
    """Обрезать текст до максимальной длины."""
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_error_message(error: Exception, context: str = "") -> str:
    """Отформатировать сообщение об ошибке для пользователя."""
    error_str = str(error)[:200]

    message = "❌ Произошла ошибка"
    if context:
        message += f" при {context}"

    message += f".\n\nТехническая информация: {error_str}"

    if len(error_str) >= 200:
        message += "..."

    return message


def create_progress_text(current: int, total: int, item_name: str = "элемент") -> str:
    """Создать текст прогресса."""
    percentage = int((current / total) * 100) if total > 0 else 0
    progress_bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)

    return (
        f"📊 Обработка: {current}/{total} {item_name}\n[{progress_bar}] {percentage}%"
    )
