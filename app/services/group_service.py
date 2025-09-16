"""
Сервис для работы с группами студентов.
"""

from typing import List, Dict
from loguru import logger

from app.database.session import get_session
from app.database.models import Group
from sqlalchemy import select


class GroupService:
    """Сервис для управления группами студентов."""

    def __init__(self):
        pass

    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """Получить все группы."""
        logger.info("Getting all groups (stub)")
        return []

    async def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Получить группу по ID."""
        logger.info(f"Getting group {group_id} (stub)")
        return None

    async def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новую группу."""
        logger.info("Creating group (stub)")
        return group_data

    async def update_group(self, group_id: int, group_data: Dict[str, Any]) -> bool:
        """Обновить группу."""
        logger.info(f"Updating group {group_id} (stub)")
        return True

    async def delete_group(self, group_id: int) -> bool:
        """Удалить группу."""
        logger.info(f"Deleting group {group_id} (stub)")
        return True

    async def find_groups_by_number(self, group_number: str) -> List[Dict[str, Any]]:
        """Найти группы по номеру."""
        logger.info(f"Finding groups by number {group_number} (stub)")
        return []

    async def get_groups_by_faculty(self, faculty: str) -> List[Dict[str, Any]]:
        """Получить группы по факультету."""
        logger.info(f"Getting groups by faculty {faculty} (stub)")
        return []

    async def get_available_faculties(self) -> List[str]:
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
            return []

    async def find_or_create_group(self, group_number: str) -> Dict[str, str] | None:
        """Найти или создать группу по номеру."""
        try:
            async for session in get_session():
                # Ищем существующую группу
                result = await session.execute(
                    select(Group).filter(Group.name == group_number)
                )
                group = result.scalar_one_or_none()
                
                if group:
                    logger.info(f"Found existing group {group.name}")
                    return {
                        "id": group.id,
                        "name": group.name,
                        "faculty": group.faculty,
                        "speciality": group.speciality,
                        "course": group.course
                    }
                
                # Создаем новую группу
                new_group = Group(
                    name=group_number,
                    faculty="Unknown",
                    speciality="Unknown",
                    course=1
                )
                session.add(new_group)
                await session.commit()
                
                logger.info(f"Created new group {new_group.name} with ID {new_group.id}")
                return {
                    "id": new_group.id,
                    "name": new_group.name,
                    "faculty": new_group.faculty,
                    "speciality": new_group.speciality,
                    "course": new_group.course
                }
        except Exception as e:
            logger.error(f"Error finding or creating group: {e}")
            return None

    async def update_group_info(self, group_id: int, info: Dict[str, str]) -> bool:
        """Обновить информацию о группе."""
        logger.info(f"Updating group {group_id} with info {info} (stub)")
        return True