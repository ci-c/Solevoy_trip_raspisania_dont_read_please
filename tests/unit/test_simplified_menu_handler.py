"""Tests for simplified menu handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.callbacks import MenuCallback
from app.bot.handlers.simplified_menu_handler import (
    format_user_schedule,
    handle_export_schedule,
    handle_menu_action,
    register_simplified_menu_handlers,
    show_group_selection,
    show_main_menu,
    show_settings_menu,
    show_user_schedule,
)


@pytest.fixture
def mock_callback():
    """Mock callback query."""
    callback = AsyncMock(spec=types.CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123456
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_message():
    """Mock message."""
    message = AsyncMock(spec=types.Message)
    message.from_user = MagicMock()
    message.from_user.id = 123456
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    """Mock FSM state."""
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_user_profile():
    """Mock user profile."""
    return {
        "user_id": 123456,
        "group_name": "101а",
        "faculty": "Лечебный факультет",
        "course": 1,
    }


@pytest.mark.asyncio
class TestHandleMenuAction:
    """Tests for handle_menu_action."""

    async def test_home_action(self, mock_callback, mock_state, mock_user_profile):
        """Test home action."""
        callback_data = MenuCallback(action="home")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc, patch(
            "app.bot.handlers.simplified_menu_handler.show_main_menu"
        ) as mock_show:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(
                return_value=mock_user_profile
            )
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.answer.assert_called_once()
            mock_show.assert_called_once_with(
                mock_callback.message, mock_user_profile
            )

    async def test_select_group_action(self, mock_callback, mock_state):
        """Test select group action."""
        callback_data = MenuCallback(action="select_group")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc, patch(
            "app.bot.handlers.simplified_menu_handler.show_group_selection"
        ) as mock_show:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(return_value=None)
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.answer.assert_called_once()
            mock_show.assert_called_once_with(mock_callback.message, mock_state)

    async def test_my_schedule_action_with_profile(
        self, mock_callback, mock_state, mock_user_profile
    ):
        """Test my schedule action with user profile."""
        callback_data = MenuCallback(action="my_schedule")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc, patch(
            "app.bot.handlers.simplified_menu_handler.show_user_schedule"
        ) as mock_show:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(
                return_value=mock_user_profile
            )
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.answer.assert_called_once()
            mock_show.assert_called_once()

    async def test_my_schedule_action_without_profile(self, mock_callback, mock_state):
        """Test my schedule action without user profile."""
        callback_data = MenuCallback(action="my_schedule")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(return_value=None)
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.message.edit_text.assert_called_once()
            assert "настройте профиль" in str(
                mock_callback.message.edit_text.call_args
            )

    async def test_export_action_with_profile(
        self, mock_callback, mock_state, mock_user_profile
    ):
        """Test export action with user profile."""
        callback_data = MenuCallback(action="export")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc, patch(
            "app.bot.handlers.simplified_menu_handler.handle_export_schedule"
        ) as mock_export:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(
                return_value=mock_user_profile
            )
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.answer.assert_called_once()
            mock_export.assert_called_once()

    async def test_export_action_without_profile(self, mock_callback, mock_state):
        """Test export action without user profile."""
        callback_data = MenuCallback(action="export")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(return_value=None)
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.message.edit_text.assert_called_once()
            assert "настройте профиль" in str(
                mock_callback.message.edit_text.call_args
            )

    async def test_settings_action(
        self, mock_callback, mock_state, mock_user_profile
    ):
        """Test settings action."""
        callback_data = MenuCallback(action="settings")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc, patch(
            "app.bot.handlers.simplified_menu_handler.show_settings_menu"
        ) as mock_show:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(
                return_value=mock_user_profile
            )
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.answer.assert_called_once()
            mock_show.assert_called_once()

    async def test_unknown_action(self, mock_callback, mock_state):
        """Test unknown action."""
        callback_data = MenuCallback(action="unknown_action")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(return_value=None)
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.message.edit_text.assert_called_once()
            assert "в разработке" in str(mock_callback.message.edit_text.call_args)

    async def test_error_handling(self, mock_callback, mock_state):
        """Test error handling."""
        callback_data = MenuCallback(action="home")

        with patch(
            "app.bot.handlers.simplified_menu_handler.UserService"
        ) as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_profile = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_user_svc.return_value = user_service_instance

            await handle_menu_action(mock_callback, callback_data, mock_state)

            mock_callback.message.edit_text.assert_called_once()
            assert "Ошибка" in str(mock_callback.message.edit_text.call_args)


@pytest.mark.asyncio
class TestShowMainMenu:
    """Tests for show_main_menu."""

    async def test_show_main_menu_with_profile(self, mock_message, mock_user_profile):
        """Test showing main menu with user profile."""
        await show_main_menu(mock_message, mock_user_profile)

        mock_message.edit_text.assert_called_once()
        call_args = str(mock_message.edit_text.call_args)
        assert "101а" in call_args or "группа" in call_args.lower()

    async def test_show_main_menu_without_profile(self, mock_message):
        """Test showing main menu without user profile."""
        await show_main_menu(mock_message, None)

        mock_message.edit_text.assert_called_once()
        call_args = str(mock_message.edit_text.call_args)
        assert "выберите" in call_args.lower() or "добро" in call_args.lower()

    async def test_show_main_menu_edit_fails(self, mock_message, mock_user_profile):
        """Test showing main menu when edit fails."""
        mock_message.edit_text = AsyncMock(side_effect=Exception("Edit failed"))

        await show_main_menu(mock_message, mock_user_profile)

        # Should fallback to answer
        mock_message.answer.assert_called_once()


@pytest.mark.asyncio
class TestShowGroupSelection:
    """Tests for show_group_selection."""

    async def test_show_group_selection_with_faculties(self, mock_message, mock_state):
        """Test showing group selection with faculties."""
        mock_faculties = [
            {"name": "Лечебный факультет"},
            {"name": "Педиатрический факультет"},
        ]

        with patch(
            "app.bot.handlers.simplified_menu_handler.ScheduleService"
        ) as mock_svc:
            service_instance = AsyncMock()
            service_instance.get_available_faculties = AsyncMock(
                return_value=mock_faculties
            )
            mock_svc.return_value = service_instance

            await show_group_selection(mock_message, mock_state)

            mock_message.edit_text.assert_called_once()

    async def test_show_group_selection_without_faculties(
        self, mock_message, mock_state
    ):
        """Test showing group selection without faculties."""
        with patch(
            "app.bot.handlers.simplified_menu_handler.ScheduleService"
        ) as mock_svc:
            service_instance = AsyncMock()
            service_instance.get_available_faculties = AsyncMock(return_value=[])
            mock_svc.return_value = service_instance

            await show_group_selection(mock_message, mock_state)

            mock_message.edit_text.assert_called_once()
            call_args = str(mock_message.edit_text.call_args)
            assert "Введите" in call_args or "номер" in call_args

    async def test_show_group_selection_error(self, mock_message, mock_state):
        """Test showing group selection with error."""
        with patch(
            "app.bot.handlers.simplified_menu_handler.ScheduleService"
        ) as mock_svc:
            service_instance = AsyncMock()
            service_instance.get_available_faculties = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_svc.return_value = service_instance

            await show_group_selection(mock_message, mock_state)

            mock_message.edit_text.assert_called_once()
            call_args = str(mock_message.edit_text.call_args)
            # When there's an error or no faculties, it falls back to manual input
            assert "Введите" in call_args or "номер" in call_args


@pytest.mark.asyncio
class TestShowUserSchedule:
    """Tests for show_user_schedule."""

    async def test_show_user_schedule_with_data(
        self, mock_message, mock_state, mock_user_profile
    ):
        """Test showing user schedule with data."""
        mock_schedule = [
            {
                "day_of_week": 1,
                "lesson_number": 1,
                "subject_name": "Анатомия",
                "lesson_type": "Лекция",
                "teacher_name": "Иванов И.И.",
                "start_time": "09:00",
                "end_time": "10:35",
            }
        ]

        with patch(
            "app.bot.handlers.simplified_menu_handler.ScheduleService"
        ) as mock_svc:
            service_instance = AsyncMock()
            service_instance.get_user_schedule = AsyncMock(
                return_value=mock_schedule
            )
            mock_svc.return_value = service_instance

            await show_user_schedule(mock_message, mock_user_profile, mock_state)

            mock_message.edit_text.assert_called_once()

    async def test_show_user_schedule_without_data(
        self, mock_message, mock_state, mock_user_profile
    ):
        """Test showing user schedule without data."""
        with patch(
            "app.bot.handlers.simplified_menu_handler.ScheduleService"
        ) as mock_svc:
            service_instance = AsyncMock()
            service_instance.get_user_schedule = AsyncMock(return_value=None)
            mock_svc.return_value = service_instance

            await show_user_schedule(mock_message, mock_user_profile, mock_state)

            mock_message.edit_text.assert_called_once()
            call_args = str(mock_message.edit_text.call_args)
            assert "Нет данных" in call_args or "нет" in call_args.lower()

    async def test_show_user_schedule_error(
        self, mock_message, mock_state, mock_user_profile
    ):
        """Test showing user schedule with error."""
        with patch(
            "app.bot.handlers.simplified_menu_handler.ScheduleService"
        ) as mock_svc:
            service_instance = AsyncMock()
            service_instance.get_user_schedule = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_svc.return_value = service_instance

            await show_user_schedule(mock_message, mock_user_profile, mock_state)

            mock_message.edit_text.assert_called_once()
            call_args = str(mock_message.edit_text.call_args)
            assert "Ошибка" in call_args


@pytest.mark.asyncio
async def test_handle_export_schedule(mock_message, mock_state, mock_user_profile):
    """Test handle export schedule."""
    await handle_export_schedule(mock_message, mock_user_profile, mock_state)

    mock_message.edit_text.assert_called_once()
    call_args = str(mock_message.edit_text.call_args)
    assert "Экспорт" in call_args or "разработке" in call_args


@pytest.mark.asyncio
class TestShowSettingsMenu:
    """Tests for show_settings_menu."""

    async def test_show_settings_with_profile(self, mock_message, mock_user_profile):
        """Test showing settings menu with user profile."""
        await show_settings_menu(mock_message, mock_user_profile)

        mock_message.edit_text.assert_called_once()
        call_args = str(mock_message.edit_text.call_args)
        assert "Настройки" in call_args

    async def test_show_settings_without_profile(self, mock_message):
        """Test showing settings menu without user profile."""
        await show_settings_menu(mock_message, None)

        mock_message.edit_text.assert_called_once()
        call_args = str(mock_message.edit_text.call_args)
        assert "настройте профиль" in call_args


class TestFormatUserSchedule:
    """Tests for format_user_schedule."""

    def test_format_empty_schedule(self):
        """Test formatting empty schedule."""
        result = format_user_schedule([], "101а")

        assert "101а" in result
        assert "Нет занятий" in result or "нет" in result.lower()

    def test_format_schedule_with_lessons(self):
        """Test formatting schedule with lessons."""
        schedule = [
            {
                "day_of_week": 1,
                "lesson_number": 1,
                "subject_name": "Анатомия",
                "lesson_type": "Лекция",
                "teacher_name": "Иванов И.И.",
                "start_time": "09:00",
                "end_time": "10:35",
                "room_number": "101",
            },
            {
                "day_of_week": 1,
                "lesson_number": 2,
                "subject_name": "Биология",
                "lesson_type": "Практика",
                "teacher_name": "Петров П.П.",
                "start_time": "10:45",
                "end_time": "12:20",
            },
        ]

        result = format_user_schedule(schedule, "101а")

        assert "101а" in result
        assert "Анатомия" in result
        assert "Биология" in result
        assert "Понедельник" in result
        assert "Иванов И.И." in result

    def test_format_schedule_multiple_days(self):
        """Test formatting schedule with multiple days."""
        schedule = [
            {
                "day_of_week": 1,
                "lesson_number": 1,
                "subject_name": "Анатомия",
                "lesson_type": "Лекция",
                "teacher_name": "Иванов И.И.",
            },
            {
                "day_of_week": 2,
                "lesson_number": 1,
                "subject_name": "Биология",
                "lesson_type": "Практика",
                "teacher_name": "Петров П.П.",
            },
        ]

        result = format_user_schedule(schedule, "101а")

        assert "Понедельник" in result
        assert "Вторник" in result

    def test_format_schedule_with_building(self):
        """Test formatting schedule with building info."""
        schedule = [
            {
                "day_of_week": 1,
                "lesson_number": 1,
                "subject_name": "Анатомия",
                "lesson_type": "Лекция",
                "teacher_name": "Иванов И.И.",
                "room_number": "101",
                "building": "Корпус А",
            }
        ]

        result = format_user_schedule(schedule, "101а")

        assert "101" in result
        assert "Корпус А" in result


@pytest.mark.asyncio
async def test_register_simplified_menu_handlers():
    """Test handler registration."""
    dp = MagicMock()
    dp.callback_query = MagicMock()
    dp.callback_query.register = MagicMock()

    await register_simplified_menu_handlers(dp)

    dp.callback_query.register.assert_called_once()
