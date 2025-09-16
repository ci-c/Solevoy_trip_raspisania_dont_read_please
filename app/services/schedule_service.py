"""
Сервис для работы с расписаниями из базы данных.
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from app.database.session import get_session
from app.database.models import (
    Schedule, Lesson, Faculty, Speciality, AcademicYear, Semester
)
from sqlalchemy import select, and_, or_


class ScheduleService:
    """Сервис для работы с расписаниями."""

    async def get_user_schedule(
        self, 
        user_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить расписание пользователя.
        
        Args:
            user_id: ID пользователя
            start_date: Начальная дата (по умолчанию - текущая неделя)
            end_date: Конечная дата (по умолчанию - текущая неделя)
            
        Returns:
            Список занятий пользователя
        """
        try:
            # Получаем группу пользователя
            from app.services.user_service import UserService
            user_service = UserService()
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or not user.group_id:
                logger.warning(f"User {user_id} has no group assigned")
                return []
            
            # Получаем занятия группы
            async for session in get_session():
                result = await session.execute(
                    select(Lesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(
                        and_(
                            Schedule.speciality_id == user.group.speciality_id,
                            Lesson.schedule_id == Schedule.id
                        )
                    )
                    .order_by(Lesson.week_number, Lesson.day_name, Lesson.start_time)
                )
                
                lessons = result.scalars().all()
                
                # Форматируем результат
                formatted_lessons = []
                for lesson in lessons:
                    formatted_lessons.append({
                        "id": lesson.id,
                        "subject": lesson.subject.name,
                        "type": lesson.lesson_type.name,
                        "lecturer": lesson.lecturer.name if lesson.lecturer else None,
                        "classroom": lesson.classroom.number if lesson.classroom else None,
                        "building": lesson.classroom.building if lesson.classroom else None,
                        "day_name": lesson.day_name,
                        "week_number": lesson.week_number,
                        "pair_time": lesson.pair_time,
                        "start_time": lesson.start_time,
                        "end_time": lesson.end_time,
                        "subgroup": lesson.subgroup,
                        "study_group": lesson.study_group,
                        "department": lesson.department.name if lesson.department else None
                    })
                
                return formatted_lessons
                
        except Exception as e:
            logger.error(f"Error getting user schedule: {e}")
            return []

    async def get_group_schedule(
        self, 
        group_name: str,
        week_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить расписание группы.
        
        Args:
            group_name: Название группы (например, "105а")
            week_number: Номер недели (по умолчанию - текущая)
            
        Returns:
            Список занятий группы
        """
        try:
            async for session in get_session():
                query = (
                    select(Lesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(
                        and_(
                            or_(
                                Lesson.subgroup == group_name,
                                Lesson.study_group == group_name
                            ),
                            Lesson.schedule_id == Schedule.id
                        )
                    )
                )
                
                if week_number:
                    query = query.where(Lesson.week_number == week_number)
                
                result = await session.execute(
                    query.order_by(Lesson.week_number, Lesson.day_name, Lesson.start_time)
                )
                
                lessons = result.scalars().all()
                
                # Форматируем результат
                formatted_lessons = []
                for lesson in lessons:
                    formatted_lessons.append({
                        "id": lesson.id,
                        "subject": lesson.subject.name,
                        "type": lesson.lesson_type.name,
                        "lecturer": lesson.lecturer.name if lesson.lecturer else None,
                        "classroom": lesson.classroom.number if lesson.classroom else None,
                        "building": lesson.classroom.building if lesson.classroom else None,
                        "day_name": lesson.day_name,
                        "week_number": lesson.week_number,
                        "pair_time": lesson.pair_time,
                        "start_time": lesson.start_time,
                        "end_time": lesson.end_time,
                        "subgroup": lesson.subgroup,
                        "study_group": lesson.study_group,
                        "department": lesson.department.name if lesson.department else None,
                        "faculty": lesson.schedule.speciality.faculty.name,
                        "speciality": lesson.schedule.speciality.name
                    })
                
                return formatted_lessons
                
        except Exception as e:
            logger.error(f"Error getting group schedule: {e}")
            return []

    async def search_groups(
        self, 
        faculty_name: Optional[str] = None,
        speciality_name: Optional[str] = None,
        course_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск групп по критериям.
        
        Args:
            faculty_name: Название факультета
            speciality_name: Название специальности
            course_number: Номер курса
            
        Returns:
            Список найденных групп
        """
        try:
            async for session in get_session():
                query = (
                    select(Lesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(Lesson.schedule_id == Schedule.id)
                )
                
                if faculty_name:
                    query = query.where(Faculty.name == faculty_name)
                
                if speciality_name:
                    query = query.where(Speciality.name == speciality_name)
                
                if course_number:
                    # Извлекаем номер курса из названия группы
                    query = query.where(
                        or_(
                            Lesson.subgroup.like(f"{course_number}%"),
                            Lesson.study_group.like(f"{course_number}%")
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
                        groups[group_key] = {
                            "group_name": group_key,
                            "faculty": lesson.schedule.speciality.faculty.name,
                            "speciality": lesson.schedule.speciality.name,
                            "course": self._extract_course_number(group_key),
                            "lessons_count": 0
                        }
                    
                    if group_key:
                        groups[group_key]["lessons_count"] += 1
                
                return list(groups.values())
                
        except Exception as e:
            logger.error(f"Error searching groups: {e}")
            return []

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

    async def get_current_academic_year(self) -> Optional[Dict[str, Any]]:
        """Получить текущий учебный год."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(AcademicYear)
                    .where(AcademicYear.is_current)
                    .order_by(AcademicYear.created_at.desc())
                )
                
                year = result.scalar_one_or_none()
                
                if year:
                    return {
                        "id": year.id,
                        "name": year.name,
                        "is_current": year.is_current
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting current academic year: {e}")
            return None

    async def get_current_semester(self) -> Optional[Dict[str, Any]]:
        """Получить текущий семестр."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Semester)
                    .where(Semester.is_current)
                    .order_by(Semester.created_at.desc())
                )
                
                semester = result.scalar_one_or_none()
                
                if semester:
                    return {
                        "id": semester.id,
                        "name": semester.name,
                        "academic_year_id": semester.academic_year_id,
                        "is_current": semester.is_current
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting current semester: {e}")
            return None

    async def get_lessons_by_week(
        self, 
        group_name: str, 
        week_number: int
    ) -> List[Dict[str, Any]]:
        """
        Получить занятия группы за определенную неделю.
        
        Args:
            group_name: Название группы
            week_number: Номер недели
            
        Returns:
            Список занятий, отсортированный по дням и времени
        """
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Lesson)
                    .join(Schedule)
                    .where(
                        and_(
                            or_(
                                Lesson.subgroup == group_name,
                                Lesson.study_group == group_name
                            ),
                            Lesson.week_number == week_number,
                            Lesson.schedule_id == Schedule.id
                        )
                    )
                    .order_by(
                        Lesson.day_name,
                        Lesson.start_time
                    )
                )
                
                lessons = result.scalars().all()
                
                # Группируем по дням
                days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
                grouped_lessons = {day: [] for day in days}
                
                for lesson in lessons:
                    day_lessons = grouped_lessons.get(lesson.day_name, [])
                    day_lessons.append({
                        "id": lesson.id,
                        "subject": lesson.subject.name,
                        "type": lesson.lesson_type.name,
                        "lecturer": lesson.lecturer.name if lesson.lecturer else None,
                        "classroom": lesson.classroom.number if lesson.classroom else None,
                        "building": lesson.classroom.building if lesson.classroom else None,
                        "pair_time": lesson.pair_time,
                        "start_time": lesson.start_time,
                        "end_time": lesson.end_time,
                        "department": lesson.department.name if lesson.department else None
                    })
                    grouped_lessons[lesson.day_name] = day_lessons
                
                return grouped_lessons
                
        except Exception as e:
            logger.error(f"Error getting lessons by week: {e}")
            return {}

    def _extract_course_number(self, group_name: str) -> Optional[int]:
        """Извлечь номер курса из названия группы."""
        try:
            # Ищем цифру в начале строки
            import re
            match = re.match(r'^(\d+)', group_name)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None

    async def get_schedule_statistics(self) -> Dict[str, Any]:
        """Получить статистику по расписаниям."""
        try:
            async for session in get_session():
                # Подсчитываем общее количество занятий
                lessons_count = await session.execute(select(Lesson.id))
                total_lessons = len(lessons_count.scalars().all())
                
                # Подсчитываем количество расписаний
                schedules_count = await session.execute(select(Schedule.id))
                total_schedules = len(schedules_count.scalars().all())
                
                # Подсчитываем количество факультетов
                faculties_count = await session.execute(select(Faculty.id))
                total_faculties = len(faculties_count.scalars().all())
                
                # Подсчитываем количество специальностей
                specialities_count = await session.execute(select(Speciality.id))
                total_specialities = len(specialities_count.scalars().all())
                
                return {
                    "total_lessons": total_lessons,
                    "total_schedules": total_schedules,
                    "total_faculties": total_faculties,
                    "total_specialities": total_specialities,
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting schedule statistics: {e}")
            return {}