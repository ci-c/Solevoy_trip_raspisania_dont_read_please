"""
Интеграционные тесты для операций с базой данных.

Тестирование взаимодействия различных компонентов:
- UserService + DatabaseConnection
- ScheduleService + DatabaseConnection  
- Миграции и схема БД
- Целостность данных между связанными таблицами
"""

import pytest
from datetime import datetime, date

from app.database.connection import DatabaseConnection
from app.services.user_service import UserService
from app.models.user import User, AccessLevel


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    """Интеграционные тесты для БД."""

    async def test_full_user_lifecycle(self, test_db: DatabaseConnection):
        """Тест полного жизненного цикла пользователя."""
        user_service = UserService(db_connection=test_db)
        
        # 1. Создание пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            telegram_username="test_user",
            full_name="Test User"
        )
        
        assert user.id is not None
        assert user.access_level == AccessLevel.GUEST
        
        # 2. Получение пользователя
        retrieved_user = await user_service.get_user_by_telegram_id(123456789)
        assert retrieved_user.id == user.id
        assert retrieved_user.telegram_username == "test_user"
        
        # 3. Обновление уровня доступа
        await user_service.update_user_access_level(user.id, AccessLevel.BASIC)
        
        # 4. Проверка обновления
        updated_user = await user_service.get_user_by_telegram_id(123456789)
        assert updated_user.access_level == AccessLevel.BASIC
        
        # 5. Создание студенческого профиля
        profile = await user_service.create_student_profile(
            user_id=user.id,
            student_id="2024001"
        )
        
        assert profile.user_id == user.id
        assert profile.student_id == "2024001"
        
        # 6. Получение профиля
        retrieved_profile = await user_service.get_user_profile(user.id)
        assert retrieved_profile.student_id == "2024001"

    async def test_database_constraints_and_foreign_keys(self, test_db: DatabaseConnection):
        """Тест ограничений БД и внешних ключей."""
        import aiosqlite
        
        async with aiosqlite.connect(str(test_db.db_path)) as conn:
            # Создаем пользователя
            cursor = await conn.execute(
                "INSERT INTO users (telegram_id, telegram_username) VALUES (?, ?)",
                (987654321, "constraint_test")
            )
            user_id = cursor.lastrowid
            
            # Пытаемся создать профиль для несуществующей группы
            with pytest.raises(Exception):  # Ожидаем нарушение внешнего ключа
                await conn.execute(
                    "INSERT INTO student_profiles (user_id, group_id) VALUES (?, ?)",
                    (user_id, 99999)  # Несуществующий group_id
                )

    async def test_database_migration_integrity(self, test_db: DatabaseConnection):
        """Тест целостности после применения миграций.""" 
        import aiosqlite
        
        # Проверяем что все необходимые таблицы существуют
        async with aiosqlite.connect(str(test_db.db_path)) as conn:
            # Получаем список таблиц
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]
            
            expected_tables = [
                'users', 'specialities', 'study_groups', 'student_profiles',
                'invitations', 'subscriptions', 'teachers', 'rooms',
                'subjects', 'schedules', 'lessons', 'grades', 'attendance',
                'homework', 'settings', 'activity_log', 'search_cache'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"

    async def test_concurrent_user_creation(self, test_db: DatabaseConnection):
        """Тест параллельного создания пользователей."""
        import asyncio
        
        user_service = UserService(db_connection=test_db)
        
        async def create_user(telegram_id: int):
            return await user_service.create_user(
                telegram_id=telegram_id,
                full_name=f"User {telegram_id}"
            )
        
        # Создаем 10 пользователей параллельно
        tasks = [create_user(i) for i in range(100000, 100010)]
        users = await asyncio.gather(*tasks)
        
        assert len(users) == 10
        assert all(user.id is not None for user in users)
        
        # Проверяем уникальность ID
        user_ids = [user.id for user in users]
        assert len(set(user_ids)) == 10  # Все ID уникальны

    async def test_data_consistency_after_complex_operations(self, populated_test_db: DatabaseConnection):
        """Тест согласованности данных после сложных операций."""
        import aiosqlite
        user_service = UserService(db_connection=populated_test_db)
        
        # Получаем существующего пользователя
        user = await user_service.get_user_by_telegram_id(123456789)
        
        # Создаем профиль
        profile = await user_service.create_student_profile(
            user_id=user.id,
            group_id=1,
            student_id="2024999"
        )
        
        # Проверяем согласованность данных в БД напрямую
        async with aiosqlite.connect(str(populated_test_db.db_path)) as conn:
            # Проверяем связь user -> profile -> group
            cursor = await conn.execute("""
                SELECT u.telegram_id, sp.student_id, sg.number
                FROM users u 
                JOIN student_profiles sp ON u.id = sp.user_id
                JOIN study_groups sg ON sp.group_id = sg.id
                WHERE u.id = ?
            """, (user.id,))
            
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 123456789  # telegram_id
            assert row[1] == "2024999"   # student_id  
            assert row[2] == "101а"      # group number

    async def test_database_transaction_rollback(self, test_db: DatabaseConnection):
        """Тест отката транзакций при ошибке."""
        import aiosqlite
        
        async with aiosqlite.connect(str(test_db.db_path)) as conn:
            try:
                async with conn.transaction():
                    # Создаем пользователя
                    await conn.execute(
                        "INSERT INTO users (telegram_id, telegram_username) VALUES (?, ?)",
                        (555555555, "rollback_test")
                    )
                    
                    # Намеренно вызываем ошибку
                    await conn.execute("INSERT INTO nonexistent_table VALUES (1)")
                    
            except Exception:
                pass  # Ожидаем ошибку
            
            # Проверяем что пользователь не создался из-за отката
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM users WHERE telegram_id = ?",
                (555555555,)
            )
            count = await cursor.fetchone()
            assert count[0] == 0  # Пользователь не должен существовать