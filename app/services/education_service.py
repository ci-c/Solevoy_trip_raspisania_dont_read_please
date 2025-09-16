"""
Сервис для работы с образовательными данными.
"""

from typing import List, Dict, Any
from loguru import logger



class EducationService:
    """Сервис для управления образовательными данными."""

    def __init__(self):
        pass

    async def get_user_education_data(self, user_id: int) -> Dict[str, Any]:
        """Получить образовательные данные пользователя."""
        logger.info(f"Getting education data for user {user_id} (stub)")
        return {}

    async def update_user_education_data(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Обновить образовательные данные пользователя."""
        logger.info(f"Updating education data for user {user_id} (stub)")
        return True

    async def get_subjects(self, group_id: int) -> List[Dict[str, Any]]:
        """Получить предметы группы."""
        logger.info(f"Getting subjects for group {group_id} (stub)")
        return []

    async def get_teachers(self, subject_id: int) -> List[Dict[str, Any]]:
        """Получить преподавателей предмета."""
        logger.info(f"Getting teachers for subject {subject_id} (stub)")
        return []

    async def get_rooms(self) -> List[Dict[str, Any]]:
        """Получить все аудитории."""
        logger.info("Getting all rooms (stub)")
        return []