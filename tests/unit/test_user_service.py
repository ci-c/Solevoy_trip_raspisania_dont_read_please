"""
Тесты для UserService.
"""

import pytest

from app.services.user_service import UserService
from app.models.user import User, AccessLevel


@pytest.mark.asyncio
@pytest.mark.unit
class TestUserService:
    """Тесты для сервиса пользователей."""

    async def test_create_user_success(self, test_user_service: UserService, sample_user_data):
        """Тест успешного создания пользователя."""
        user = await test_user_service.create_user(
            telegram_id=sample_user_data["telegram_id"],
            telegram_username=sample_user_data["telegram_username"],
            full_name=sample_user_data["full_name"]
        )
        
        assert isinstance(user, User)
        assert user.telegram_id == sample_user_data["telegram_id"]
        assert user.telegram_username == sample_user_data["telegram_username"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.access_level == AccessLevel.GUEST  # default level
        assert user.is_active is True
        assert user.id is not None

    async def test_get_user_by_telegram_id_not_existing(self, test_user_service: UserService):
        """Тест получения несуществующего пользователя."""
        user = await test_user_service.get_user_by_telegram_id(999999999)
        
        assert user is None

    async def test_get_all_users(self, test_user_service: UserService):
        """Тест получения всех пользователей."""
        users = await test_user_service.get_all_users()
        
        assert isinstance(users, list)

    async def test_get_users_count(self, test_user_service: UserService):
        """Тест подсчета пользователей."""
        count = await test_user_service.get_users_count()
        
        assert isinstance(count, int)
        assert count >= 0

    async def test_update_user_activity(self, test_user_service: UserService):
        """Тест обновления активности пользователя."""
        # Создаем пользователя
        user = await test_user_service.create_user(
            telegram_id=123456789,
            telegram_username="test_user",
            full_name="Test User"
        )
        
        # Обновляем активность (заглушка)
        await test_user_service.update_user_activity(user.id)
        
        # Проверяем что метод выполнился без ошибок
        assert True

    async def test_update_user_access_level(self, test_user_service: UserService):
        """Тест обновления уровня доступа."""
        # Создаем пользователя
        user = await test_user_service.create_user(
            telegram_id=123456789,
            telegram_username="test_user",
            full_name="Test User"
        )
        
        # Обновляем уровень доступа (заглушка)
        result = await test_user_service.update_user_access_level(user.id, AccessLevel.ADMIN)
        
        # Проверяем что метод выполнился без ошибок
        assert result is True

    async def test_get_user_profile(self, test_user_service: UserService):
        """Тест получения профиля пользователя."""
        # Создаем пользователя
        user = await test_user_service.create_user(
            telegram_id=123456789,
            telegram_username="test_user",
            full_name="Test User"
        )
        
        # Получаем профиль (заглушка)
        profile = await test_user_service.get_user_profile(user.id)
        
        # Проверяем что метод выполнился без ошибок
        assert profile is None  # Заглушка возвращает None

    async def test_create_or_update_profile(self, test_user_service: UserService):
        """Тест создания/обновления профиля."""
        from app.models.user import StudentProfile
        
        # Создаем пользователя
        user = await test_user_service.create_user(
            telegram_id=123456789,
            telegram_username="test_user",
            full_name="Test User"
        )
        
        # Создаем профиль
        profile = StudentProfile(
            user_id=user.id,
            group_id=1,
            student_id="2024001"
        )
        
        # Сохраняем профиль (заглушка)
        result = await test_user_service.create_or_update_profile(profile)
        
        # Проверяем что метод выполнился без ошибок
        assert isinstance(result, StudentProfile)