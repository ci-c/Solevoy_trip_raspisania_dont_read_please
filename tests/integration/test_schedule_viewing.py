"""
Integration tests for Schedule Viewing flow.

Tests aligned with Constitution Principle IV: Tests Before Code

Priority: P0 - Critical
User Story: Schedule Viewing Works Without Crashes

These tests verify that schedule display works with proper JOINs,
handles nullable foreign keys correctly, and doesn't crash on edge cases.
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.schedule_service import ScheduleService
from app.services.group_service import GroupService
from app.services.user_service import UserService
from app.database.models import Schedule
from app.database.models import Group
from app.database.models import Faculty


@pytest.mark.integration
@pytest.mark.asyncio
class TestScheduleViewing:
    """Test schedule viewing and display functionality."""

    async def test_get_schedule_for_group(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group,
        sample_schedule_lesson
    ):
        """
        Test retrieving schedule for a specific group.

        CRITICAL: Verifies basic schedule retrieval works.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-003
        """
        # Arrange
        schedule_service = ScheduleService()

        # Create faculty and group
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group_data = {**sample_group, "faculty_id": faculty.id}
        group = Group(**group_data)
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        # Create schedule lesson
        lesson_data = {**sample_schedule_lesson, "group_id": group.id}
        lesson = Schedule(**lesson_data)
        db_session.add(lesson)
        await db_session.commit()

        # Act
        schedule = await schedule_service.get_schedule_for_group(
            group_id=group.id,
            date=sample_schedule_lesson["date"]
        )

        # Assert
        assert schedule is not None
        assert len(schedule) >= 1
        assert schedule[0].group_id == group.id

    async def test_empty_schedule_handling(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group
    ):
        """
        Test handling of empty schedule (no lessons for group).

        Verifies graceful handling when group has no schedule yet.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-003
        """
        # Arrange
        schedule_service = ScheduleService()

        # Create faculty and group with no schedule
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group_data = {**sample_group, "faculty_id": faculty.id}
        group = Group(**group_data)
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        # Act
        schedule = await schedule_service.get_schedule_for_group(
            group_id=group.id,
            date=date.today()
        )

        # Assert - Empty schedule, no crash
        assert schedule == []

    async def test_schedule_date_filtering(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group,
        sample_schedule_lesson
    ):
        """
        Test that schedule is correctly filtered by date.

        Verifies date-based queries work correctly.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-003
        """
        # Arrange
        schedule_service = ScheduleService()

        # Create faculty and group
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group_data = {**sample_group, "faculty_id": faculty.id}
        group = Group(**group_data)
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        # Create lessons on different dates
        today = date.today()
        tomorrow = today + timedelta(days=1)

        lesson_today_data = {**sample_schedule_lesson, "group_id": group.id, "date": today}
        lesson_tomorrow_data = {**sample_schedule_lesson, "group_id": group.id, "date": tomorrow}

        lesson_today = Schedule(**lesson_today_data)
        lesson_tomorrow = Schedule(**lesson_tomorrow_data)

        db_session.add(lesson_today)
        db_session.add(lesson_tomorrow)
        await db_session.commit()

        # Act - Get today's schedule
        today_schedule = await schedule_service.get_schedule_for_group(
            group_id=group.id,
            date=today
        )

        # Assert - Only today's lesson returned
        assert len(today_schedule) >= 1
        assert all(lesson.date == today for lesson in today_schedule)

    async def test_schedule_with_nullable_foreign_keys(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group,
        sample_schedule_lesson
    ):
        """
        Test schedule handling when foreign keys are nullable.

        CRITICAL: Verifies JOINs work with nullable FKs.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-003
        """
        # Arrange
        schedule_service = ScheduleService()

        # Create faculty and group
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group_data = {**sample_group, "faculty_id": faculty.id}
        group = Group(**group_data)
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        # Create schedule with some nullable fields set to None
        lesson_data = {
            **sample_schedule_lesson,
            "group_id": group.id,
            "teacher_name": None,  # Nullable
            "room_number": None,   # Nullable
        }
        lesson = Schedule(**lesson_data)
        db_session.add(lesson)
        await db_session.commit()

        # Act
        schedule = await schedule_service.get_schedule_for_group(
            group_id=group.id,
            date=sample_schedule_lesson["date"]
        )

        # Assert - Schedule retrieved despite nullable fields
        assert len(schedule) >= 1
        assert schedule[0].teacher_name is None
        assert schedule[0].room_number is None

    async def test_schedule_for_user_group(
        self,
        db_session: AsyncSession,
        sample_telegram_user,
        sample_faculty,
        sample_group,
        sample_schedule_lesson
    ):
        """
        Test retrieving schedule for user's selected group.

        Verifies complete JOIN: User -> Group -> Schedule.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-003
        """
        # Arrange
        user_service = UserService()
        schedule_service = ScheduleService()

        # Create user
        user = await user_service.get_or_create_user(
            telegram_id=sample_telegram_user["id"],
            telegram_username=sample_telegram_user["username"],
            full_name=sample_telegram_user["first_name"]
        )

        # Create faculty and group
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group_data = {**sample_group, "faculty_id": faculty.id}
        group = Group(**group_data)
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        # Assign group to user
        await user_service.set_user_group(user.telegram_id, group.id)

        # Create schedule
        lesson_data = {**sample_schedule_lesson, "group_id": group.id}
        lesson = Schedule(**lesson_data)
        db_session.add(lesson)
        await db_session.commit()

        # Act - Get schedule for user's group
        updated_user = await user_service.get_user(user.telegram_id)
        schedule = await schedule_service.get_schedule_for_group(
            group_id=updated_user.selected_group_id,
            date=sample_schedule_lesson["date"]
        )

        # Assert
        assert len(schedule) >= 1
        assert schedule[0].group_id == group.id

    async def test_schedule_with_multiple_lessons(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group,
        multiple_lessons
    ):
        """
        Test schedule display with multiple lessons.

        Verifies ordering and filtering work correctly.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-003
        """
        # Arrange
        schedule_service = ScheduleService()

        # Create faculty and group
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group_data = {**sample_group, "faculty_id": faculty.id}
        group = Group(**group_data)
        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        # Create multiple lessons
        for lesson_data in multiple_lessons:
            lesson = Schedule(**{**lesson_data, "group_id": group.id})
            db_session.add(lesson)
        await db_session.commit()

        # Act
        schedule = await schedule_service.get_schedule_for_group(
            group_id=group.id,
            date=multiple_lessons[0]["date"]
        )

        # Assert
        assert len(schedule) >= len(multiple_lessons)
        # Verify lessons are ordered by start_time
        start_times = [lesson.start_time for lesson in schedule]
        assert start_times == sorted(start_times)

    async def test_schedule_invalid_group_id(
        self,
        db_session: AsyncSession
    ):
        """
        Test handling of invalid group ID in schedule query.

        Verifies graceful error handling for invalid inputs.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-006
        """
        # Arrange
        schedule_service = ScheduleService()

        # Act - Try to get schedule for non-existent group
        schedule = await schedule_service.get_schedule_for_group(
            group_id=99999,
            date=date.today()
        )

        # Assert - Empty schedule returned (or raises exception)
        # Either behavior is acceptable as long as it doesn't crash
        assert schedule == [] or schedule is None
