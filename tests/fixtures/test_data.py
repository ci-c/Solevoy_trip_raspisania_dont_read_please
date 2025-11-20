"""
Test data fixtures for SZGMU Schedule Bot.

Provides sample users, groups, schedules, and other test data.
"""

from datetime import datetime, timedelta
from typing import Any

import pytest


@pytest.fixture
def sample_telegram_user() -> dict[str, Any]:
    """Sample Telegram user data."""
    return {
        "id": 123456789,
        "is_bot": False,
        "first_name": "Иван",
        "last_name": "Петров",
        "username": "ivan_petrov",
        "language_code": "ru",
    }


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for database."""
    return {
        "telegram_id": 123456789,
        "username": "ivan_petrov",
        "full_name": "Иван Петров",
        "is_active": True,
    }


@pytest.fixture
def sample_faculty() -> dict[str, Any]:
    """Sample faculty data for database."""
    return {
        "name": "Лечебный факультет",
        "short_name": "ЛФ",
        "description": "Лечебный факультет СЗГМУ",
    }


@pytest.fixture
def sample_group() -> dict[str, Any]:
    """Sample group data for database."""
    return {
        "name": "103а",
        "faculty": "Лечебный факультет",
        "speciality": "31.05.01 лечебное дело",
        "course": 1,
    }


@pytest.fixture
def sample_schedule_lesson() -> dict[str, Any]:
    """Sample schedule lesson data."""
    return {
        "date": datetime.now().date(),
        "day_of_week": 1,
        "lesson_number": 1,
        "lesson_type": "Лекция",
        "subject_name": "Анатомия",
        "lecturer_name": "Иванов И.И.",
        "classroom_number": "101",
        "start_time": "09:00",
        "end_time": "10:30",
        "group_id": 1,
    }


@pytest.fixture
def multiple_lessons() -> list[dict[str, Any]]:
    """Multiple schedule lessons for testing."""
    base_date = datetime.now().date()
    lessons = []

    for i in range(3):
        lessons.append({
            "date": base_date + timedelta(days=i),
            "day_of_week": i + 1,
            "lesson_number": i + 1,
            "lesson_type": "Лекция" if i % 2 == 0 else "Семинар",
            "subject_name": f"Предмет {i+1}",
            "lecturer_name": f"Преподаватель {i+1}",
            "classroom_number": f"10{i+1}",
            "start_time": f"0{9+i}:00",
            "end_time": f"{10+i}:30",
            "group_id": 1,
        })

    return lessons
