"""
Callback data фабрики для бота.
"""

from aiogram.filters.callback_data import CallbackData


class FilterCallback(CallbackData, prefix="filter"):
    """Callback для фильтров поиска."""

    name: str


class OptionCallback(CallbackData, prefix="option"):
    """Callback для опций фильтров."""

    filter_name: str
    value: str


class ResultCallback(CallbackData, prefix="result"):
    """Callback для результатов поиска."""

    index: int


class FormatCallback(CallbackData, prefix="format"):
    """Callback для форматов файлов."""

    result_index: int
    format_type: str


class MenuCallback(CallbackData, prefix="menu"):
    """Callback для меню."""

    action: str


class ProfileCallback(CallbackData, prefix="profile"):
    """Callback для настройки профиля."""

    action: str
    value: str = ""


class DiaryCallback(CallbackData, prefix="diary"):
    """Callback для дневника."""

    action: str
    item_id: str = ""


class ApplicationCallback(CallbackData, prefix="app"):
    """Callback для заявлений."""

    action: str
    data: str = ""


class AttestationCallback(CallbackData, prefix="attest"):
    """Callback для аттестации."""

    action: str
    topic: str = ""


class GradeCallback(CallbackData, prefix="grade"):
    """Callback для оценок."""

    action: str
    subject: str = ""
    data: str = ""


class GroupSearchCallback(CallbackData, prefix="group_search"):
    """Callback для поиска группы."""

    action: str
    value: str | None = None
    group_id: str | None = None


class GroupSelectionCallback(CallbackData, prefix="group_select"):
    """Callback для выбора группы."""

    action: str
    group_id: int = 0
    faculty: str = ""


class GroupConfirmationCallback(CallbackData, prefix="group_confirm"):
    """Callback для подтверждения выбора группы."""

    action: str
    group_id: int = 0


# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

