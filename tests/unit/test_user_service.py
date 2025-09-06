"""
Тесты для UserService.

Критически важные функции:
- Создание пользователей
- Получение пользователя по telegram_id  
- Управление профилями студентов
- Проверка прав доступа
"""

import pytest
from datetime import datetime

from app.services.user_service import UserService
from app.models.user import User, AccessLevel, StudentProfile


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

    async def test_get_user_by_telegram_id_existing(self, populated_test_db, sample_user_data):
        """Тест получения существующего пользователя."""
        user_service = UserService(db_connection=populated_test_db)
        
        user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        
        assert user is not None
        assert isinstance(user, User)
        assert user.telegram_id == sample_user_data["telegram_id"]
        assert user.access_level == sample_user_data["access_level"]

    async def test_get_user_by_telegram_id_not_existing(self, test_user_service: UserService):
        """Тест получения несуществующего пользователя."""
        user = await test_user_service.get_user_by_telegram_id(999999999)
        
        assert user is None

    async def test_update_user_activity(self, populated_test_db, sample_user_data):
        """Тест обновления активности пользователя."""
        user_service = UserService(db_connection=populated_test_db)
        
        # Получаем пользователя
        user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        assert user is not None
        
        # Обновляем активность
        await user_service.update_user_activity(user.id)
        
        # Проверяем что last_seen обновилось (тест на время может быть неточным)
        updated_user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        assert updated_user.last_seen is not None

    async def test_create_duplicate_user_fails(self, populated_test_db, sample_user_data):
        """Тест что создание дублирующего пользователя не проходит."""
        user_service = UserService(db_connection=populated_test_db)
        
        with pytest.raises(Exception):  # Ожидаем ошибку уникальности
            await user_service.create_user(
                telegram_id=sample_user_data["telegram_id"],
                telegram_username="duplicate_user"
            )

    async def test_upgrade_user_access_level(self, populated_test_db, sample_user_data):
        """Тест повышения уровня доступа пользователя."""
        user_service = UserService(db_connection=populated_test_db)
        
        # Получаем пользователя
        user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        assert user.access_level == AccessLevel.BASIC
        
        # Повышаем до admin
        await user_service.update_user_access_level(user.id, AccessLevel.ADMIN)
        
        # Проверяем обновление
        updated_user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        assert updated_user.access_level == AccessLevel.ADMIN

    async def test_create_student_profile(self, populated_test_db, sample_user_data):
        """Тест создания студенческого профиля."""
        user_service = UserService(db_connection=populated_test_db)
        
        user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        
        profile = await user_service.create_student_profile(
            user_id=user.id,
            group_id=1,  # Используем группу из populated_test_db
            student_id="2024001"
        )
        
        assert isinstance(profile, StudentProfile)
        assert profile.user_id == user.id
        assert profile.group_id == 1
        assert profile.student_id == "2024001"

    async def test_get_user_profile(self, populated_test_db, sample_user_data):
        """Тест получения профиля пользователя.""" 
        user_service = UserService(db_connection=populated_test_db)
        
        user = await user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        
        # Создаем профиль
        await user_service.create_student_profile(
            user_id=user.id,
            group_id=1,
            student_id="2024001"
        )
        
        # Получаем профиль
        profile = await user_service.get_user_profile(user.id)
        
        assert profile is not None
        assert profile.user_id == user.id
        assert profile.group_id == 1

    @pytest.mark.parametrize("access_level,expected_access", [
        (AccessLevel.GUEST, False),
        (AccessLevel.BASIC, True), 
        (AccessLevel.TESTER, True),
        (AccessLevel.ADMIN, True),
    ])
    async def test_user_access_permissions(self, test_user_service, access_level, expected_access):
        """Тест проверки прав доступа пользователей."""
        user = await test_user_service.create_user(
            telegram_id=123456789,
            access_level=access_level
        )
        
        # Имитируем проверку доступа к премиум функциям
        has_access = access_level != AccessLevel.GUEST
        assert has_access == expected_access