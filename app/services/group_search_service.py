"""
Сервис поиска групп согласно UX дизайну.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from app.database.session import get_session
from app.database.models import (
    Schedule, Lesson, Faculty, Speciality
)
from sqlalchemy import select, and_, or_


@dataclass
class GroupInfo:
    """Информация о группе."""
    number: str  # "103а"
    speciality: str
    course: int
    stream: str  # "а", "б", "в"
    semester: str
    year: str
    faculty: str
    lecture_schedule_id: Optional[int] = None
    seminar_schedule_id: Optional[int] = None
    unified_schedule: Optional[Dict[str, Any]] = None




@dataclass
class UnifiedSchedule:
    """Объединенное расписание."""
    group: str
    week_schedule: Dict[str, List[Lesson]]  # день недели -> уроки
    metadata: Dict[str, Any]


class GroupSearchService:
    """Сервис поиска групп."""

    def __init__(self):
        self.current_semester = self.detect_current_semester()
        self.groups_cache = {}

    def detect_current_semester(self) -> Tuple[str, str]:
        """Определить текущий семестр и учебный год."""
        now = datetime.now()
        if 9 <= now.month <= 12:  # Осенний семестр
            return "осенний", f"{now.year}/{now.year + 1}"
        else:  # Весенний семестр
            return "весенний", f"{now.year - 1}/{now.year}"

    async def search_group_by_number(self, group_number: str) -> List[GroupInfo]:
        """Поиск группы по номеру (103а, 204б, etc)."""
        try:
            logger.info(f"Searching for group: {group_number}")
            
            async for session in get_session():
                # Ищем занятия с таким номером группы
                result = await session.execute(
                    select(Lesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(
                        and_(
                            or_(
                                Lesson.subgroup == group_number,
                                Lesson.study_group == group_number
                            ),
                            Lesson.schedule_id == Schedule.id
                        )
                    )
                    .order_by(Lesson.week_number, Lesson.day_name)
                )
                
                lessons = result.scalars().all()
                
                if not lessons:
                    logger.info(f"No lessons found for group {group_number}")
                    return []
                
                # Группируем по расписаниям
                schedules = {}
                for lesson in lessons:
                    schedule_id = lesson.schedule_id
                    if schedule_id not in schedules:
                        schedules[schedule_id] = {
                            'schedule': lesson.schedule,
                            'lessons': []
                        }
                    schedules[schedule_id]['lessons'].append(lesson)
                
                # Создаем GroupInfo для каждого расписания
                groups = []
                for schedule_id, data in schedules.items():
                    lesson = data['lessons'][0]  # Берем первый урок для метаданных
                    schedule = data['schedule']
                    
                    # Определяем тип расписания по названию файла
                    file_name = schedule.file_name.lower()
                    if 'лекц' in file_name or 'л' in file_name:
                        schedule_type = 'lecture'
                    elif 'сем' in file_name or 'с' in file_name:
                        schedule_type = 'seminar'
                    else:
                        schedule_type = 'mixed'
                    
                    group_info = GroupInfo(
                        number=group_number,
                        speciality=lesson.schedule.speciality.name,
                        course=self._extract_course_number(group_number),
                        stream=self._extract_stream(group_number),
                        semester=lesson.schedule.semester.name,
                        year=lesson.schedule.academic_year.name,
                        faculty=lesson.schedule.speciality.faculty.name,
                        lecture_schedule_id=schedule_id if schedule_type in ['lecture', 'mixed'] else None,
                        seminar_schedule_id=schedule_id if schedule_type in ['seminar', 'mixed'] else None
                    )
                    
                    groups.append(group_info)
                
                logger.info(f"Found {len(groups)} group variants for {group_number}")
                return groups
                
        except Exception as e:
            logger.error(f"Error searching group by number: {e}")
            return []

    async def search_groups_by_filters(
        self, 
        faculty: Optional[str] = None,
        speciality: Optional[str] = None,
        course: Optional[int] = None,
        stream: Optional[str] = None
    ) -> List[GroupInfo]:
        """Поиск групп по фильтрам."""
        try:
            logger.info(f"Searching groups with filters: faculty={faculty}, speciality={speciality}, course={course}, stream={stream}")
            
            async for session in get_session():
                query = (
                    select(Lesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(Lesson.schedule_id == Schedule.id)
                )
                
                if faculty:
                    query = query.where(Faculty.name == faculty)
                
                if speciality:
                    query = query.where(Speciality.name == speciality)
                
                if course:
                    # Фильтруем по номеру курса в названии группы
                    query = query.where(
                        or_(
                            Lesson.subgroup.like(f"{course}%"),
                            Lesson.study_group.like(f"{course}%")
                        )
                    )
                
                if stream:
                    query = query.where(
                        or_(
                            Lesson.subgroup.like(f"%{stream}"),
                            Lesson.study_group.like(f"%{stream}")
                        )
                    )
                
                result = await session.execute(
                    query.order_by(Faculty.name, Speciality.name, Lesson.subgroup)
                )
                
                lessons = result.scalars().all()
                
                # Группируем по группам
                groups = {}
                for lesson in lessons:
                    group_key = lesson.subgroup or lesson.study_group
                    if group_key and group_key not in groups:
                        groups[group_key] = GroupInfo(
                            number=group_key,
                            speciality=lesson.schedule.speciality.name,
                            course=self._extract_course_number(group_key),
                            stream=self._extract_stream(group_key),
                            semester=lesson.schedule.semester.name,
                            year=lesson.schedule.academic_year.name,
                            faculty=lesson.schedule.speciality.faculty.name
                        )
                
                logger.info(f"Found {len(groups)} groups with filters")
                return list(groups.values())
                
        except Exception as e:
            logger.error(f"Error searching groups by filters: {e}")
            return []

    def merge_lecture_seminar_schedules(self, group: GroupInfo) -> UnifiedSchedule:
        """Объединить лекции и семинары в единое расписание."""
        # TODO: Реализовать объединение расписаний
        # Пока возвращаем заглушку
        return UnifiedSchedule(
            group=group.number,
            week_schedule={},
            metadata={
                "faculty": group.faculty,
                "speciality": group.speciality,
                "course": group.course,
                "stream": group.stream,
                "semester": group.semester,
                "year": group.year
            }
        )

    def _extract_course_number(self, group_name: str) -> int:
        """Извлечь номер курса из названия группы."""
        try:
            import re
            match = re.match(r'^(\d+)', group_name)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 1  # По умолчанию

    def _extract_stream(self, group_name: str) -> str:
        """Извлечь поток из названия группы."""
        try:
            import re
            match = re.search(r'([абвгд])', group_name.lower())
            if match:
                return match.group(1)
        except Exception:
            pass
        return "а"  # По умолчанию

    async def get_available_faculties(self) -> List[Dict[str, Any]]:
        """Получить список доступных факультетов."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Faculty)
                    .distinct()
                    .order_by(Faculty.name)
                )
                
                faculties = result.scalars().all()
                
                return [
                    {
                        "id": faculty.id,
                        "name": faculty.name,
                        "short_name": faculty.short_name,
                        "description": faculty.description
                    }
                    for faculty in faculties
                ]
                
        except Exception as e:
            logger.error(f"Error getting faculties: {e}")
            return []

    async def get_available_specialities(self, faculty_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получить список доступных специальностей."""
        try:
            async for session in get_session():
                query = select(Speciality).distinct().order_by(Speciality.name)
                
                if faculty_id:
                    query = query.where(Speciality.faculty_id == faculty_id)
                
                result = await session.execute(query)
                specialities = result.scalars().all()
                
                return [
                    {
                        "id": spec.id,
                        "name": spec.name,
                        "code": spec.code,
                        "faculty_id": spec.faculty_id,
                        "faculty_name": spec.faculty.name
                    }
                    for spec in specialities
                ]
                
        except Exception as e:
            logger.error(f"Error getting specialities: {e}")
            return []

    async def get_available_courses(self) -> List[int]:
        """Получить список доступных курсов."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Lesson.subgroup, Lesson.study_group)
                    .distinct()
                )
                
                courses = set()
                for row in result.fetchall():
                    subgroup, study_group = row
                    group_name = subgroup or study_group
                    if group_name:
                        course = self._extract_course_number(group_name)
                        if 1 <= course <= 6:  # Валидные курсы
                            courses.add(course)
                
                return sorted(list(courses))
                
        except Exception as e:
            logger.error(f"Error getting courses: {e}")
            return [1, 2, 3, 4, 5, 6]  # По умолчанию

    async def get_available_streams(self) -> List[str]:
        """Получить список доступных потоков."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Lesson.subgroup, Lesson.study_group)
                    .distinct()
                )
                
                streams = set()
                for row in result.fetchall():
                    subgroup, study_group = row
                    group_name = subgroup or study_group
                    if group_name:
                        stream = self._extract_stream(group_name)
                        streams.add(stream)
                
                return sorted(list(streams))
                
        except Exception as e:
            logger.error(f"Error getting streams: {e}")
            return ["а", "б", "в", "г"]  # По умолчанию

    def get_current_semester_info(self) -> Dict[str, Any]:
        """Получить информацию о текущем семестре."""
        semester, year = self.current_semester
        return {
            "name": semester,
            "year": year,
            "is_current": True
        }
