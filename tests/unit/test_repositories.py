"""Tests for database repositories."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Group, User
from app.database.repositories.group import GroupRepository
from app.database.repositories.user import UserRepository


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Mock user model."""
    user = MagicMock(spec=User)
    user.id = 1
    user.telegram_id = 123456
    user.telegram_username = "test_user"
    user.full_name = "Test User"
    return user


@pytest.fixture
def mock_group():
    """Mock group model."""
    group = MagicMock(spec=Group)
    group.id = 1
    group.name = "101а"
    group.course = 1
    group.faculty = "Лечебный факультет"
    return group


class TestUserRepository:
    """Tests for UserRepository."""

    def test_initialization(self, mock_session):
        """Test repository initialization."""
        repo = UserRepository(mock_session)

        assert repo._session == mock_session
        assert repo._model == User

    @pytest.mark.asyncio
    async def test_get_by_telegram_id_found(self, mock_session, mock_user):
        """Test getting user by telegram_id when found."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_session)
        user = await repo.get_by_telegram_id(123456)

        assert user == mock_user
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_telegram_id_not_found(self, mock_session):
        """Test getting user by telegram_id when not found."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UserRepository(mock_session)
        user = await repo.get_by_telegram_id(999999)

        assert user is None
        mock_session.execute.assert_called_once()


class TestGroupRepository:
    """Tests for GroupRepository."""

    def test_initialization(self, mock_session):
        """Test repository initialization."""
        repo = GroupRepository(mock_session)

        assert repo._session == mock_session
        assert repo._model == Group

    @pytest.mark.asyncio
    async def test_get_by_name_found(self, mock_session, mock_group):
        """Test getting group by name when found."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_group)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = GroupRepository(mock_session)
        group = await repo.get_by_name("101а")

        assert group == mock_group
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, mock_session):
        """Test getting group by name when not found."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = GroupRepository(mock_session)
        group = await repo.get_by_name("999а")

        assert group is None
        mock_session.execute.assert_called_once()

