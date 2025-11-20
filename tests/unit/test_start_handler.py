"""Comprehensive tests for start_handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.handlers.start_handler import cmd_start, cmd_cancel, cmd_clean


@pytest.mark.asyncio
@pytest.mark.unit
class TestStartHandler:
    """Tests for start command handlers."""

    async def test_cmd_start_no_user(self):
        """Test start command when user is not identified."""
        message = MagicMock(spec=types.Message)
        message.from_user = None
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)

        await cmd_start(message, state)

        message.answer.assert_called_once()
        assert "Could not identify user" in message.answer.call_args[0][0]

    async def test_cmd_start_rate_limited(self):
        """Test start command with rate limiting."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (False, "Too many requests")

            await cmd_start(message, state)

            message.answer.assert_called_once()
            assert "Too many requests" in message.answer.call_args[0][0]

    async def test_cmd_start_new_user(self, db_session):
        """Test start command for new user."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 999999
        message.from_user.username = "newuser"
        message.from_user.full_name = "New User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.set_state = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            await cmd_start(message, state)

            state.clear.assert_called_once()
            state.set_state.assert_called_once()
            message.answer.assert_called_once()

    async def test_cmd_start_existing_user(self, db_session):
        """Test start command for existing user."""
        from app.services.user_service import UserService

        # Create user first
        user_service = UserService()
        await user_service.create_user(
            telegram_id=888888,
            telegram_username="existinguser",
            full_name="Existing User"
        )

        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 888888
        message.from_user.username = "existinguser"
        message.from_user.full_name = "Existing User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.set_state = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            await cmd_start(message, state)

            state.clear.assert_called_once()
            message.answer.assert_called_once()

    async def test_cmd_start_invalid_username(self, db_session):
        """Test start command with invalid username."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 777777
        message.from_user.username = None
        message.from_user.full_name = "Test User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.set_state = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            await cmd_start(message, state)

            # Should still work
            message.answer.assert_called_once()

    async def test_cmd_start_validation_error(self, db_session):
        """Test start command with validation error."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 666666
        message.from_user.username = "validuser"
        message.from_user.full_name = "Valid User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            with patch('app.bot.handlers.start_handler.UserService') as mock_service:
                from app.utils.validation import ValidationError
                mock_service.return_value.get_user_by_telegram_id = AsyncMock(
                    side_effect=ValidationError("Invalid data")
                )

                await cmd_start(message, state)

                # Should handle error
                message.answer.assert_called()

    async def test_cmd_cancel_no_state(self):
        """Test cancel command when no active state."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.get_state = AsyncMock(return_value=None)

        await cmd_cancel(message, state)

        message.answer.assert_called_once()
        assert "Нет активных действий" in message.answer.call_args[0][0]

    async def test_cmd_cancel_with_state(self):
        """Test cancel command with active state."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.get_state = AsyncMock(return_value="SomeState")
        state.clear = AsyncMock()

        await cmd_cancel(message, state)

        state.clear.assert_called_once()
        message.answer.assert_called_once()
        assert "отменено" in message.answer.call_args[0][0]

    async def test_cmd_clean_success(self):
        """Test clean command successful execution."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()

        await cmd_clean(message, state)

        state.clear.assert_called_once()
        message.answer.assert_called_once()
        assert "очищен" in message.answer.call_args[0][0]

    async def test_cmd_clean_with_error(self):
        """Test clean command with error."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock(side_effect=Exception("State error"))

        await cmd_clean(message, state)

        # Should handle error gracefully
        message.answer.assert_called_once()
        assert "Ошибка" in message.answer.call_args[0][0]

    async def test_cmd_start_with_profile(self, db_session):
        """Test start command for user with profile."""
        from app.services.user_service import UserService
        from app.models.user import StudentProfile

        # Create user with profile
        user_service = UserService()
        user = await user_service.create_user(
            telegram_id=555555,
            telegram_username="profileuser",
            full_name="Profile User"
        )

        # Mock profile
        profile = StudentProfile(user_id=user.id, group_id=1, student_id="2024001")

        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 555555
        message.from_user.username = "profileuser"
        message.from_user.full_name = "Profile User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.set_state = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            with patch('app.bot.handlers.start_handler.UserService') as MockUserService:
                mock_service = AsyncMock()
                mock_service.get_user_by_telegram_id.return_value = user
                mock_service.update_user_activity.return_value = None
                mock_service.get_user_profile.return_value = profile
                MockUserService.return_value = mock_service

                await cmd_start(message, state)

                message.answer.assert_called_once()
                # Should mention profile
                call_text = message.answer.call_args[0][0]
                assert "профиль" in call_text.lower() or "Группа" in call_text

    async def test_cmd_start_database_error(self, db_session):
        """Test start command with database error."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 444444
        message.from_user.username = "testuser"
        message.from_user.full_name = "Test User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            with patch('app.bot.handlers.start_handler.UserService') as mock_service:
                from app.utils.error_handling import DatabaseError
                mock_service.return_value.get_user_by_telegram_id = AsyncMock(
                    side_effect=DatabaseError("DB Error")
                )

                await cmd_start(message, state)

                # Should handle error
                message.answer.assert_called()

    async def test_cmd_start_unknown_error(self, db_session):
        """Test start command with unknown error."""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 333333
        message.from_user.username = "testuser"
        message.from_user.full_name = "Test User"
        message.answer = AsyncMock()

        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()

        with patch('app.utils.rate_limiter.check_rate_limit_manual') as mock_rate_limit:
            mock_rate_limit.return_value = (True, "")

            with patch('app.bot.handlers.start_handler.UserService') as mock_service:
                mock_service.return_value.get_user_by_telegram_id = AsyncMock(
                    side_effect=Exception("Unknown error")
                )

                await cmd_start(message, state)

                # Should handle error
                message.answer.assert_called()
