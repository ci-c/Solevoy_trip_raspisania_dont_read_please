"""
Конфигурация pytest с фикстурами для всех тестов.
"""

import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock

import pytest

from app.services.user_service import UserService
from app.services.schedule_service import ScheduleService
from app.models.user import AccessLevel


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_telegram_api():
    """Mock для Telegram API."""
    mock = AsyncMock()
    mock.send_message = AsyncMock(return_value={"message_id": 123})
    mock.edit_message_text = AsyncMock(return_value={"message_id": 123})
    mock.delete_message = AsyncMock(return_value=True)
    return mock


@pytest.fixture 
def mock_szgmu_api():
    """Mock для SZGMU API."""
    mock = AsyncMock()
    mock.search_schedules = AsyncMock(return_value=[
        {
            "id": 1,
            "display_name": "31.05.01 лечебное дело - 1 курс, а поток",
            "data": {
                "scheduleLessonDtoList": [
                    {
                        "subject": "Анатомия",
                        "teacher": "Иванов И.И.",
                        "room": "101",
                        "timeStart": "09:00",
                        "timeEnd": "10:35",
                        "dayName": "понедельник",
                        "weekNumber": 1,
                        "group": "101а",
                        "lessonType": "лекция"
                    }
                ]
            }
        }
    ])
    return mock


@pytest.fixture
def test_user_service() -> UserService:
    """Сервис пользователей для тестов."""
    return UserService()


@pytest.fixture
def test_schedule_service() -> ScheduleService:
    """Сервис расписания для тестов.""" 
    return ScheduleService()


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Тестовые данные пользователя."""
    return {
        "telegram_id": 123456789,
        "telegram_username": "test_user",
        "full_name": "Test User",
        "access_level": AccessLevel.BASIC
    }


@pytest.fixture 
def sample_group_data() -> Dict[str, Any]:
    """Тестовые данные группы."""
    return {
        "number": "101а",
        "course": 1,
        "stream": "а",
        "speciality": "31.05.01 лечебное дело",
        "academic_year": "2024/2025",
        "current_semester": "осенний"
    }


@pytest.fixture
def sample_lesson_data() -> Dict[str, Any]:
    """Тестовые данные занятия."""
    return {
        "subject_name": "Анатомия человека",
        "lesson_type": "lecture",
        "teacher_name": "Петров П.П.",
        "room_number": "201",
        "start_time": "09:00",
        "end_time": "10:35", 
        "day_of_week": 1,
        "week_number": 1,
        "date": "2024-09-02"
    }


# Маркеры для категоризации тестов
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.database = pytest.mark.database