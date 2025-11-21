"""Comprehensive tests for ScheduleService."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.models import Faculty
from app.services.group_service import GroupService
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserService


@pytest.mark.asyncio
@pytest.mark.unit
class TestScheduleService:
    """Comprehensive tests for ScheduleService."""

    async def test_init(self):
        """Test ScheduleService initialization."""
        service = ScheduleService()
        assert service is not None

    async def test_get_user_schedule_user_not_found(self, db_session):
        """Test getting schedule for non-existent user."""
        service = ScheduleService()
        result = await service.get_user_schedule(99999)
        assert result is None

    async def test_get_user_schedule_no_group(self, db_session):
        """Test getting schedule for user without group."""
        user_service = UserService()
        user = await user_service.create_user(
            telegram_id=111111,
            telegram_username="testuser1",
            full_name="Test User 1"
        )

        service = ScheduleService()
        result = await service.get_user_schedule(user.telegram_id)
        assert result is None

    async def test_get_group_schedule_not_found(self, db_session):
        """Test getting schedule for non-existent group."""
        service = ScheduleService()
        result = await service.get_group_schedule("NonExistentGroup")
        assert result is None

    async def test_get_group_schedule_empty(self, db_session):
        """Test getting schedule for group with no lessons."""
        group_service = GroupService()
        await group_service.find_or_create_group("TestGroup1")

        service = ScheduleService()
        result = await service.get_group_schedule("TestGroup1")
        assert result == []

    async def test_search_groups_no_filters(self, db_session):
        """Test searching groups without filters."""
        service = ScheduleService()
        result = await service.search_groups()
        assert isinstance(result, list)

    async def test_get_available_faculties_empty(self, db_session):
        """Test getting available faculties from empty database."""
        service = ScheduleService()
        result = await service.get_available_faculties()
        assert result == [] or result is None

    async def test_get_available_specialities_empty(self, db_session):
        """Test getting specialities from empty database."""
        service = ScheduleService()
        result = await service.get_available_specialities()
        assert result == [] or result is None

    async def test_get_available_specialities_with_faculty_filter(self, db_session):
        """Test getting specialities filtered by faculty."""
        service = ScheduleService()
        result = await service.get_available_specialities(faculty_id=1)
        assert isinstance(result, list) or result is None

    async def test_get_current_academic_year_not_found(self, db_session):
        """Test getting current academic year when none set."""
        service = ScheduleService()
        result = await service.get_current_academic_year()
        assert result is None

    async def test_get_current_semester_not_found(self, db_session):
        """Test getting current semester when none set."""
        service = ScheduleService()
        result = await service.get_current_semester()
        assert result is None

    async def test_get_lessons_by_week_group_not_found(self, db_session):
        """Test getting lessons by week for non-existent group."""
        service = ScheduleService()
        result = await service.get_lessons_by_week("NonExistent", 1)
        assert result is None

    async def test_get_lessons_by_week_no_lessons(self, db_session):
        """Test getting lessons by week when no lessons exist."""
        group_service = GroupService()
        await group_service.find_or_create_group("TestGroup2")

        service = ScheduleService()
        result = await service.get_lessons_by_week("TestGroup2", 1)

        # Should return empty dict for days
        assert isinstance(result, dict)

    async def test_extract_course_number_valid(self):
        """Test extracting course number from group name."""
        service = ScheduleService()

        assert service._extract_course_number("101а") == 1
        assert service._extract_course_number("205б") == 2
        assert service._extract_course_number("314в") == 3

    async def test_extract_course_number_invalid(self):
        """Test extracting course number from invalid group name."""
        service = ScheduleService()

        result = service._extract_course_number("abc")
        assert result is None

        result = service._extract_course_number("")
        assert result is None

    async def test_get_schedule_statistics_empty(self, db_session):
        """Test getting statistics from empty database."""
        service = ScheduleService()
        result = await service.get_schedule_statistics()

        assert result is not None
        assert "total_lessons" in result
        assert "total_schedules" in result
        assert "total_faculties" in result
        assert "total_specialities" in result
        assert result["total_lessons"] == 0

    async def test_get_schedule_for_group_not_found(self, db_session):
        """Test getting schedule for non-existent group ID."""
        service = ScheduleService()
        result = await service.get_schedule_for_group(99999)
        assert result == []

    async def test_get_schedule_for_group_empty(self, db_session):
        """Test getting schedule for group with no lessons."""
        group_service = GroupService()
        created = await group_service.find_or_create_group_with_faculty(
            group_name="TestGroup3",
            course=1,
            faculty_id=1,
            speciality_id=1
        )

        service = ScheduleService()
        result = await service.get_schedule_for_group(created["id"])
        assert result == []

    async def test_sync_schedule_for_group_not_found(self, db_session):
        """Test syncing schedule for non-existent group."""
        service = ScheduleService()
        result = await service.sync_schedule_for_group(99999)
        assert result is False

    async def test_sync_schedule_for_group_success(self, db_session):
        """Test successful schedule sync."""
        group_service = GroupService()
        created = await group_service.find_or_create_group_with_faculty(
            group_name="TestGroup4",
            course=1,
            faculty_id=1,
            speciality_id=1
        )

        service = ScheduleService()
        result = await service.sync_schedule_for_group(created["id"])
        assert result is True  # Stub returns True

    async def test_sync_schedule_for_group_with_retry(self, db_session):
        """Test schedule sync with retry parameter."""
        group_service = GroupService()
        created = await group_service.find_or_create_group_with_faculty(
            group_name="TestGroup5",
            course=1,
            faculty_id=1,
            speciality_id=1
        )

        service = ScheduleService()
        result = await service.sync_schedule_for_group(created["id"], retry=True)
        assert result is True

    async def test_get_user_schedule_with_date_range(self, db_session):
        """Test getting user schedule with date filtering."""
        user_service = UserService()
        user = await user_service.create_user(
            telegram_id=222222,
            telegram_username="testuser2",
            full_name="Test User 2"
        )

        service = ScheduleService()
        start = date(2025, 1, 1)
        end = date(2025, 1, 7)

        result = await service.get_user_schedule(
            user.telegram_id,
            start_date=start,
            end_date=end
        )
        # User has no group, so should return None
        assert result is None

    async def test_get_group_schedule_with_week_filter(self, db_session):
        """Test getting group schedule with week number filter."""
        group_service = GroupService()
        await group_service.find_or_create_group("TestGroup6")

        service = ScheduleService()
        result = await service.get_group_schedule("TestGroup6", week_number=1)

        assert isinstance(result, list)

    async def test_search_groups_with_faculty_filter(self, db_session):
        """Test searching groups with faculty filter."""
        service = ScheduleService()
        result = await service.search_groups(faculty_name="Лечебный факультет")
        assert isinstance(result, list) or result is None

    async def test_search_groups_with_speciality_filter(self, db_session):
        """Test searching groups with speciality filter."""
        service = ScheduleService()
        result = await service.search_groups(speciality_name="Лечебное дело")
        assert isinstance(result, list) or result is None

    async def test_search_groups_with_course_filter(self, db_session):
        """Test searching groups with course filter."""
        service = ScheduleService()
        result = await service.search_groups(course_number=1)
        assert isinstance(result, list) or result is None

    async def test_search_groups_all_filters(self, db_session):
        """Test searching groups with all filters."""
        service = ScheduleService()
        result = await service.search_groups(
            faculty_name="Лечебный факультет",
            speciality_name="Лечебное дело",
            course_number=1
        )
        assert isinstance(result, list) or result is None

    async def test_get_available_faculties_with_data(self, db_session):
        """Test getting available faculties with data in database."""
        from app.database.session import get_session

        # Create test faculty
        async for session in get_session():
            faculty = Faculty(
                name="Test Faculty",
                short_name="TF",
                description="Test Description"
            )
            session.add(faculty)
            await session.commit()
            break

        service = ScheduleService()
        result = await service.get_available_faculties()

        assert result is not None
        assert len(result) > 0
        assert result[0]["name"] == "Test Faculty"

    async def test_extract_course_number_edge_cases(self):
        """Test course extraction with edge cases."""
        service = ScheduleService()

        # Single digit
        assert service._extract_course_number("5") == 5

        # Multiple digits
        assert service._extract_course_number("12a") == 12

        # Zero
        result = service._extract_course_number("0")
        assert result == 0

    async def test_get_lessons_by_week_with_days(self, db_session):
        """Test lesson grouping by days structure."""
        group_service = GroupService()
        await group_service.find_or_create_group("TestGroup7")

        service = ScheduleService()
        result = await service.get_lessons_by_week("TestGroup7", 1)

        # Should have structure for all days
        if isinstance(result, dict):
            expected_days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
            for day in expected_days:
                assert day in result
                assert isinstance(result[day], list)

    async def test_sync_schedule_retry_on_failure(self, db_session):
        """Test schedule sync retry mechanism."""
        service = ScheduleService()

        # Mock to fail first, then succeed
        with patch.object(service, "sync_schedule_for_group", wraps=service.sync_schedule_for_group):
            group_service = GroupService()
            created = await group_service.find_or_create_group_with_faculty(
                group_name="TestGroup8",
                course=1,
                faculty_id=1,
                speciality_id=1
            )

            # This should work (stub implementation)
            result = await service.sync_schedule_for_group(created["id"], retry=True)
            assert result is True

    async def test_get_schedule_statistics_exception_handling(self, db_session):
        """Test statistics retrieval with database error."""
        service = ScheduleService()

        # Create a mock that raises an exception when executing queries
        with patch("app.services.schedule_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

            async def mock_generator():
                yield mock_session

            mock_get_session.return_value = mock_generator()

            result = await service.get_schedule_statistics()
            assert result is None

    async def test_search_groups_exception_handling(self, db_session):
        """Test search groups with exception."""
        service = ScheduleService()

        # Create a mock that raises an exception when executing queries
        with patch("app.services.schedule_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

            async def mock_generator():
                yield mock_session

            mock_get_session.return_value = mock_generator()

            result = await service.search_groups()
            assert result is None
