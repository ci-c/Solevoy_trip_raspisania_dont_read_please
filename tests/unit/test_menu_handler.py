"""Comprehensive tests for menu_handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.callbacks import MenuCallback


@pytest.mark.asyncio
@pytest.mark.unit
class TestMenuHandler:
    """Tests for menu handler."""

    def create_callback_query(self, user_id: int, action: str):
        """Helper to create callback query."""
        callback = MagicMock(spec=types.CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = user_id
        callback.from_user.first_name = "Test User"
        callback.answer = AsyncMock()
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        return callback

    async def test_handle_menu_home(self, db_session):
        """Test handling home menu action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "home")
        callback_data = MenuCallback(action="home")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Главное меню" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_setup_profile(self, db_session):
        """Test handling setup profile action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "setup_profile")
        callback_data = MenuCallback(action="setup_profile")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Настройка профиля" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_my_schedule_no_profile(self, db_session):
        """Test my schedule action without profile."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "my_schedule")
        callback_data = MenuCallback(action="my_schedule")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        call_text = callback.message.edit_text.call_args[0][0]
        assert "необходимо настроить профиль" in call_text

    async def test_handle_menu_my_schedule_with_profile(self, db_session):
        """Test my schedule action with profile."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "my_schedule")
        callback_data = MenuCallback(action="my_schedule")
        state = MagicMock(spec=FSMContext)

        # Create a mock user with profile
        mock_user = MagicMock()
        mock_user.profile = MagicMock()
        mock_user.profile.group_id = 1

        with patch("app.bot.handlers.menu_handler.UserService") as MockUserService:
            mock_service = AsyncMock()
            mock_service.get_user_by_telegram_id.return_value = mock_user
            MockUserService.return_value = mock_service

            await handle_menu(callback, callback_data, state)

            callback.answer.assert_called_once()
            callback.message.edit_text.assert_called_once()

    async def test_handle_menu_search_group(self, db_session):
        """Test search group action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "search_group")
        callback_data = MenuCallback(action="search_group")
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        state.set_state.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Поиск группы" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_search(self, db_session):
        """Test search action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "search")
        callback_data = MenuCallback(action="search")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()

    async def test_handle_menu_applications(self, db_session):
        """Test applications action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "applications")
        callback_data = MenuCallback(action="applications")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Заявления" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_diary(self, db_session):
        """Test diary action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "diary")
        callback_data = MenuCallback(action="diary")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "дневник" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_attestation(self, db_session):
        """Test attestation action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "attestation")
        callback_data = MenuCallback(action="attestation")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Аттестация" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_grades(self, db_session):
        """Test grades action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "grades")
        callback_data = MenuCallback(action="grades")
        state = MagicMock(spec=FSMContext)

        with patch("app.bot.handlers.grade_handler.handle_grades_main") as mock_grades:
            mock_grades.return_value = None

            await handle_menu(callback, callback_data, state)

            callback.answer.assert_called_once()
            mock_grades.assert_called_once()

    async def test_handle_menu_reminders(self, db_session):
        """Test reminders action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "reminders")
        callback_data = MenuCallback(action="reminders")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Напоминания" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_settings(self, db_session):
        """Test settings action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "settings")
        callback_data = MenuCallback(action="settings")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Настройки" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_retry(self, db_session):
        """Test retry action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "retry")
        callback_data = MenuCallback(action="retry")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Повторная попытка" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_unknown_action(self, db_session):
        """Test unknown menu action."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "unknown_action")
        callback_data = MenuCallback(action="unknown_action")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        assert "Неизвестное действие" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_exception(self, db_session):
        """Test menu handler with exception."""
        from app.bot.handlers.menu_handler import handle_menu

        callback = self.create_callback_query(123456, "home")
        callback_data = MenuCallback(action="home")
        state = MagicMock(spec=FSMContext)

        with patch("app.bot.handlers.menu_handler.UserService") as mock_service:
            mock_service.return_value.get_user_by_telegram_id = AsyncMock(
                side_effect=Exception("Test error")
            )

            await handle_menu(callback, callback_data, state)

            callback.answer.assert_called_once()
            callback.message.edit_text.assert_called_once()
            assert "Ошибка" in callback.message.edit_text.call_args[0][0]

    async def test_handle_menu_with_user(self, db_session):
        """Test menu handler with existing user."""
        from app.bot.handlers.menu_handler import handle_menu
        from app.services.user_service import UserService

        user_service = UserService()
        await user_service.create_user(
            telegram_id=123456,
            telegram_username="testuser",
            full_name="Test User"
        )

        callback = self.create_callback_query(123456, "home")
        callback_data = MenuCallback(action="home")
        state = MagicMock(spec=FSMContext)

        await handle_menu(callback, callback_data, state)

        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
