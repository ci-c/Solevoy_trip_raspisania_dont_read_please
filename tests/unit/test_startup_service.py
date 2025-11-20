"""Tests for startup service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.startup_service import StartupService


@pytest.fixture
def service():
    """Create service instance."""
    return StartupService()


@pytest.mark.asyncio
class TestInitializeSystem:
    """Tests for initialize_system."""

    async def test_initialize_system_success_with_faculties(self, service):
        """Test initializing system successfully with existing faculties."""
        mock_faculties = [{"id": 1, "name": "Лечебный"}]
        mock_stats = {"total_schedules": 10, "total_lessons": 100}
        mock_semester = {"name": "Осенний 2024/2025"}
        mock_year = {"name": "2024/2025"}

        with patch.object(
            service.schedule_service,
            "get_available_faculties",
            return_value=mock_faculties,
        ):
            with patch.object(
                service.schedule_service,
                "get_schedule_statistics",
                return_value=mock_stats,
            ):
                with patch.object(
                    service.schedule_service,
                    "get_current_semester",
                    return_value=mock_semester,
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_academic_year",
                        return_value=mock_year,
                    ):
                        with patch(
                            "app.services.group_service.GroupService"
                        ) as mock_group_svc:
                            group_instance = AsyncMock()
                            group_instance.get_groups_count = AsyncMock(return_value=5)
                            mock_group_svc.return_value = group_instance

                            result = await service.initialize_system()

                            assert result is not None
                            assert result["faculties_loaded"] is True
                            assert result["database_ready"] is True
                            assert len(result["errors"]) == 0

    async def test_initialize_system_no_faculties(self, service):
        """Test initializing system with no faculties."""
        mock_stats = {"total_schedules": 10}

        with patch.object(
            service.schedule_service, "get_available_faculties", return_value=[]
        ):
            with patch.object(
                service.schedule_service,
                "get_schedule_statistics",
                return_value=mock_stats,
            ):
                with patch.object(
                    service.schedule_service, "get_current_semester", return_value=None
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_academic_year",
                        return_value=None,
                    ):
                        with patch(
                            "app.services.group_service.GroupService"
                        ) as mock_group_svc:
                            group_instance = AsyncMock()
                            group_instance.get_groups_count = AsyncMock(return_value=0)
                            mock_group_svc.return_value = group_instance

                            with patch.object(
                                service.api_sync_service,
                                "_create_groups_from_lessons",
                                return_value=None,
                            ):
                                with patch("asyncio.create_task"):
                                    result = await service.initialize_system()

                                    assert result is not None
                                    assert result["faculties_loaded"] is False

    async def test_initialize_system_database_not_ready(self, service):
        """Test initializing system when database not ready."""
        mock_faculties = [{"id": 1, "name": "Лечебный"}]

        with patch.object(
            service.schedule_service,
            "get_available_faculties",
            return_value=mock_faculties,
        ):
            with patch.object(
                service.schedule_service, "get_schedule_statistics", return_value=None
            ):
                with patch.object(
                    service.schedule_service, "get_current_semester", return_value=None
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_academic_year",
                        return_value=None,
                    ):
                        with patch(
                            "app.services.group_service.GroupService"
                        ) as mock_group_svc:
                            group_instance = AsyncMock()
                            group_instance.get_groups_count = AsyncMock(return_value=5)
                            mock_group_svc.return_value = group_instance

                            result = await service.initialize_system()

                            assert result is not None
                            assert result["database_ready"] is False
                            assert "Database not ready" in result["errors"]

    async def test_initialize_system_error(self, service):
        """Test initializing system with error."""
        with patch.object(
            service.schedule_service,
            "get_available_faculties",
            side_effect=Exception("Database error"),
        ):
            result = await service.initialize_system()

            assert result is not None
            assert len(result["errors"]) > 0


@pytest.mark.asyncio
class TestBackgroundSync:
    """Tests for _background_sync."""

    async def test_background_sync_success(self, service):
        """Test background sync successfully."""
        with patch.object(
            service.api_sync_service, "full_sync", return_value=True
        ) as mock_sync:
            await service._background_sync()

            mock_sync.assert_called_once()

    async def test_background_sync_failure(self, service):
        """Test background sync failure."""
        with patch.object(
            service.api_sync_service, "full_sync", return_value=False
        ) as mock_sync:
            await service._background_sync()

            mock_sync.assert_called_once()

    async def test_background_sync_error(self, service):
        """Test background sync with error."""
        with patch.object(
            service.api_sync_service,
            "full_sync",
            side_effect=Exception("Sync error"),
        ) as mock_sync:
            await service._background_sync()

            mock_sync.assert_called_once()


@pytest.mark.asyncio
class TestCheckSystemHealth:
    """Tests for check_system_health."""

    async def test_check_system_health_healthy(self, service):
        """Test checking system health when healthy."""
        mock_stats = {"total_schedules": 10, "total_lessons": 100}
        mock_faculties = [{"id": 1, "name": "Лечебный"}]
        mock_specialities = [{"id": 1, "name": "31.05.01"}]
        mock_semester = {"name": "Осенний 2024/2025"}

        with patch.object(
            service.schedule_service,
            "get_schedule_statistics",
            return_value=mock_stats,
        ):
            with patch.object(
                service.schedule_service,
                "get_available_faculties",
                return_value=mock_faculties,
            ):
                with patch.object(
                    service.schedule_service,
                    "get_available_specialities",
                    return_value=mock_specialities,
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_semester",
                        return_value=mock_semester,
                    ):
                        result = await service.check_system_health()

                        assert result is not None
                        assert result["status"] == "healthy"
                        assert len(result["issues"]) == 0

    async def test_check_system_health_database_unhealthy(self, service):
        """Test checking system health when database unhealthy."""
        with patch.object(
            service.schedule_service, "get_schedule_statistics", return_value=None
        ):
            with patch.object(
                service.schedule_service, "get_available_faculties", return_value=[]
            ):
                with patch.object(
                    service.schedule_service,
                    "get_available_specialities",
                    return_value=[],
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_semester",
                        return_value=None,
                    ):
                        result = await service.check_system_health()

                        assert result is not None
                        assert result["status"] == "unhealthy"
                        assert len(result["issues"]) > 0

    async def test_check_system_health_no_semester_warning(self, service):
        """Test checking system health with no semester (warning)."""
        mock_stats = {"total_schedules": 10}
        mock_faculties = [{"id": 1, "name": "Лечебный"}]
        mock_specialities = [{"id": 1, "name": "31.05.01"}]

        with patch.object(
            service.schedule_service,
            "get_schedule_statistics",
            return_value=mock_stats,
        ):
            with patch.object(
                service.schedule_service,
                "get_available_faculties",
                return_value=mock_faculties,
            ):
                with patch.object(
                    service.schedule_service,
                    "get_available_specialities",
                    return_value=mock_specialities,
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_semester",
                        return_value=None,
                    ):
                        result = await service.check_system_health()

                        assert result is not None
                        assert result["status"] == "warning"
                        assert any("semester" in issue.lower() for issue in result["issues"])

    async def test_check_system_health_error(self, service):
        """Test checking system health with error."""
        with patch.object(
            service.schedule_service,
            "get_schedule_statistics",
            side_effect=Exception("Database error"),
        ):
            result = await service.check_system_health()

            assert result is not None
            assert result["status"] == "unhealthy"
            assert len(result["issues"]) > 0


@pytest.mark.asyncio
class TestWarmUpCache:
    """Tests for warm_up_cache."""

    async def test_warm_up_cache_success(self, service):
        """Test warming up cache successfully."""
        mock_faculties = [{"id": 1, "name": "Лечебный"}]
        mock_specialities = [{"id": 1, "name": "31.05.01"}]
        mock_semester = {"name": "Осенний 2024/2025"}
        mock_year = {"name": "2024/2025"}

        with patch.object(
            service.schedule_service,
            "get_available_faculties",
            return_value=mock_faculties,
        ):
            with patch.object(
                service.schedule_service,
                "get_available_specialities",
                return_value=mock_specialities,
            ):
                with patch.object(
                    service.schedule_service,
                    "get_current_semester",
                    return_value=mock_semester,
                ):
                    with patch.object(
                        service.schedule_service,
                        "get_current_academic_year",
                        return_value=mock_year,
                    ):
                        await service.warm_up_cache()

                        # Should call all methods
                        service.schedule_service.get_available_faculties.assert_called_once()

    async def test_warm_up_cache_error(self, service):
        """Test warming up cache with error."""
        with patch.object(
            service.schedule_service,
            "get_available_faculties",
            side_effect=Exception("Cache error"),
        ):
            await service.warm_up_cache()

            # Should handle error gracefully


@pytest.mark.asyncio
class TestRunStartupChecks:
    """Tests for run_startup_checks."""

    async def test_run_startup_checks_success(self, service):
        """Test running startup checks successfully."""
        mock_init_results = {"errors": []}
        mock_health = {"status": "healthy", "issues": []}

        with patch.object(
            service, "initialize_system", return_value=mock_init_results
        ):
            with patch.object(
                service, "check_system_health", return_value=mock_health
            ):
                with patch.object(service, "warm_up_cache", return_value=None):
                    result = await service.run_startup_checks()

                    assert result is True

    async def test_run_startup_checks_health_failure(self, service):
        """Test running startup checks with health failure."""
        mock_init_results = {"errors": []}
        mock_health = {"status": "unhealthy", "issues": ["Database down"]}

        with patch.object(
            service, "initialize_system", return_value=mock_init_results
        ):
            with patch.object(
                service, "check_system_health", return_value=mock_health
            ):
                with patch.object(service, "warm_up_cache", return_value=None):
                    result = await service.run_startup_checks()

                    assert result is False

    async def test_run_startup_checks_with_init_errors(self, service):
        """Test running startup checks with initialization errors."""
        mock_init_results = {"errors": ["Database error"]}
        mock_health = {"status": "healthy", "issues": []}

        with patch.object(
            service, "initialize_system", return_value=mock_init_results
        ):
            with patch.object(
                service, "check_system_health", return_value=mock_health
            ):
                with patch.object(service, "warm_up_cache", return_value=None):
                    result = await service.run_startup_checks()

                    # Still returns True if health is healthy
                    assert result is True

    async def test_run_startup_checks_error(self, service):
        """Test running startup checks with error."""
        with patch.object(
            service,
            "initialize_system",
            side_effect=Exception("Critical error"),
        ):
            result = await service.run_startup_checks()

            assert result is False


def test_service_initialization():
    """Test service initialization."""
    service = StartupService()

    assert service.api_sync_service is not None
    assert service.schedule_service is not None
    assert service.faculty_service is not None
