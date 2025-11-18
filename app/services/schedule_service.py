"""
Сервис для работы с расписаниями из базы данных.
"""

from datetime import date, datetime
from typing import List, Dict
from loguru import logger

from app.database.session import get_session
from app.database.models import (
    Schedule,
    ScheduleLesson,
    Faculty,
    Speciality,
    AcademicYear,
    Semester,
    Group,
)
from sqlalchemy import select, and_, or_, func


class ScheduleService:
    """Сервис для работы с расписаниями."""

    async def get_user_schedule(
        self, user_id: int, start_date: date | None = None, end_date: date | None = None
    ) -> List[Dict[str, str]] | None:
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
            # Получаем пользователя и его группу из профиля
            async for session in get_session():
                from app.database.models import User as UserModel

                result = await session.execute(
                    select(UserModel).filter(UserModel.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User {user_id} not found")
                    return None

                group_id = None
                if getattr(user, "profile", None) and user.profile.group_id:
                    group_id = user.profile.group_id
                elif user.group_id:
                    group_id = user.group_id

                if not group_id:
                    logger.warning(f"User {user_id} has no group assigned")
                    return None

            # Получаем занятия группы из нормализованной таблицы
            async for session in get_session():
                query = select(ScheduleLesson).where(
                    ScheduleLesson.group_id == group_id
                )

                if start_date:
                    query = query.where(
                        ScheduleLesson.date.isnot(None),
                        ScheduleLesson.date >= start_date,
                    )
                if end_date:
                    query = query.where(
                        ScheduleLesson.date.isnot(None),
                        ScheduleLesson.date <= end_date,
                    )

                result = await session.execute(
                    query.order_by(
                        func.coalesce(ScheduleLesson.date, datetime.utcnow().date()),
                        ScheduleLesson.week_number,
                        ScheduleLesson.day_name,
                        ScheduleLesson.start_time,
                    )
                )

                lessons = result.scalars().all()

                formatted_lessons = []
                for lesson in lessons:
                    formatted_lessons.append(
                        {
                            "id": lesson.id,
                            "subject": lesson.subject.name,
                            "type": lesson.lesson_type.name,
                            "lecturer": lesson.lecturer.full_name
                            if lesson.lecturer
                            else None,
                            "classroom": lesson.classroom.number
                            if lesson.classroom
                            else None,
                            "building": lesson.classroom.building
                            if lesson.classroom
                            else None,
                            "campus": lesson.classroom.campus
                            if lesson.classroom
                            else None,
                            "day_name": lesson.day_name,
                            "week_number": lesson.week_number,
                            "pair_time": lesson.pair_time,
                            "start_time": lesson.start_time,
                            "end_time": lesson.end_time,
                            "date": lesson.date,
                            "subgroup": lesson.subgroup,
                            "study_group": lesson.study_group,
                            "department": lesson.department.name
                            if lesson.department
                            else None,
                        }
                    )

                return formatted_lessons

        except Exception as e:
            logger.error(f"Error getting user schedule: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    async def get_group_schedule(
        self, group_name: str, week_number: int | None = None
    ) -> List[Dict[str, str]] | None:
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
                group_result = await session.execute(
                    select(Group).where(Group.name == group_name)
                )
                group = group_result.scalar_one_or_none()
                if not group:
                    logger.warning(f"Group {group_name} not found")
                    return None

                query = select(ScheduleLesson).where(
                    ScheduleLesson.group_id == group.id
                )

                if week_number:
                    query = query.where(ScheduleLesson.week_number == week_number)

                result = await session.execute(
                    query.order_by(
                        ScheduleLesson.week_number,
                        ScheduleLesson.day_name,
                        ScheduleLesson.start_time,
                    )
                )

                lessons = result.scalars().all()

                formatted_lessons = []
                for lesson in lessons:
                    formatted_lessons.append(
                        {
                            "id": lesson.id,
                            "subject": lesson.subject.name,
                            "type": lesson.lesson_type.name,
                            "lecturer": lesson.lecturer.full_name
                            if lesson.lecturer
                            else None,
                            "classroom": lesson.classroom.number
                            if lesson.classroom
                            else None,
                            "building": lesson.classroom.building
                            if lesson.classroom
                            else None,
                            "campus": lesson.classroom.campus
                            if lesson.classroom
                            else None,
                            "day_name": lesson.day_name,
                            "week_number": lesson.week_number,
                            "pair_time": lesson.pair_time,
                            "start_time": lesson.start_time,
                            "end_time": lesson.end_time,
                            "date": lesson.date,
                            "subgroup": lesson.subgroup,
                            "study_group": lesson.study_group,
                            "department": lesson.department.name
                            if lesson.department
                            else None,
                            "faculty": group.faculty_obj.name
                            if group.faculty_obj
                            else None,
                            "speciality": group.speciality_obj.name
                            if group.speciality_obj
                            else None,
                        }
                    )

                return formatted_lessons

        except Exception as e:
            logger.error(f"Error getting group schedule: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    async def search_groups(
        self,
        faculty_name: str | None = None,
        speciality_name: str | None = None,
        course_number: int | None = None,
    ) -> List[Dict[str, str]]:
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
                    select(Group)
                    .join(Speciality, Group.speciality_id == Speciality.id, isouter=True)
                    .join(Faculty, Speciality.faculty_id == Faculty.id, isouter=True)
                )

                if faculty_name:
                    query = query.where(Faculty.name == faculty_name)

                if speciality_name:
                    query = query.where(Speciality.name == speciality_name)

                if course_number:
                    query = query.where(Group.course == course_number)

                result = await session.execute(query.order_by(Group.name))
                groups = result.scalars().all()

                semester, year = self.current_semester

                return [
                    {
                        "group_name": group.name,
                        "faculty": group.faculty_obj.name
                        if group.faculty_obj
                        else None,
                        "speciality": group.speciality_obj.name
                        if group.speciality_obj
                        else None,
                        "course": group.course,
                        "semester": semester,
                        "year": year,
                    }
                    for group in groups
                ]

        except Exception as e:
            logger.error(f"Error searching groups: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    async def get_available_faculties(self) -> List[Dict[str, str]]:
        """Получить список доступных факультетов."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Faculty).distinct().order_by(Faculty.name)
                )

                faculties = result.scalars().all()

                if not faculties:
                    logger.warning("No faculties found in database")
                    return []

                faculty_list = []
                for faculty in faculties:
                    faculty_data = {
                        "id": str(faculty.id),
                        "name": faculty.name or "Unknown",
                        "short_name": faculty.short_name or "",
                        "description": faculty.description or "",
                    }
                    faculty_list.append(faculty_data)

                logger.info(f"Found {len(faculty_list)} faculties")
                return faculty_list

        except Exception as e:
            logger.error(f"Error getting faculties: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None  # Пробрасываем ошибку дальше!

    async def get_available_specialities(
        self, faculty_id: int | None = None
    ) -> List[Dict[str, str]]:
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
                        "faculty_name": spec.faculty.name,
                    }
                    for spec in specialities
                ]

        except Exception as e:
            logger.error(f"Error getting specialities: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    async def get_current_academic_year(self) -> Dict[str, str] | None:
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
                        "is_current": year.is_current,
                    }

                return None

        except Exception as e:
            logger.error(f"Error getting current academic year: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    async def get_current_semester(self) -> Dict[str, str] | None:
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
                        "is_current": semester.is_current,
                    }

                return None

        except Exception as e:
            logger.error(f"Error getting current semester: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    async def get_lessons_by_week(
        self, group_name: str, week_number: int
    ) -> List[Dict[str, str]]:
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
                group_result = await session.execute(
                    select(Group).where(Group.name == group_name)
                )
                group = group_result.scalar_one_or_none()
                if not group:
                    logger.warning(f"Group {group_name} not found")
                    return None

                result = await session.execute(
                    select(ScheduleLesson)
                    .where(
                        and_(
                            ScheduleLesson.group_id == group.id,
                            ScheduleLesson.week_number == week_number,
                        )
                    )
                    .order_by(
                        ScheduleLesson.day_name,
                        ScheduleLesson.start_time,
                    )
                )

                lessons = result.scalars().all()

                # Группируем по дням
                days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
                grouped_lessons = {day: [] for day in days}

                for lesson in lessons:
                    day_lessons = grouped_lessons.get(lesson.day_name, [])
                    day_lessons.append(
                        {
                            "id": lesson.id,
                            "subject": lesson.subject.name,
                            "type": lesson.lesson_type.name,
                            "lecturer": lesson.lecturer.full_name
                            if lesson.lecturer
                            else None,
                            "classroom": lesson.classroom.number
                            if lesson.classroom
                            else None,
                            "building": lesson.classroom.building
                            if lesson.classroom
                            else None,
                            "campus": lesson.classroom.campus
                            if lesson.classroom
                            else None,
                            "pair_time": lesson.pair_time,
                            "start_time": lesson.start_time,
                            "end_time": lesson.end_time,
                            "department": lesson.department.name
                            if lesson.department
                            else None,
                        }
                    )
                    grouped_lessons[lesson.day_name] = day_lessons

                return grouped_lessons

        except Exception as e:
            logger.error(f"Error getting lessons by week: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None

    def _extract_course_number(self, group_name: str) -> int | None:
        """Извлечь номер курса из названия группы."""
        try:
            # Ищем цифру в начале строки
            import re

            match = re.match(r"^(\d+)", group_name)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.error(f"Error extracting course number from '{group_name}': {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return None

    async def get_schedule_statistics(self) -> Dict[str, str] | None:
        """Получить статистику по расписаниям."""
        try:
            async for session in get_session():
                # Подсчитываем общее количество занятий
                lessons_count = await session.execute(select(ScheduleLesson.id))
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
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting schedule statistics: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None
