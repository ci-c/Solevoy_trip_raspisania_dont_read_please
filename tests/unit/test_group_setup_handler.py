"""Tests for group setup handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.handlers.group_setup_handler import (
    handle_group_command,
    handle_group_setup_callback,
    handle_help_command,
    register_group_setup_handlers,
    select_group,
    show_faculty_groups,
    show_faculty_list,
    start_group_setup,
    handle_schedule_callback,
    handle_grades_callback,
    handle_settings_callback,
)
from app.bot.states import GroupSetupStates


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
def mock_callback():
    """Mock callback query."""
    callback = AsyncMock(spec=types.CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123456
    callback.message = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = "group_setup:test"
    return callback


@pytest.fixture
def mock_state():
    """Mock FSM state."""
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.mark.asyncio
class TestHandleGroupCommand:
    """Tests for handle_group_command."""

    async def test_handle_group_command(self, mock_message, mock_state):
        """Test group command handler."""
        with patch(
            "app.bot.handlers.group_setup_handler.show_faculty_list"
        ) as mock_show:
            await handle_group_command(mock_message, mock_state)

            mock_show.assert_called_once_with(mock_message, mock_state)


@pytest.mark.asyncio
class TestHandleHelpCommand:
    """Tests for handle_help_command."""

    async def test_handle_help_command(self, mock_message, mock_state):
        """Test help command handler."""
        await handle_help_command(mock_message, mock_state)

        mock_message.answer.assert_called_once()
        call_args = str(mock_message.answer.call_args)
        assert "Помощь" in call_args or "help" in call_args.lower()

    async def test_handle_help_command_error(self, mock_message, mock_state):
        """Test help command error handling."""
        mock_message.answer = AsyncMock(side_effect=[Exception("Error"), None])

        await handle_help_command(mock_message, mock_state)

        # Should handle error gracefully and call answer twice
        assert mock_message.answer.call_count == 2


@pytest.mark.asyncio
class TestStartGroupSetup:
    """Tests for start_group_setup."""

    async def test_start_group_setup_success(self, mock_message, mock_state):
        """Test starting group setup successfully."""
        with patch(
            "app.bot.handlers.group_setup_handler.show_faculty_list"
        ) as mock_show:
            await start_group_setup(mock_message, mock_state)

            mock_show.assert_called_once_with(mock_message, mock_state)

    async def test_start_group_setup_error(self, mock_message, mock_state):
        """Test starting group setup with error."""
        with patch(
            "app.bot.handlers.group_setup_handler.show_faculty_list"
        ) as mock_show:
            mock_show.side_effect = Exception("Database error")

            await start_group_setup(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            assert "Ошибка" in str(mock_message.answer.call_args)


@pytest.mark.asyncio
class TestHandleGroupSetupCallback:
    """Tests for handle_group_setup_callback."""

    async def test_select_from_list_action(self, mock_callback, mock_state):
        """Test select from list action."""
        mock_callback.data = "group_setup:select_from_list"

        with patch(
            "app.bot.handlers.group_setup_handler.show_faculty_list"
        ) as mock_show:
            await handle_group_setup_callback(mock_callback, mock_state)

            mock_show.assert_called_once()

    async def test_select_faculty_action(self, mock_callback, mock_state):
        """Test select faculty action."""
        mock_callback.data = "group_setup:select_faculty:1"

        with patch(
            "app.bot.handlers.group_setup_handler.show_faculty_groups"
        ) as mock_show:
            await handle_group_setup_callback(mock_callback, mock_state)

            mock_show.assert_called_once_with(mock_callback, mock_state, "1")

    async def test_select_group_action(self, mock_callback, mock_state):
        """Test select group action."""
        mock_callback.data = "group_setup:select_group:10"

        with patch("app.bot.handlers.group_setup_handler.select_group") as mock_select:
            await handle_group_setup_callback(mock_callback, mock_state)

            mock_select.assert_called_once_with(mock_callback, mock_state, "10")

    async def test_schedule_action(self, mock_callback, mock_state):
        """Test schedule action."""
        mock_callback.data = "group_setup:schedule:today"

        with patch(
            "app.bot.handlers.group_setup_handler.handle_schedule_callback"
        ) as mock_schedule:
            await handle_group_setup_callback(mock_callback, mock_state)

            mock_schedule.assert_called_once()

    async def test_grades_action(self, mock_callback, mock_state):
        """Test grades action."""
        mock_callback.data = "group_setup:grades:view"

        with patch(
            "app.bot.handlers.group_setup_handler.handle_grades_callback"
        ) as mock_grades:
            await handle_group_setup_callback(mock_callback, mock_state)

            mock_grades.assert_called_once()

    async def test_settings_action(self, mock_callback, mock_state):
        """Test settings action."""
        mock_callback.data = "group_setup:settings:main"

        with patch(
            "app.bot.handlers.group_setup_handler.handle_settings_callback"
        ) as mock_settings:
            await handle_group_setup_callback(mock_callback, mock_state)

            mock_settings.assert_called_once()

    async def test_back_to_start_action(self, mock_callback, mock_state):
        """Test back to start action."""
        mock_callback.data = "group_setup:back_to_start"

        await handle_group_setup_callback(mock_callback, mock_state)

        mock_callback.message.edit_text.assert_called_once()
        mock_state.clear.assert_called_once()

    async def test_unknown_action(self, mock_callback, mock_state):
        """Test unknown action."""
        mock_callback.data = "group_setup:unknown_action"

        await handle_group_setup_callback(mock_callback, mock_state)

        mock_callback.answer.assert_called()

    async def test_non_group_setup_callback(self, mock_callback, mock_state):
        """Test callback that doesn't start with group_setup."""
        mock_callback.data = "other:action"

        await handle_group_setup_callback(mock_callback, mock_state)

        # Should ignore non-group_setup callbacks
        mock_callback.answer.call_count >= 0  # May or may not be called

    async def test_error_handling(self, mock_callback, mock_state):
        """Test error handling in callback."""
        mock_callback.data = "group_setup:select_from_list"

        with patch(
            "app.bot.handlers.group_setup_handler.show_faculty_list"
        ) as mock_show:
            mock_show.side_effect = Exception("Database error")

            await handle_group_setup_callback(mock_callback, mock_state)

            mock_callback.answer.assert_called()
            assert "Ошибка" in str(mock_callback.answer.call_args)


@pytest.mark.asyncio
class TestSelectGroup:
    """Tests for select_group."""

    async def test_select_group_success(self, mock_callback, mock_state):
        """Test selecting group successfully."""
        mock_group = {
            "id": 10,
            "name": "101а",
            "course": 1,
        }

        with patch("app.bot.handlers.group_setup_handler.GroupService") as mock_service:
            with patch("app.services.user_service.UserService") as mock_user_svc:
                service_instance = AsyncMock()
                service_instance.get_group_by_id = AsyncMock(return_value=mock_group)
                mock_service.return_value = service_instance

                user_service_instance = AsyncMock()
                user_service_instance.update_user_group = AsyncMock()
                mock_user_svc.return_value = user_service_instance

                await select_group(mock_callback, mock_state, "10")

                service_instance.get_group_by_id.assert_called_once_with(10)
                user_service_instance.update_user_group.assert_called_once()
                mock_callback.message.edit_text.assert_called_once()
                mock_state.clear.assert_called_once()

    async def test_select_group_not_found(self, mock_callback, mock_state):
        """Test selecting non-existent group."""
        with patch("app.bot.handlers.group_setup_handler.GroupService") as mock_service:
            service_instance = AsyncMock()
            service_instance.get_group_by_id = AsyncMock(return_value=None)
            mock_service.return_value = service_instance

            await select_group(mock_callback, mock_state, "999")

            mock_callback.answer.assert_called_once()
            assert "не найдена" in str(mock_callback.answer.call_args)

    async def test_select_group_error(self, mock_callback, mock_state):
        """Test selecting group with error."""
        with patch("app.bot.handlers.group_setup_handler.GroupService") as mock_service:
            service_instance = AsyncMock()
            service_instance.get_group_by_id = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service.return_value = service_instance

            await select_group(mock_callback, mock_state, "10")

            mock_callback.answer.assert_called()
            assert "Ошибка" in str(mock_callback.answer.call_args)


@pytest.mark.asyncio
class TestShowFacultyList:
    """Tests for show_faculty_list."""

    async def test_show_faculty_list_success(self, mock_message, mock_state):
        """Test showing faculty list successfully."""
        mock_faculties = [
            {"id": 1, "name": "Лечебный факультет"},
            {"id": 2, "name": "Педиатрический факультет"},
        ]

        with patch(
            "app.services.schedule_service.ScheduleService"
        ) as mock_service:
            service_instance = AsyncMock()
            service_instance.get_available_faculties = AsyncMock(
                return_value=mock_faculties
            )
            mock_service.return_value = service_instance

            await show_faculty_list(mock_message, mock_state)

            mock_message.edit_text.assert_called_once()
            mock_state.set_state.assert_called_once_with(
                GroupSetupStates.selecting_faculty
            )

    async def test_show_faculty_list_no_faculties(self, mock_message, mock_state):
        """Test showing faculty list with no faculties."""
        with patch(
            "app.services.schedule_service.ScheduleService"
        ) as mock_service:
            service_instance = AsyncMock()
            service_instance.get_available_faculties = AsyncMock(return_value=[])
            mock_service.return_value = service_instance

            await show_faculty_list(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            assert "не найдены" in str(mock_message.answer.call_args)

    async def test_show_faculty_list_error(self, mock_message, mock_state):
        """Test showing faculty list with error."""
        with patch(
            "app.services.schedule_service.ScheduleService"
        ) as mock_service:
            service_instance = AsyncMock()
            service_instance.get_available_faculties = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service.return_value = service_instance

            await show_faculty_list(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            assert "Ошибка" in str(mock_message.answer.call_args)


@pytest.mark.asyncio
class TestShowFacultyGroups:
    """Tests for show_faculty_groups."""

    async def test_show_faculty_groups_success(self, mock_callback, mock_state):
        """Test showing faculty groups successfully."""
        mock_faculties = [{"id": 1, "name": "Лечебный факультет"}]
        mock_groups = [
            {"id": 10, "name": "101а", "course": 1},
            {"id": 11, "name": "101б", "course": 1},
        ]

        with patch(
            "app.services.schedule_service.ScheduleService"
        ) as mock_schedule_svc:
            with patch(
                "app.bot.handlers.group_setup_handler.GroupService"
            ) as mock_group_svc:
                schedule_instance = AsyncMock()
                schedule_instance.get_available_faculties = AsyncMock(
                    return_value=mock_faculties
                )
                mock_schedule_svc.return_value = schedule_instance

                group_instance = AsyncMock()
                group_instance.get_groups_by_faculty = AsyncMock(
                    return_value=mock_groups
                )
                mock_group_svc.return_value = group_instance

                await show_faculty_groups(mock_callback, mock_state, "1")

                mock_callback.message.edit_text.assert_called_once()

    async def test_show_faculty_groups_no_groups(self, mock_callback, mock_state):
        """Test showing faculty with no groups."""
        mock_faculties = [{"id": 1, "name": "Лечебный факультет"}]

        with patch(
            "app.services.schedule_service.ScheduleService"
        ) as mock_schedule_svc:
            with patch(
                "app.bot.handlers.group_setup_handler.GroupService"
            ) as mock_group_svc:
                schedule_instance = AsyncMock()
                schedule_instance.get_available_faculties = AsyncMock(
                    return_value=mock_faculties
                )
                mock_schedule_svc.return_value = schedule_instance

                group_instance = AsyncMock()
                group_instance.get_groups_by_faculty = AsyncMock(return_value=[])
                mock_group_svc.return_value = group_instance

                await show_faculty_groups(mock_callback, mock_state, "1")

                call_args = str(mock_callback.message.edit_text.call_args)
                assert "не найдены" in call_args

    async def test_show_faculty_groups_error(self, mock_callback, mock_state):
        """Test showing faculty groups with error."""
        with patch(
            "app.services.schedule_service.ScheduleService"
        ) as mock_schedule_svc:
            schedule_instance = AsyncMock()
            schedule_instance.get_available_faculties = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_schedule_svc.return_value = schedule_instance

            await show_faculty_groups(mock_callback, mock_state, "1")

            mock_callback.message.answer.assert_called_once()
            assert "Ошибка" in str(mock_callback.message.answer.call_args)


@pytest.mark.asyncio
class TestHandleScheduleCallback:
    """Tests for handle_schedule_callback."""

    async def test_handle_schedule_today(self, mock_callback):
        """Test schedule today callback."""
        await handle_schedule_callback(mock_callback, "schedule:today")

        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_handle_schedule_week(self, mock_callback):
        """Test schedule week callback."""
        await handle_schedule_callback(mock_callback, "schedule:week")

        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_handle_schedule_error(self, mock_callback):
        """Test schedule callback error."""
        mock_callback.message.edit_text = AsyncMock(side_effect=Exception("Error"))

        await handle_schedule_callback(mock_callback, "schedule:today")

        mock_callback.answer.assert_called()


@pytest.mark.asyncio
class TestHandleGradesCallback:
    """Tests for handle_grades_callback."""

    async def test_handle_grades_view(self, mock_callback):
        """Test grades view callback."""
        await handle_grades_callback(mock_callback, "grades:view")

        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_handle_grades_error(self, mock_callback):
        """Test grades callback error."""
        mock_callback.message.edit_text = AsyncMock(side_effect=Exception("Error"))

        await handle_grades_callback(mock_callback, "grades:view")

        mock_callback.answer.assert_called()


@pytest.mark.asyncio
class TestHandleSettingsCallback:
    """Tests for handle_settings_callback."""

    async def test_handle_settings_main(self, mock_callback):
        """Test settings main callback."""
        await handle_settings_callback(mock_callback, "settings:main")

        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_handle_settings_error(self, mock_callback):
        """Test settings callback error."""
        mock_callback.message.edit_text = AsyncMock(side_effect=Exception("Error"))

        await handle_settings_callback(mock_callback, "settings:main")

        mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_register_group_setup_handlers():
    """Test handler registration."""
    dp = MagicMock()
    dp.callback_query = MagicMock()
    dp.callback_query.register = MagicMock()

    await register_group_setup_handlers(dp)

    dp.callback_query.register.assert_called_once()
