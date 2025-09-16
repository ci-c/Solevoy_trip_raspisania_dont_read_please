"""
Базовые тесты функциональности.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.user_service import UserService
from app.services.schedule_service import ScheduleService
from app.services.group_search_service import GroupSearchService


class TestBasicFunctionality:
    """Базовые тесты функциональности."""

    def test_user_service_initialization(self):
        """Тест инициализации UserService."""
        service = UserService()
        assert service is not None

    def test_schedule_service_initialization(self):
        """Тест инициализации ScheduleService."""
        service = ScheduleService()
        assert service is not None

    def test_group_search_service_initialization(self):
        """Тест инициализации GroupSearchService."""
        service = GroupSearchService()
        assert service is not None

    def test_group_search_semester_detection(self):
        """Тест определения семестра."""
        service = GroupSearchService()
        semester, year = service.detect_current_semester()
        
        assert semester in ["осенний", "весенний"]
        assert "/" in year
        assert len(year.split("/")) == 2

    def test_group_search_course_extraction(self):
        """Тест извлечения номера курса из названия группы."""
        service = GroupSearchService()
        
        assert service._extract_course_number("103а") == 103  # Извлекает все цифры
        assert service._extract_course_number("204б") == 204
        assert service._extract_course_number("301в") == 301
        assert service._extract_course_number("invalid") == 1  # По умолчанию

    def test_group_search_stream_extraction(self):
        """Тест извлечения потока из названия группы."""
        service = GroupSearchService()
        
        assert service._extract_stream("103а") == "а"
        assert service._extract_stream("204б") == "б"
        assert service._extract_stream("301в") == "в"
        assert service._extract_stream("123") == "а"  # По умолчанию

    @pytest.mark.asyncio
    async def test_user_service_create_user(self):
        """Тест создания пользователя."""
        service = UserService()
        
        # Мокаем базу данных
        with patch('app.database.session.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            
            # Тест создания пользователя с уникальным ID
            import random
            unique_id = random.randint(1000000000, 9999999999)
            
            user = await service.create_user(
                telegram_id=unique_id,
                telegram_username="test_user",
                full_name="Test User"
            )
            
            assert user.telegram_id == unique_id
            assert user.telegram_username == "test_user"
            assert user.full_name == "Test User"

    @pytest.mark.asyncio
    async def test_schedule_service_get_statistics(self):
        """Тест получения статистики расписаний."""
        service = ScheduleService()
        
        # Мокаем базу данных
        with patch('app.database.session.get_session') as mock_session:
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            
            stats = await service.get_schedule_statistics()
            
            assert isinstance(stats, dict)
            assert "total_lessons" in stats
            assert "total_schedules" in stats
            assert "total_faculties" in stats
            assert "total_specialities" in stats
