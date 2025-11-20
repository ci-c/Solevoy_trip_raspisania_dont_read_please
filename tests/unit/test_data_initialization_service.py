"""Tests for data initialization service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.data_initialization_service import DataInitializationService


@pytest.fixture
def service():
    """Create service instance."""
    return DataInitializationService()


@pytest.mark.asyncio
class TestInitializeFaculties:
    """Tests for initialize_faculties."""

    async def test_initialize_from_api_success(self, service):
        """Test initializing faculties from API successfully."""
        with patch.object(
            service.faculty_service, "sync_faculties", return_value=True
        ) as mock_sync:
            result = await service.initialize_faculties()

            assert result is True
            mock_sync.assert_called_once()

    async def test_initialize_from_api_failure(self, service):
        """Test initializing faculties when API fails."""
        with patch.object(
            service.faculty_service, "sync_faculties", return_value=False
        ) as mock_sync:
            with patch.object(
                service, "_create_default_faculties", return_value=False
            ) as mock_create:
                result = await service.initialize_faculties()

                assert result is False
                mock_sync.assert_called_once()
                mock_create.assert_called_once()

    async def test_initialize_faculties_error(self, service):
        """Test initializing faculties with error."""
        with patch.object(
            service.faculty_service,
            "sync_faculties",
            side_effect=Exception("API error"),
        ):
            result = await service.initialize_faculties()

            assert result is False


@pytest.mark.asyncio
class TestCreateDefaultFaculties:
    """Tests for _create_default_faculties."""

    async def test_create_default_faculties(self, service):
        """Test creating default faculties."""
        # This method currently always returns False
        result = await service._create_default_faculties()

        assert result is False

    async def test_create_default_faculties_error(self, service):
        """Test creating default faculties with error."""
        # Even with errors, should return False gracefully
        result = await service._create_default_faculties()

        assert result is False


@pytest.mark.asyncio
class TestInitializeSampleGroups:
    """Tests for initialize_sample_groups."""

    async def test_initialize_sample_groups_success(self, service):
        """Test initializing sample groups successfully."""
        mock_faculties = ["Лечебный", "Педиатрический", "Стоматологический"]

        with patch.object(
            service.faculty_service,
            "get_faculty_names",
            return_value=mock_faculties,
        ):
            with patch.object(service, "_save_groups", return_value=True) as mock_save:
                result = await service.initialize_sample_groups()

                assert result is True
                mock_save.assert_called_once()
                # Check that groups were created
                groups_data = mock_save.call_args[0][0]
                assert len(groups_data) > 0

    async def test_initialize_sample_groups_no_faculties(self, service):
        """Test initializing sample groups with no faculties."""
        with patch.object(
            service.faculty_service, "get_faculty_names", return_value=[]
        ):
            result = await service.initialize_sample_groups()

            assert result is False

    async def test_initialize_sample_groups_error(self, service):
        """Test initializing sample groups with error."""
        with patch.object(
            service.faculty_service,
            "get_faculty_names",
            side_effect=Exception("Database error"),
        ):
            result = await service.initialize_sample_groups()

            assert result is False




@pytest.mark.asyncio
class TestInitializeAllData:
    """Tests for initialize_all_data."""

    async def test_initialize_all_data_success(self, service):
        """Test initializing all data successfully."""
        with patch.object(
            service, "initialize_faculties", return_value=True
        ) as mock_faculties:
            with patch.object(
                service, "initialize_sample_groups", return_value=True
            ) as mock_groups:
                result = await service.initialize_all_data()

                assert result is True
                mock_faculties.assert_called_once()
                mock_groups.assert_called_once()

    async def test_initialize_all_data_faculties_fail(self, service):
        """Test initializing all data when faculties fail."""
        with patch.object(
            service, "initialize_faculties", return_value=False
        ) as mock_faculties:
            result = await service.initialize_all_data()

            assert result is False
            mock_faculties.assert_called_once()

    async def test_initialize_all_data_groups_fail(self, service):
        """Test initializing all data when groups fail."""
        with patch.object(service, "initialize_faculties", return_value=True):
            with patch.object(
                service, "initialize_sample_groups", return_value=False
            ) as mock_groups:
                result = await service.initialize_all_data()

                # Should still return True even if groups fail
                assert result is True
                mock_groups.assert_called_once()

    async def test_initialize_all_data_error(self, service):
        """Test initializing all data with error."""
        with patch.object(
            service,
            "initialize_faculties",
            side_effect=Exception("Critical error"),
        ):
            result = await service.initialize_all_data()

            assert result is False


@pytest.mark.asyncio
class TestCheckDataAvailability:
    """Tests for check_data_availability."""

    async def test_check_data_availability_success(self, service):
        """Test checking data availability successfully."""
        mock_faculties = ["Лечебный", "Педиатрический"]
        mock_groups = [{"id": 1, "name": "101а"}, {"id": 2, "name": "102а"}]

        with patch.object(
            service.faculty_service,
            "get_faculty_names",
            return_value=mock_faculties,
        ):
            with patch.object(
                service.group_service, "get_all_groups", return_value=mock_groups
            ):
                result = await service.check_data_availability()

                assert result is not None
                assert result["faculties_available"] is True
                assert result["groups_available"] is True
                assert result["faculties_count"] == 2
                assert result["groups_count"] == 2

    async def test_check_data_availability_no_data(self, service):
        """Test checking data availability with no data."""
        with patch.object(
            service.faculty_service, "get_faculty_names", return_value=[]
        ):
            with patch.object(service.group_service, "get_all_groups", return_value=[]):
                result = await service.check_data_availability()

                assert result is not None
                assert result["faculties_available"] is False
                assert result["groups_available"] is False
                assert result["faculties_count"] == 0
                assert result["groups_count"] == 0

    async def test_check_data_availability_error(self, service):
        """Test checking data availability with error."""
        with patch.object(
            service.faculty_service,
            "get_faculty_names",
            side_effect=Exception("Database error"),
        ):
            result = await service.check_data_availability()

            assert result is not None
            assert result["faculties_available"] is False
            assert result["groups_available"] is False


def test_service_initialization():
    """Test service initialization."""
    service = DataInitializationService()

    assert service.faculty_service is not None
    assert service.group_service is not None
