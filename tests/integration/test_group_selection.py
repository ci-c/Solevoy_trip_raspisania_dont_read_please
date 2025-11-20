"""
Integration tests for Group Selection flow.

Tests aligned with Constitution Principle IV: Tests Before Code

Priority: P0 - Critical
User Story: Group Selection and Management Works Reliably

These tests verify that faculty lists load correctly, group search works,
and group assignment doesn't fail or corrupt data.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.group_service import GroupService
from app.services.faculty_service import FacultyService
from app.services.user_service import UserService
from app.database.models import Group
from app.database.models import Faculty


@pytest.mark.integration
@pytest.mark.asyncio
class TestGroupSelection:
    """Test group selection flow end-to-end."""

    async def test_faculty_list_retrieval(
        self,
        db_session: AsyncSession,
        sample_faculty
    ):
        """
        Test that faculty list can be retrieved from database.

        CRITICAL: Verifies faculty selection step doesn't fail.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        faculty_service = FacultyService()

        # Create multiple faculties
        faculty1 = Faculty(**sample_faculty)
        faculty2_data = {**sample_faculty, "name": "Педиатрический факультет", "short_name": "ПФ"}
        faculty2 = Faculty(**faculty2_data)

        db_session.add(faculty1)
        db_session.add(faculty2)
        await db_session.commit()

        # Act
        faculties = await faculty_service.get_all_faculties()

        # Assert
        assert len(faculties) >= 2
        assert any(f.name == sample_faculty["name"] for f in faculties)
        assert any(f.name == "Педиатрический факультет" for f in faculties)

    async def test_empty_faculty_list_handling(
        self,
        clean_db: AsyncSession
    ):
        """
        Test that empty faculty list is handled gracefully.

        Verifies no crash when no faculties exist yet.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        faculty_service = FacultyService()

        # Act
        faculties = await faculty_service.get_all_faculties()

        # Assert - Empty list returned, no exception
        assert faculties == []

    async def test_groups_by_faculty_retrieval(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group
    ):
        """
        Test that groups can be retrieved filtered by faculty.

        Verifies FK relationship between Faculty and Group works.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        group_service = GroupService()

        # Create faculty
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        # Create groups for this faculty
        group1_data = {**sample_group, "faculty_id": faculty.id, "name": "101а"}
        group2_data = {**sample_group, "faculty_id": faculty.id, "name": "101б"}
        group1 = Group(**group1_data)
        group2 = Group(**group2_data)

        db_session.add(group1)
        db_session.add(group2)
        await db_session.commit()

        # Act
        groups = await group_service.get_groups_by_faculty(faculty.id)

        # Assert
        assert len(groups) >= 2
        assert all(g["faculty_id"] == faculty.id for g in groups)
        assert any(g["name"] == "101а" for g in groups)
        assert any(g["name"] == "101б" for g in groups)

    async def test_empty_group_list_for_faculty(
        self,
        db_session: AsyncSession,
        sample_faculty
    ):
        """
        Test handling of faculty with no groups.

        Verifies graceful handling when faculty exists but has no groups yet.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        group_service = GroupService()

        # Create faculty with no groups
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        # Act
        groups = await group_service.get_groups_by_faculty(faculty.id)

        # Assert - Empty list, no crash
        assert groups == []

    async def test_group_search_by_number(
        self,
        db_session: AsyncSession,
        sample_faculty,
        sample_group
    ):
        """
        Test group search by number works correctly.

        Verifies search functionality for group selection.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        group_service = GroupService()

        # Create faculty and groups
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group1_data = {**sample_group, "faculty_id": faculty.id, "name": "101а"}
        group2_data = {**sample_group, "faculty_id": faculty.id, "name": "202б"}
        group1 = Group(**group1_data)
        group2 = Group(**group2_data)

        db_session.add(group1)
        db_session.add(group2)
        await db_session.commit()

        # Act - Search for specific group
        results = await group_service.search_groups("101а")

        # Assert
        assert len(results) >= 1
        assert any(g.name == "101а" for g in results)
        # Should not include unrelated groups
        assert not any(g.name == "202б" for g in results)

    async def test_group_assignment_to_user(
        self,
        db_session: AsyncSession,
        sample_telegram_user,
        sample_faculty,
        sample_group
    ):
        """
        Test assigning group to user works correctly.

        CRITICAL: Verifies group assignment doesn't corrupt data.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        user_service = UserService()
        group_service = GroupService()

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

        # Act - Assign group
        await user_service.set_user_group(user.telegram_id, group.id)

        # Assert - Assignment persisted
        updated_user = await user_service.get_user(user.telegram_id)
        assert updated_user.selected_group_id == group.id

        # Assert - Can retrieve group through relationship
        user_group = await group_service.get_group(updated_user.selected_group_id)
        assert user_group.id == group.id

    async def test_group_reassignment(
        self,
        db_session: AsyncSession,
        sample_telegram_user,
        sample_faculty,
        sample_group
    ):
        """
        Test changing user's group assignment.

        Verifies users can change groups without data corruption.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-002
        """
        # Arrange
        user_service = UserService()

        # Create user
        user = await user_service.get_or_create_user(
            telegram_id=sample_telegram_user["id"],
            telegram_username=sample_telegram_user["username"],
            full_name=sample_telegram_user["first_name"]
        )

        # Create faculty and two groups
        faculty = Faculty(**sample_faculty)
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)

        group1_data = {**sample_group, "faculty_id": faculty.id, "name": "101а"}
        group2_data = {**sample_group, "faculty_id": faculty.id, "name": "102а"}
        group1 = Group(**group1_data)
        group2 = Group(**group2_data)

        db_session.add(group1)
        db_session.add(group2)
        await db_session.commit()
        await db_session.refresh(group1)
        await db_session.refresh(group2)

        # Act - Assign first group
        await user_service.set_user_group(user.telegram_id, group1.id)
        first_assignment = await user_service.get_user(user.telegram_id)
        assert first_assignment.selected_group_id == group1.id

        # Act - Reassign to second group
        await user_service.set_user_group(user.telegram_id, group2.id)
        second_assignment = await user_service.get_user(user.telegram_id)

        # Assert - Group changed successfully
        assert second_assignment.selected_group_id == group2.id
        assert second_assignment.selected_group_id != group1.id

    async def test_invalid_group_assignment(
        self,
        db_session: AsyncSession,
        sample_telegram_user
    ):
        """
        Test handling of invalid group assignment.

        Verifies validation prevents assigning non-existent groups.
        Reference: specs/003-comprehensive-testing-reliability/spec.md#US-006
        """
        # Arrange
        user_service = UserService()

        # Create user
        user = await user_service.get_or_create_user(
            telegram_id=sample_telegram_user["id"],
            telegram_username=sample_telegram_user["username"],
            full_name=sample_telegram_user["first_name"]
        )

        # Act & Assert - Try to assign non-existent group
        with pytest.raises((ValueError, Exception)):
            await user_service.set_user_group(user.telegram_id, 99999)

        # Verify user's group wasn't changed
        unchanged_user = await user_service.get_user(user.telegram_id)
        assert unchanged_user.selected_group_id is None
