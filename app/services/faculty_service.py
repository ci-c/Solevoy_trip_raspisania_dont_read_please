"""
Сервис для работы с факультетами через реальный SZGMU API.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from app.database.session import get_session
from app.database.models import Faculty
from app.schedule.faculty_api_client import FacultyAPIClient


class FacultyService:
    """Сервис для работы с факультетами."""

    def __init__(self):
        self.api_client = FacultyAPIClient()

    async def load_faculties_from_api(self) -> List[Dict[str, Any]]:
        """Загрузить факультеты из реального SZGMU API."""
        try:
            import requests
            import json
            
            # Получаем все расписания для извлечения факультетов
            url = "https://frsview.szgmu.ru/api/xlsxSchedule/findAll/0"
            payload = {}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "content" not in data:
                logger.warning("API response missing 'content' key")
                return []
            
            # Извлекаем уникальные факультеты из специальностей
            faculties = set()
            for schedule in data["content"]:
                if "xlsxHeaderDto" in schedule:
                    for header in schedule["xlsxHeaderDto"]:
                        if "speciality" in header:
                            speciality = header["speciality"]
                            # Извлекаем факультет из специальности
                            faculty = self._extract_faculty_from_speciality(speciality)
                            if faculty:
                                faculties.add(faculty)
            
            # Преобразуем в список словарей
            faculties_data = []
            for i, faculty_name in enumerate(sorted(faculties), 1):
                faculties_data.append({
                    "id": i,
                    "name": faculty_name,
                    "short_name": self._generate_short_name(faculty_name),
                    "description": f"Факультет {faculty_name}"
                })
            
            if faculties_data:
                logger.info(f"Extracted {len(faculties_data)} faculties from SZGMU API")
                return faculties_data
            else:
                logger.warning("No faculties extracted from API")
                return []
                
        except Exception as e:
            logger.error(f"Error loading faculties from API: {e}")
            return []

    def _extract_faculty_from_speciality(self, speciality: str) -> str:
        """Извлечь название факультета из специальности."""
        # Маппинг специальностей на факультеты
        if "лечебное дело" in speciality.lower():
            return "Лечебный факультет"
        elif "педиатрия" in speciality.lower():
            return "Педиатрический факультет"
        elif "медико-профилактическое дело" in speciality.lower():
            return "Медико-профилактический факультет"
        elif "стоматология" in speciality.lower():
            return "Стоматологический факультет"
        elif "фармация" in speciality.lower():
            return "Фармацевтический факультет"
        elif "сестринское дело" in speciality.lower():
            return "Факультет сестринского дела"
        elif "медицинская кибернетика" in speciality.lower():
            return "Факультет медицинской кибернетики"
        elif "управление сестринской деятельностью" in speciality.lower():
            return "Факультет управления сестринской деятельностью"
        else:
            # Если не удалось определить, возвращаем общее название
            return "Неизвестный факультет"

    async def save_faculties_to_db(self, faculties_data: List[Dict[str, Any]]) -> bool:
        """Сохранить факультеты в базу данных."""
        try:
            async for session in get_session():
                for faculty_data in faculties_data:
                    # API возвращает данные в формате: {"id": 1, "name": "Лечебный факультет"}
                    faculty = Faculty(
                        name=faculty_data.get("name", ""),
                        short_name=self._generate_short_name(faculty_data.get("name", "")),
                        description=f"Факультет {faculty_data.get('name', '')}"
                    )
                    
                    # Используем merge для обновления существующих записей
                    await session.merge(faculty)
                
                await session.commit()
                logger.info(f"Saved {len(faculties_data)} faculties to database")
                return True
        except Exception as e:
            logger.error(f"Error saving faculties to database: {e}")
            return False

    def _generate_short_name(self, full_name: str) -> str:
        """Генерировать сокращенное название факультета."""
        # Простая логика для сокращения названий
        if "лечебный" in full_name.lower():
            return "ЛФ"
        elif "педиатрический" in full_name.lower():
            return "ПФ"
        elif "медико-профилактический" in full_name.lower():
            return "МПФ"
        elif "стоматологический" in full_name.lower():
            return "СФ"
        elif "фармацевтический" in full_name.lower():
            return "ФФ"
        else:
            # Берем первые буквы слов
            words = full_name.split()
            return "".join([word[0].upper() for word in words[:2]])

    async def get_faculties_from_db(self) -> List[Dict[str, Any]]:
        """Получить факультеты из базы данных."""
        try:
            from sqlalchemy import select
            
            async for session in get_session():
                result = await session.execute(
                    select(Faculty).order_by(Faculty.name)
                )
                faculties = []
                
                for faculty in result.scalars():
                    faculties.append({
                        "id": faculty.id,
                        "name": faculty.name,
                        "short_name": faculty.short_name,
                        "description": faculty.description
                    })
                
                return faculties
        except Exception as e:
            logger.error(f"Error getting faculties from database: {e}")
            return []

    async def sync_faculties(self) -> bool:
        """Синхронизировать факультеты с API."""
        try:
            # Загружаем с API
            api_faculties = await self.load_faculties_from_api()
            
            if api_faculties:
                # Сохраняем в БД
                success = await self.save_faculties_to_db(api_faculties)
                if success:
                    logger.info("Successfully synced faculties")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error syncing faculties: {e}")
            return False

    async def get_faculty_names(self) -> List[str]:
        """Получить только названия факультетов."""
        try:
            from sqlalchemy import select
            
            async for session in get_session():
                result = await session.execute(
                    select(Faculty.name).order_by(Faculty.name)
                )
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting faculty names: {e}")
            return []

    async def get_faculty_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Получить факультет по названию."""
        try:
            from sqlalchemy import select
            
            async for session in get_session():
                result = await session.execute(
                    select(Faculty).filter(Faculty.name == name)
                )
                faculty = result.scalar_one_or_none()
                
                if faculty:
                    return {
                        "id": faculty.id,
                        "name": faculty.name,
                        "short_name": faculty.short_name,
                        "description": faculty.description
                    }
                
                return None
        except Exception as e:
            logger.error(f"Error getting faculty by name: {e}")
            return None