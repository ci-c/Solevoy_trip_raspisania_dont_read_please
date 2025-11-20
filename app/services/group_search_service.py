"""Сервис поиска групп согласно UX дизайну."""

from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import and_, or_, select

from app.database.models import Faculty, Schedule, ScheduleLesson, Speciality
from app.database.session import get_session


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
    lecture_schedule_id: int | None = None
    seminar_schedule_id: int | None = None
    unified_schedule: dict[str, str] | None = None


@dataclass
class UnifiedSchedule:
    """Объединенное расписание."""

    group: str
    week_schedule: dict[str, list[ScheduleLesson]]  # день недели -> уроки
    metadata: dict[str, object]


class GroupSearchService:
    """Сервис поиска групп."""

    def __init__(self) -> None:
        self.current_semester = self.detect_current_semester()
        self.groups_cache = {}

    def detect_current_semester(self) -> tuple[str, str]:
        """Определить текущий семестр и учебный год."""
        now = datetime.now(tz=timezone.utc)
        if 9 <= now.month <= 12:  # Осенний семестр
            return "осенний", f"{now.year}/{now.year + 1}"
        # Весенний семестр
        return "весенний", f"{now.year - 1}/{now.year}"

    async def search_group_by_number(self, group_number: str) -> list[GroupInfo] | None:
        """Поиск группы по номеру (103а, 204б, etc)."""
        try:
            logger.info(f"Searching for group: {group_number}")

            async for session in get_session():
                # Ищем занятия с таким номером группы
                result = await session.execute(
                    select(ScheduleLesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(
                        and_(
                            or_(
                                ScheduleLesson.subgroup == group_number,
                                ScheduleLesson.study_group == group_number,
                            ),
                            ScheduleLesson.schedule_id == Schedule.id,
                        ),
                    )
                    .order_by(
                        ScheduleLesson.week_number,
                        ScheduleLesson.day_name,
                        ScheduleLesson.start_time,
                    ),
                )

                lessons = result.scalars().all()

                if not lessons:
                    logger.info(f"No lessons found for group {group_number}")
                    return []

                # Группируем по расписаниям
                schedules: dict[int, dict[str, object]] = {}
                for lesson in lessons:
                    schedule_id = lesson.schedule_id
                    if schedule_id not in schedules:
                        schedules[schedule_id] = {
                            "schedule": lesson.schedule,
                            "lessons": [],
                        }
                    # Type assertion для mypy
                    lessons_list = schedules[schedule_id]["lessons"]
                    if isinstance(lessons_list, list):
                        lessons_list.append(lesson)

                # Создаем GroupInfo для каждого расписания
                groups = []
                for schedule_id, data in schedules.items():
                    lessons_list = data["lessons"]
                    if not isinstance(lessons_list, list) or not lessons_list:
                        continue
                    lesson = lessons_list[0]  # Берем первый урок для метаданных
                    schedule = data["schedule"]

                    # Определяем тип расписания по названию файла
                    if hasattr(schedule, "file_name"):
                        file_name = schedule.file_name.lower()
                    else:
                        file_name = ""
                    if "лекц" in file_name or "л" in file_name:
                        schedule_type = "lecture"
                    elif "сем" in file_name or "с" in file_name:
                        schedule_type = "seminar"
                    else:
                        schedule_type = "mixed"

                    group_info = GroupInfo(
                        number=group_number,
                        speciality=lesson.schedule.speciality.name,
                        course=self._extract_course_number(group_number),
                        stream=self._extract_stream(group_number),
                        semester=lesson.schedule.semester.name,
                        year=lesson.schedule.academic_year.name,
                        faculty=lesson.schedule.speciality.faculty.name,
                        lecture_schedule_id=schedule_id
                        if schedule_type in ["lecture", "mixed"]
                        else None,
                        seminar_schedule_id=schedule_id
                        if schedule_type in ["seminar", "mixed"]
                        else None,
                    )

                    groups.append(group_info)

                logger.info(f"Found {len(groups)} group variants for {group_number}")
                return groups

        except Exception as e:
            logger.error(f"Error searching group by number: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return None

    async def search_groups_by_filters(
        self,
        faculty: str | None = None,
        speciality: str | None = None,
        course: int | None = None,
        stream: str | None = None,
    ) -> list[GroupInfo]:
        """Поиск групп по фильтрам."""
        try:
            logger.info(
                f"Searching groups with filters: faculty={faculty}, speciality={speciality}, course={course}, stream={stream}",
            )

            async for session in get_session():
                query = (
                    select(ScheduleLesson)
                    .join(Schedule)
                    .join(Speciality)
                    .join(Faculty)
                    .where(ScheduleLesson.schedule_id == Schedule.id)
                )

                if faculty:
                    query = query.where(Faculty.name == faculty)

                if speciality:
                    query = query.where(Speciality.name == speciality)

                if course:
                    # Фильтруем по номеру курса в названии группы
                    query = query.where(
                        or_(
                            ScheduleLesson.subgroup.like(f"{course}%"),
                            ScheduleLesson.study_group.like(f"{course}%"),
                        ),
                    )

                if stream:
                    query = query.where(
                        or_(
                            ScheduleLesson.subgroup.like(f"%{stream}"),
                            ScheduleLesson.study_group.like(f"%{stream}"),
                        ),
                    )

                result = await session.execute(
                    query.order_by(
                        Faculty.name,
                        Speciality.name,
                        ScheduleLesson.subgroup,
                        ScheduleLesson.start_time,
                    ),
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
                            faculty=lesson.schedule.speciality.faculty.name,
                        )

                logger.info(f"Found {len(groups)} groups with filters")
                return list(groups.values())

        except Exception as e:
            logger.error(f"Error searching groups by filters: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
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
                "year": group.year,
            },
        )

    def _extract_course_number(self, group_name: str) -> int:
        """Извлечь номер курса из названия группы."""
        try:
            import re

            match = re.match(r"^(\d+)", group_name)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return 1  # По умолчанию

    def _extract_stream(self, group_name: str) -> str:
        """Извлечь поток из названия группы."""
        try:
            import re

            match = re.search(r"([абвгд])", group_name.lower())
            if match:
                return match.group(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return "а"  # По умолчанию

    async def get_available_faculties(self) -> list[dict[str, object]]:
        """Получить список доступных факультетов."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Faculty).distinct().order_by(Faculty.name),
                )

                faculties = result.scalars().all()

                return [
                    {
                        "id": faculty.id,
                        "name": faculty.name,
                        "short_name": faculty.short_name,
                        "description": faculty.description,
                    }
                    for faculty in faculties
                ]

        except Exception as e:
            logger.error(f"Error getting faculties: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return []

    async def get_available_specialities(
        self, faculty_id: int | None = None,
    ) -> list[dict[str, object]]:
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
        return []

    async def get_available_courses(self) -> list[int]:
        """Получить список доступных курсов."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(
                        ScheduleLesson.subgroup, ScheduleLesson.study_group,
                    ).distinct(),
                )

                courses = set()
                for row in result.fetchall():
                    subgroup, study_group = row
                    group_name = subgroup or study_group
                    if group_name:
                        course = self._extract_course_number(group_name)
                        if 1 <= course <= 6:  # Валидные курсы
                            courses.add(course)

                return sorted(courses)

        except Exception as e:
            logger.error(f"Error getting courses: {e}")
            return [1, 2, 3, 4, 5, 6]  # По умолчанию
        return [1, 2, 3, 4, 5, 6]  # Fallback

    async def get_available_streams(self) -> list[str]:
        """Получить список доступных потоков."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(
                        ScheduleLesson.subgroup, ScheduleLesson.study_group,
                    ).distinct(),
                )

                streams = set()
                for row in result.fetchall():
                    subgroup, study_group = row
                    group_name = subgroup or study_group
                    if group_name:
                        stream = self._extract_stream(group_name)
                        streams.add(stream)

                return sorted(streams)

        except Exception as e:
            logger.error(f"Error getting streams: {e}")
            return ["а", "б", "в", "г"]  # По умолчанию
        return ["а", "б", "в", "г"]  # Fallback

    def get_current_semester_info(self) -> dict[str, object]:
        """Получить информацию о текущем семестре."""
        semester, year = self.current_semester
        return {"name": semester, "year": year, "is_current": True}
