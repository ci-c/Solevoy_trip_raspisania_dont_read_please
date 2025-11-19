"""
Сервис для работы с группами студентов.
"""

# Используем встроенные типы Python 3.9+
from typing import Optional, List, Dict
from loguru import logger

from app.database.session import get_session
from app.database.models import Group
from app.utils.validators import validate_group_data, ValidationError
from app.utils.error_monitor import async_error_handler
from sqlalchemy import select


class GroupService:
    """Сервис для управления группами студентов."""

    def __init__(self) -> None:
        pass

    async def get_all_groups(self) -> List[Group]:
        """Получить все группы."""
        try:
            async for session in get_session():
                result = await session.execute(select(Group).order_by(Group.name))
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting all groups: {e}")
            return []

    async def get_group(self, group_id: int) -> Optional[Group]:
        """Получить группу по ID (для тестов)."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Group).where(Group.id == group_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}")
            return None

    async def search_groups(self, query: str) -> List[Group]:
        """Найти группы по номеру/названию."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Group).where(Group.name.like(f"%{query}%")).order_by(Group.name)
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching groups with query '{query}': {e}")
            return []

    async def get_available_faculties(self) -> list[str]:
        """Получить список доступных факультетов из базы данных."""
        try:
            # Сначала пытаемся получить из таблицы факультетов
            from app.services.faculty_service import FacultyService

            faculty_service = FacultyService()
            faculty_names = await faculty_service.get_faculty_names()

            if faculty_names:
                logger.info(f"Found {len(faculty_names)} faculties from faculty table")
                return faculty_names

            # Если нет, получаем из групп
            async for session in get_session():
                from sqlalchemy import select, distinct

                result = await session.execute(
                    select(distinct(Group.faculty)).filter(Group.faculty.isnot(None))
                )
                faculties = [row[0] for row in result.fetchall()]

                if not faculties:
                    logger.info("No faculties found in database")
                    return []

                logger.info(f"Found {len(faculties)} faculties from groups")
                return sorted(faculties)
        except Exception as e:
            logger.error(f"Error getting faculties from database: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    @async_error_handler(
        default_return=None, error_message="Failed to find or create group"
    )
    async def find_or_create_group(self, group_number: str) -> dict[str, str] | None:
        """Найти или создать группу по номеру."""
        # Валидируем входные данные
        if not group_number or not isinstance(group_number, str):
            logger.error(f"Invalid group number: {group_number}")
            return None

        group_number = group_number.strip()
        if not group_number:
            logger.error("Empty group number")
            return None

        try:
            async for session in get_session():
                # Ищем существующую группу
                result = await session.execute(
                    select(Group).filter(Group.name == group_number)
                )

                group = result.scalar_one_or_none()

                if group:
                    logger.info(f"Found existing group {group.name}")
                    group_data = {
                        "id": str(group.id),
                        "name": group.name,
                        "faculty": group.faculty or "Unknown",
                        "speciality": group.speciality or "Unknown",
                        "course": str(group.course or 1),
                    }

                    # Валидируем данные перед возвратом
                    validation_result = validate_group_data(group_data)
                    if not validation_result.is_valid:
                        logger.error(
                            f"Group data validation failed: {validation_result.errors}"
                        )
                        return None

                    return validation_result.data

                # Создаем новую группу с дефолтным факультетом
                # TODO: Определить факультет по названию группы или запросить у пользователя
                new_group = Group(
                    name=group_number,
                    faculty="Не определен",
                    speciality="Не определена",
                    course=1,
                    faculty_id=1,  # Дефолтный факультет (Педиатрический)
                    speciality_id=1,  # Дефолтная специальность
                )

                session.add(new_group)
                try:
                    await session.commit()
                except Exception as e:
                    logger.error(f"Failed to commit new group: {e}")
                    return None

                try:
                    await session.refresh(new_group)
                except Exception as e:
                    logger.error(f"Failed to refresh new group after creation: {e}")
                    return None

                logger.info(
                    f"Created new group {new_group.name} with ID {new_group.id}"
                )

                group_data = {
                    "id": str(new_group.id),
                    "name": new_group.name,
                    "faculty": new_group.faculty,
                    "speciality": new_group.speciality,
                    "course": str(new_group.course),
                }

                # Валидируем данные перед возвратом
                validation_result = validate_group_data(group_data)
                if not validation_result.is_valid:
                    logger.error(
                        f"New group data validation failed: {validation_result.errors}"
                    )
                    return None

                return validation_result.data

        except ValidationError as e:
            logger.error(f"Group data validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error finding or creating group: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return None

    async def find_or_create_group_with_faculty(
        self, group_name: str, course: int, faculty_id: int, speciality_id: int
    ) -> dict[str, object] | None:
        """Найти или создать группу с правильной привязкой к факультету и специальности."""
        try:
            async for session in get_session():
                # Ищем существующую группу
                result = await session.execute(
                    select(Group).where(Group.name == group_name)
                )
                existing_group = result.scalar_one_or_none()

                if existing_group:
                    # Обновляем привязки если они неправильные
                    if (
                        existing_group.faculty_id != faculty_id
                        or existing_group.speciality_id != speciality_id
                    ):
                        existing_group.faculty_id = faculty_id
                        existing_group.speciality_id = speciality_id
                        existing_group.course = course
                        await session.commit()
                        logger.info(
                            f"Updated group {group_name} with faculty {faculty_id}, speciality {speciality_id}"
                        )

                    return {
                        "id": existing_group.id,
                        "name": existing_group.name,
                        "course": existing_group.course,
                        "faculty_id": existing_group.faculty_id,
                        "speciality_id": existing_group.speciality_id,
                    }

                # Создаем новую группу
                new_group = Group(
                    name=group_name,
                    course=course,
                    faculty_id=faculty_id,
                    speciality_id=speciality_id,
                    faculty="",  # Legacy поле
                    speciality="",  # Legacy поле
                )

                session.add(new_group)
                await session.commit()
                await session.refresh(new_group)

                logger.info(
                    f"Created new group {group_name} with faculty {faculty_id}, speciality {speciality_id}"
                )

                return {
                    "id": new_group.id,
                    "name": new_group.name,
                    "course": new_group.course,
                    "faculty_id": new_group.faculty_id,
                    "speciality_id": new_group.speciality_id,
                }

        except Exception as e:
            logger.error(f"Error finding or creating group with faculty: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return None

    async def get_groups_count(self) -> int:
        """Получить количество групп в базе данных."""
        try:
            async for session in get_session():
                from sqlalchemy import select, func

                result = await session.execute(select(func.count(Group.id)))
                count = result.scalar()
                return count or 0
        except Exception as e:
            logger.error(f"Error getting groups count: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return 0

    async def get_groups_by_faculty(self, faculty_id: int) -> list[dict[str, object]]:
        """Получить группы по факультету."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Group).where(Group.faculty_id == faculty_id)
                )
                groups = result.scalars().all()

                return [
                    {
                        "id": group.id,
                        "name": group.name,
                        "course": group.course,
                        "faculty_id": group.faculty_id,
                        "speciality_id": group.speciality_id,
                    }
                    for group in groups
                ]

        except Exception as e:
            logger.error(f"Error getting groups by faculty {faculty_id}: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return []

    async def get_group_by_id(self, group_id: int) -> dict[str, object] | None:
        """Получить группу по ID."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Group).where(Group.id == group_id)
                )
                group = result.scalar_one_or_none()

                if group:
                    return {
                        "id": group.id,
                        "name": group.name,
                        "course": group.course,
                        "faculty_id": group.faculty_id,
                        "speciality_id": group.speciality_id,
                    }
                return None

        except Exception as e:
            logger.error(f"Error getting group by id {group_id}: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return None

    async def update_group_info(self, group_id: int, info: dict[str, str]) -> bool:
        """Обновить информацию о группе."""
        logger.info(f"Updating group {group_id} with info {info} (stub)")
        return True
