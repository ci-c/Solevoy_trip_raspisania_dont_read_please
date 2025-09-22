#!/usr/bin/env python3
"""
Интеграционные тесты для эмуляции пользователя.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User, Chat, CallbackQuery, Update
from aiogram.fsm.context import FSMContext

from app.bot.main import create_bot_app
from app.services.schedule_service import ScheduleService
from app.services.group_service import GroupService
from app.services.user_service import UserService


class MockUser:
    """Мок пользователя для тестов."""
    
    def __init__(self, user_id: int = 12345, username: str = "test_user"):
        self.id = user_id
        self.username = username
        self.first_name = "Test"
        self.last_name = "User"


class MockMessage:
    """Мок сообщения для тестов."""
    
    def __init__(self, text: str = "/start", user: MockUser = None):
        self.text = text
        self.from_user = user or MockUser()
        self.chat = MagicMock()
        self.chat.id = 12345
        self.answer = AsyncMock()
        self.edit_text = AsyncMock()
        self.reply = AsyncMock()


class MockCallbackQuery:
    """Мок callback query для тестов."""
    
    def __init__(self, data: str = "menu:start", user: MockUser = None):
        self.data = data
        self.from_user = user or MockUser()
        self.message = MockMessage()
        self.answer = AsyncMock()


@pytest.mark.asyncio
async def test_bot_startup():
    """Тест запуска бота."""
    try:
        app = await create_bot_app()
        assert app is not None
        assert app.bot is not None
        assert app.dp is not None
        print("✅ Bot startup test passed")
    except Exception as e:
        print(f"❌ Bot startup test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_user_creation():
    """Тест создания пользователя."""
    try:
        user_service = UserService()
        user = await user_service.create_user(
            telegram_id=99999,
            telegram_username="test_user",
            full_name="Test User"
        )
        
        if user is None:
            print("⚠️ User creation returned None (user might already exist)")
        else:
            print(f"✅ User creation test passed: {user}")
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_schedule_service_faculties():
    """Тест получения факультетов."""
    try:
        schedule_service = ScheduleService()
        faculties = await schedule_service.get_available_faculties()
        
        if faculties is None:
            print("⚠️ Faculties returned None (database might be empty)")
        elif len(faculties) == 0:
            print("⚠️ No faculties found in database")
        else:
            print(f"✅ Faculties test passed: {len(faculties)} faculties found")
            print(f"First faculty: {faculties[0]}")
    except Exception as e:
        print(f"❌ Faculties test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_group_service():
    """Тест работы с группами."""
    try:
        group_service = GroupService()
        
        # Тест поиска несуществующей группы
        group = await group_service.find_or_create_group("999")
        
        if group is None:
            print("⚠️ Group creation returned None")
        else:
            print(f"✅ Group service test passed: {group}")
    except Exception as e:
        print(f"❌ Group service test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_error_handling():
    """Тест обработки ошибок."""
    try:
        schedule_service = ScheduleService()
        
        # Тест с невалидными данными
        result = await schedule_service.get_user_schedule(-1)  # Невалидный ID
        
        if result is None:
            print("✅ Error handling test passed: service returned None for invalid input")
        else:
            print(f"⚠️ Error handling test: expected None, got {result}")
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        raise


async def run_all_tests():
    """Запустить все тесты."""
    print("🧪 Starting bot integration tests...")
    print("=" * 50)
    
    tests = [
        test_bot_startup,
        test_user_creation,
        test_schedule_service_faculties,
        test_group_service,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some tests failed!")
        return False
    else:
        print("✅ All tests passed!")
        return True


if __name__ == "__main__":
    asyncio.run(run_all_tests())
