"""Tests for invitation handler."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext

from app.bot.callbacks import InvitationCallback
from app.bot.handlers.invitation_handler import (
    handle_create_invitation,
    handle_invitation_main,
    handle_list_invitations,
    handle_use_invitation,
    process_invitation_code,
    register_invitation_handlers,
)
from app.bot.states import InvitationStates
from app.models.user import AccessLevel


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
    message.text = "ABC12345"
    message.answer = AsyncMock()
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
def mock_admin_user():
    """Mock admin user."""
    user = MagicMock()
    user.telegram_id = 123456
    user.full_name = "Admin User"
    user.access_level = AccessLevel.ADMIN
    return user


@pytest.fixture
def mock_basic_user():
    """Mock basic user."""
    user = MagicMock()
    user.telegram_id = 123456
    user.full_name = "Basic User"
    user.access_level = AccessLevel.BASIC
    return user


@pytest.fixture
def mock_invitation():
    """Mock invitation."""
    invitation = MagicMock()
    invitation.code = "ABC12345"
    invitation.access_level = AccessLevel.BASIC
    invitation.max_uses = 5
    invitation.current_uses = 2
    invitation.expires_at = datetime.now() + timedelta(days=30)
    invitation.is_active = True
    return invitation


@pytest.mark.asyncio
class TestHandleInvitationMain:
    """Tests for handle_invitation_main."""

    async def test_admin_user_access(self, mock_callback, mock_state, mock_admin_user):
        """Test admin user accessing invitation system."""
        callback_data = InvitationCallback(action="main")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            with patch("app.bot.handlers.invitation_handler.InvitationService"):
                user_service_instance = AsyncMock()
                user_service_instance.get_user_by_telegram_id = AsyncMock(
                    return_value=mock_admin_user
                )
                mock_user_svc.return_value = user_service_instance

                await handle_invitation_main(mock_callback, callback_data, mock_state)

                mock_callback.answer.assert_called_once()
                mock_callback.message.edit_text.assert_called_once()
                call_args = str(mock_callback.message.edit_text.call_args)
                assert "ADMIN" in call_args or "admin" in call_args.lower()

    async def test_basic_user_access(self, mock_callback, mock_state, mock_basic_user):
        """Test basic user accessing invitation system."""
        callback_data = InvitationCallback(action="main")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            with patch("app.bot.handlers.invitation_handler.InvitationService"):
                user_service_instance = AsyncMock()
                user_service_instance.get_user_by_telegram_id = AsyncMock(
                    return_value=mock_basic_user
                )
                mock_user_svc.return_value = user_service_instance

                await handle_invitation_main(mock_callback, callback_data, mock_state)

                mock_callback.answer.assert_called_once()
                mock_state.set_state.assert_called_once_with(
                    InvitationStates.entering_code
                )

    async def test_user_not_found(self, mock_callback, mock_state):
        """Test user not found."""
        callback_data = InvitationCallback(action="main")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_by_telegram_id = AsyncMock(return_value=None)
            mock_user_svc.return_value = user_service_instance

            await handle_invitation_main(mock_callback, callback_data, mock_state)

            call_args = str(mock_callback.message.edit_text.call_args)
            assert "не найден" in call_args

    async def test_error_handling(self, mock_callback, mock_state):
        """Test error handling."""
        callback_data = InvitationCallback(action="main")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_by_telegram_id = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_user_svc.return_value = user_service_instance

            await handle_invitation_main(mock_callback, callback_data, mock_state)

            call_args = str(mock_callback.message.edit_text.call_args)
            assert "Ошибка" in call_args


@pytest.mark.asyncio
class TestHandleCreateInvitation:
    """Tests for handle_create_invitation."""

    async def test_create_invitation_success(
        self, mock_callback, mock_state, mock_admin_user, mock_invitation
    ):
        """Test creating invitation successfully."""
        callback_data = InvitationCallback(action="create")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            with patch(
                "app.bot.handlers.invitation_handler.InvitationService"
            ) as mock_inv_svc:
                user_service_instance = AsyncMock()
                user_service_instance.get_user_by_telegram_id = AsyncMock(
                    return_value=mock_admin_user
                )
                mock_user_svc.return_value = user_service_instance

                inv_service_instance = AsyncMock()
                inv_service_instance.create_invitation = AsyncMock(
                    return_value=mock_invitation
                )
                mock_inv_svc.return_value = inv_service_instance

                await handle_create_invitation(mock_callback, callback_data, mock_state)

                mock_callback.answer.assert_called_once()
                inv_service_instance.create_invitation.assert_called_once()
                call_args = str(mock_callback.message.edit_text.call_args)
                assert "создан" in call_args.lower()

    async def test_create_invitation_no_permission(
        self, mock_callback, mock_state, mock_basic_user
    ):
        """Test creating invitation without permission."""
        callback_data = InvitationCallback(action="create")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_by_telegram_id = AsyncMock(
                return_value=mock_basic_user
            )
            mock_user_svc.return_value = user_service_instance

            await handle_create_invitation(mock_callback, callback_data, mock_state)

            call_args = str(mock_callback.message.edit_text.call_args)
            assert "нет прав" in call_args

    async def test_create_invitation_error(
        self, mock_callback, mock_state, mock_admin_user
    ):
        """Test creating invitation with error."""
        callback_data = InvitationCallback(action="create")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            with patch(
                "app.bot.handlers.invitation_handler.InvitationService"
            ) as mock_inv_svc:
                user_service_instance = AsyncMock()
                user_service_instance.get_user_by_telegram_id = AsyncMock(
                    return_value=mock_admin_user
                )
                mock_user_svc.return_value = user_service_instance

                inv_service_instance = AsyncMock()
                inv_service_instance.create_invitation = AsyncMock(
                    side_effect=Exception("Database error")
                )
                mock_inv_svc.return_value = inv_service_instance

                await handle_create_invitation(mock_callback, callback_data, mock_state)

                call_args = str(mock_callback.message.edit_text.call_args)
                assert "Ошибка" in call_args


@pytest.mark.asyncio
class TestHandleListInvitations:
    """Tests for handle_list_invitations."""

    async def test_list_invitations_success(
        self, mock_callback, mock_state, mock_admin_user, mock_invitation
    ):
        """Test listing invitations successfully."""
        callback_data = InvitationCallback(action="list")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            with patch(
                "app.bot.handlers.invitation_handler.InvitationService"
            ) as mock_inv_svc:
                user_service_instance = AsyncMock()
                user_service_instance.get_user_by_telegram_id = AsyncMock(
                    return_value=mock_admin_user
                )
                mock_user_svc.return_value = user_service_instance

                inv_service_instance = AsyncMock()
                inv_service_instance.get_user_invitations = AsyncMock(
                    return_value=[mock_invitation]
                )
                mock_inv_svc.return_value = inv_service_instance

                await handle_list_invitations(mock_callback, callback_data, mock_state)

                mock_callback.answer.assert_called_once()
                call_args = str(mock_callback.message.edit_text.call_args)
                assert "ABC12345" in call_args

    async def test_list_invitations_empty(
        self, mock_callback, mock_state, mock_admin_user
    ):
        """Test listing invitations with empty list."""
        callback_data = InvitationCallback(action="list")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            with patch(
                "app.bot.handlers.invitation_handler.InvitationService"
            ) as mock_inv_svc:
                user_service_instance = AsyncMock()
                user_service_instance.get_user_by_telegram_id = AsyncMock(
                    return_value=mock_admin_user
                )
                mock_user_svc.return_value = user_service_instance

                inv_service_instance = AsyncMock()
                inv_service_instance.get_user_invitations = AsyncMock(return_value=[])
                mock_inv_svc.return_value = inv_service_instance

                await handle_list_invitations(mock_callback, callback_data, mock_state)

                call_args = str(mock_callback.message.edit_text.call_args)
                assert "нет" in call_args.lower()

    async def test_list_invitations_no_permission(
        self, mock_callback, mock_state, mock_basic_user
    ):
        """Test listing invitations without permission."""
        callback_data = InvitationCallback(action="list")

        with patch("app.bot.handlers.invitation_handler.UserService") as mock_user_svc:
            user_service_instance = AsyncMock()
            user_service_instance.get_user_by_telegram_id = AsyncMock(
                return_value=mock_basic_user
            )
            mock_user_svc.return_value = user_service_instance

            await handle_list_invitations(mock_callback, callback_data, mock_state)

            call_args = str(mock_callback.message.edit_text.call_args)
            assert "нет прав" in call_args


@pytest.mark.asyncio
class TestHandleUseInvitation:
    """Tests for handle_use_invitation."""

    async def test_use_invitation(self, mock_callback, mock_state):
        """Test use invitation handler."""
        callback_data = InvitationCallback(action="use")

        await handle_use_invitation(mock_callback, callback_data, mock_state)

        mock_callback.answer.assert_called_once()
        mock_state.set_state.assert_called_once_with(InvitationStates.entering_code)

    async def test_use_invitation_error(self, mock_callback, mock_state):
        """Test use invitation error."""
        callback_data = InvitationCallback(action="use")

        mock_state.set_state = AsyncMock(side_effect=Exception("Error"))

        await handle_use_invitation(mock_callback, callback_data, mock_state)

        call_args = str(mock_callback.message.edit_text.call_args)
        assert "Ошибка" in call_args


@pytest.mark.asyncio
class TestProcessInvitationCode:
    """Tests for process_invitation_code."""

    async def test_process_valid_code(
        self, mock_message, mock_state, mock_invitation, mock_basic_user
    ):
        """Test processing valid invitation code."""
        mock_message.text = "abc12345"

        with patch(
            "app.bot.handlers.invitation_handler.InvitationService"
        ) as mock_inv_svc, patch(
            "app.bot.handlers.invitation_handler.UserService"
        ) as mock_user_svc:
            inv_service_instance = AsyncMock()
            inv_service_instance.validate_invitation = AsyncMock(
                return_value=mock_invitation
            )
            inv_service_instance.use_invitation = AsyncMock(return_value=True)
            mock_inv_svc.return_value = inv_service_instance

            user_service_instance = AsyncMock()
            user_service_instance.get_user_by_telegram_id = AsyncMock(
                return_value=mock_basic_user
            )
            user_service_instance.update_user = AsyncMock()
            mock_user_svc.return_value = user_service_instance

            await process_invitation_code(mock_message, mock_state)

            inv_service_instance.use_invitation.assert_called_once_with(
                "ABC12345", 123456
            )
            mock_state.clear.assert_called_once()
            call_args = str(mock_message.answer.call_args)
            assert "успешно" in call_args.lower()

    async def test_process_invalid_code(self, mock_message, mock_state):
        """Test processing invalid invitation code."""
        mock_message.text = "INVALID"

        with patch(
            "app.bot.handlers.invitation_handler.InvitationService"
        ) as mock_inv_svc:
            inv_service_instance = AsyncMock()
            inv_service_instance.validate_invitation = AsyncMock(return_value=None)
            mock_inv_svc.return_value = inv_service_instance

            await process_invitation_code(mock_message, mock_state)

            call_args = str(mock_message.answer.call_args)
            assert "Неверный" in call_args

    async def test_process_code_already_used(
        self, mock_message, mock_state, mock_invitation
    ):
        """Test processing invitation code that's already used."""
        mock_message.text = "ABC12345"

        with patch(
            "app.bot.handlers.invitation_handler.InvitationService"
        ) as mock_inv_svc, patch(
            "app.bot.handlers.invitation_handler.UserService"
        ) as mock_user_svc:
            inv_service_instance = AsyncMock()
            inv_service_instance.validate_invitation = AsyncMock(
                return_value=mock_invitation
            )
            inv_service_instance.use_invitation = AsyncMock(return_value=False)
            mock_inv_svc.return_value = inv_service_instance

            user_service_instance = AsyncMock()
            mock_user_svc.return_value = user_service_instance

            await process_invitation_code(mock_message, mock_state)

            call_args = str(mock_message.answer.call_args)
            assert "Ошибка" in call_args or "использован" in call_args.lower()

    async def test_process_code_error(self, mock_message, mock_state):
        """Test processing invitation code with error."""
        mock_message.text = "ABC12345"

        with patch(
            "app.bot.handlers.invitation_handler.InvitationService"
        ) as mock_inv_svc:
            inv_service_instance = AsyncMock()
            inv_service_instance.validate_invitation = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_inv_svc.return_value = inv_service_instance

            await process_invitation_code(mock_message, mock_state)

            call_args = str(mock_message.answer.call_args)
            assert "Ошибка" in call_args


@pytest.mark.asyncio
async def test_register_invitation_handlers():
    """Test handler registration."""
    dp = MagicMock()
    dp.callback_query = MagicMock()
    dp.callback_query.register = MagicMock()
    dp.message = MagicMock()
    dp.message.register = MagicMock()

    await register_invitation_handlers(dp)

    # Should register multiple callback handlers and one message handler
    assert dp.callback_query.register.call_count >= 4
    assert dp.message.register.call_count >= 1
