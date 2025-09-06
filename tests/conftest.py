"""
Конфигурация pytest с фикстурами для всех тестов.

Зона ответственности:
- Создание тестовых фикстур для базы данных
- Настройка тестового окружения
- Инициализация mock объектов для внешних сервисов
- Предоставление тестовых данных для всех тестов
"""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import aiosqlite

from app.database.connection import DatabaseConnection
from app.services.user_service import UserService
from app.services.schedule_service import ScheduleService
from app.models.user import User, AccessLevel


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[DatabaseConnection, None]:
    """Фикстура для тестовой базы данных в памяти."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        test_db_path = Path(temp_file.name)
    
    test_connection = DatabaseConnection(db_path=test_db_path)
    
    # Инициализируем схему
    await test_connection.initialize_database()
    
    yield test_connection
    
    # Очистка после тестов
    if test_db_path.exists():
        test_db_path.unlink()


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
async def test_user_service(test_db: DatabaseConnection) -> UserService:
    """Сервис пользователей для тестов."""
    return UserService(db_connection=test_db)


@pytest.fixture
async def test_schedule_service(test_db: DatabaseConnection) -> ScheduleService:
    """Сервис расписания для тестов.""" 
    return ScheduleService(db_connection=test_db)


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


@pytest.fixture
async def populated_test_db(test_db: DatabaseConnection, sample_user_data, sample_group_data) -> DatabaseConnection:
    """База данных с тестовыми данными."""
    async with aiosqlite.connect(str(test_db.db_path)) as conn:
        # Добавляем тестового пользователя
        await conn.execute(
            "INSERT INTO users (telegram_id, telegram_username, full_name, access_level) VALUES (?, ?, ?, ?)",
            (sample_user_data["telegram_id"], sample_user_data["telegram_username"], 
             sample_user_data["full_name"], sample_user_data["access_level"].value)
        )
        
        # Добавляем специальность
        await conn.execute(
            "INSERT INTO specialities (code, name, full_name, faculty) VALUES (?, ?, ?, ?)",
            ("31.05.01", "лечебное дело", "31.05.01 лечебное дело", "Лечебный факультет")
        )
        
        # Добавляем группу
        await conn.execute(
            "INSERT INTO study_groups (number, course, stream, speciality_id, academic_year) VALUES (?, ?, ?, ?, ?)",
            (sample_group_data["number"], sample_group_data["course"], sample_group_data["stream"], 1, 
             sample_group_data["academic_year"])
        )
        
        await conn.commit()
    
    return test_db


@pytest.fixture
def pytest_configure():
    """Конфигурация pytest."""
    pytest.main_test_data = {
        "test_user_id": 123456789,
        "test_group": "101а", 
        "test_academic_year": "2024/2025"
    }


# Маркеры для категоризации тестов
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.database = pytest.mark.database