"""
Сервис для инициализации базовых данных в системе.
"""

from typing import List, Dict, Any
from loguru import logger

from app.services.faculty_service import FacultyService
from app.services.group_service import GroupService


class DataInitializationService:
    """Сервис для инициализации данных."""

    def __init__(self):
        self.faculty_service = FacultyService()
        self.group_service = GroupService()

    async def initialize_faculties(self) -> bool:
        """Инициализировать факультеты в системе."""
        try:
            # Сначала пытаемся синхронизировать с API
            api_success = await self.faculty_service.sync_faculties()
            
            if api_success:
                logger.info("Faculties initialized from API")
                return True
            
            # Если API недоступен, создаем базовые факультеты
            logger.info("API unavailable, creating default faculties")
            return await self._create_default_faculties()
            
        except Exception as e:
            logger.error(f"Error initializing faculties: {e}")
            return False

    async def _create_default_faculties(self) -> bool:
        """Создать базовые факультеты по умолчанию (только если API недоступен)."""
        try:
            logger.warning("API unavailable, cannot create default faculties")
            logger.warning("Please check API connection or configure fallback data")
            return False
            
        except Exception as e:
            logger.error(f"Error creating default faculties: {e}")
            return False

    async def initialize_sample_groups(self) -> bool:
        """Инициализировать примеры групп для демонстрации."""
        try:
            # Получаем факультеты
            faculties = await self.faculty_service.get_faculty_names()
            
            if not faculties:
                logger.warning("No faculties found, skipping group initialization")
                return False
            
            # Создаем примеры групп
            sample_groups = []
            for faculty in faculties[:3]:  # Берем первые 3 факультета
                for course in range(1, 4):  # Курсы 1-3
                    for stream in ['а', 'б']:  # Потоки а, б
                        group_number = f"{course}0{stream}"
                        sample_groups.append({
                            "name": group_number,
                            "faculty": faculty,
                            "speciality": f"Специальность {faculty}",
                            "course": course
                        })
            
            # Сохраняем группы
            success = await self._save_groups(sample_groups)
            if success:
                logger.info(f"Created {len(sample_groups)} sample groups")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing sample groups: {e}")
            return False

    async def _save_groups(self, groups_data: List[Dict[str, Any]]) -> bool:
        """Сохранить группы в базу данных."""
        try:
            from app.database.session import get_session
            from app.database.models import Group
            
            async for session in get_session():
                for group_data in groups_data:
                    group = Group(
                        name=group_data["name"],
                        faculty=group_data["faculty"],
                        speciality=group_data["speciality"],
                        course=group_data["course"]
                    )
                    session.add(group)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving groups: {e}")
            return False

    async def initialize_all_data(self) -> bool:
        """Инициализировать все данные системы."""
        try:
            logger.info("Starting data initialization...")
            
            # Инициализируем факультеты
            faculties_success = await self.initialize_faculties()
            if not faculties_success:
                logger.error("Failed to initialize faculties")
                return False
            
            # Инициализируем примеры групп
            groups_success = await self.initialize_sample_groups()
            if not groups_success:
                logger.warning("Failed to initialize sample groups")
            
            logger.info("Data initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during data initialization: {e}")
            return False

    async def check_data_availability(self) -> Dict[str, bool]:
        """Проверить доступность данных в системе."""
        try:
            faculties = await self.faculty_service.get_faculty_names()
            groups = await self.group_service.get_all_groups()
            
            return {
                "faculties_available": len(faculties) > 0,
                "groups_available": len(groups) > 0,
                "faculties_count": len(faculties),
                "groups_count": len(groups)
            }
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return {
                "faculties_available": False,
                "groups_available": False,
                "faculties_count": 0,
                "groups_count": 0
            }
