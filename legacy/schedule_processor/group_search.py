"""
Сервис поиска групп и объединения расписаний.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field

from .api import search_schedules
from .semester_detector import SemesterDetector


@dataclass
class GroupInfo:
    """Информация о группе."""

    number: str  # "103а"
    speciality: str
    course: int
    stream: str
    semester: str
    year: str
    lecture_schedule: dict | None = None
    seminar_schedule: dict | None = None
    unified_lessons: list["UnifiedLesson"] = field(default_factory=list)


@dataclass
class UnifiedLesson:
    """Объединенное занятие (лекция или семинар)."""

    subject: str
    type: str  # "lecture", "seminar", "practice"
    teacher: str
    room: str
    time_start: str
    time_end: str
    day_name: str
    day_of_week: int
    week_number: int
    group: str
    subgroup: str | None = None

    @property
    def time_range(self) -> str:
        return f"{self.time_start}-{self.time_end}"

    @property
    def full_info(self) -> str:
        type_emoji = "📚" if self.type == "lecture" else "📝"
        subgroup_info = f" | Подгр. {self.subgroup}" if self.subgroup else ""
        return f"{type_emoji} {self.subject} ({self.type})\n     👨‍🏫 {self.teacher} | 🏢 {self.room}{subgroup_info}"


class GroupSearchService:
    """Сервис поиска групп и объединения расписаний."""

    def __init__(self) -> None:
        self.semester_detector = SemesterDetector()
        self.groups_cache: dict[str, list[GroupInfo]] = {}

    async def search_group_by_number(self, group_number: str) -> list[GroupInfo]:
        """Поиск группы по номеру (103а, 204б, etc)."""
        from loguru import logger

        try:
            # Нормализуем номер группы
            normalized_number = self._normalize_group_number(group_number)
            logger.info(
                f"Searching for group: {group_number} (normalized: {normalized_number})"
            )

            # Проверяем кэш
            if normalized_number in self.groups_cache:
                logger.info(f"Found group {normalized_number} in cache")
                return self.groups_cache[normalized_number]

            # Получаем приоритетные фильтры (текущий семестр)
            try:
                priority_filters = self.semester_detector.get_priority_filters()
            except Exception as e:
                logger.warning(f"Failed to get priority filters: {e}, using defaults")
                priority_filters = {
                    "Семестр": ["осенний"],
                    "Учебный год": ["2024/2025"],
                }

            # Добавляем фильтр по группе
            search_filters = {
                **priority_filters,
                "Группа": [group_number, normalized_number],
            }

            logger.info(f"Search filters: {search_filters}")

            # Ищем расписания с защитой от ошибок
            try:
                schedules = await search_schedules(search_filters)
                logger.info(f"Found {len(schedules)} schedules")
            except Exception as e:
                logger.error(f"Error in search_schedules: {e}")
                schedules = []

            if not schedules:
                logger.warning(f"No schedules found for group {group_number}")
                return []

            # Группируем по типу (лекции/семинары)
            try:
                groups = self._process_schedules_to_groups(schedules, normalized_number)
                logger.info(f"Processed {len(groups)} groups")
            except Exception as e:
                logger.error(f"Error processing schedules: {e}")
                groups = []

            # Кэшируем результат
            self.groups_cache[normalized_number] = groups

            return groups

        except Exception as e:
            logger.error(f"Critical error in search_group_by_number: {e}")
            return []

    async def search_groups_by_filters(self, filters: dict) -> list[GroupInfo]:
        """Поиск групп по фильтрам."""
        # Добавляем текущий семестр к фильтрам
        priority_filters = self.semester_detector.get_priority_filters()
        combined_filters = {**priority_filters, **filters}

        # Ищем расписания
        schedules = await search_schedules(combined_filters)

        # Группируем по номерам групп
        groups_by_number = defaultdict(list)

        for schedule in schedules:
            group_numbers = self._extract_group_numbers_from_schedule(schedule)
            for group_num in group_numbers:
                groups_by_number[group_num].append(schedule)

        # Создаем объекты GroupInfo
        result = []
        for group_num, group_schedules in groups_by_number.items():
            groups = self._process_schedules_to_groups(group_schedules, group_num)
            result.extend(groups)

        return result

    def _normalize_group_number(self, group_number: str) -> str:
        """Нормализация номера группы."""
        # Убираем лишние символы, приводим к единому формату
        return re.sub(r"[^\w\d]", "", group_number.lower())

    def _process_schedules_to_groups(
        self, schedules: list[dict], group_number: str
    ) -> list[GroupInfo]:
        """Обработать расписания и создать информацию о группах."""
        if not schedules:
            return []

        # Группируем расписания по типам
        lecture_schedules = []
        seminar_schedules = []

        for schedule in schedules:
            schedule_type = self._detect_schedule_type(schedule)
            if schedule_type == "lecture":
                lecture_schedules.append(schedule)
            elif schedule_type == "seminar":
                seminar_schedules.append(schedule)

        # Создаем группу
        first_schedule = schedules[0]
        group_info = self._extract_group_info_from_schedule(
            first_schedule, group_number
        )

        # Добавляем расписания
        if lecture_schedules:
            group_info.lecture_schedule = lecture_schedules[0]
        if seminar_schedules:
            group_info.seminar_schedule = seminar_schedules[0]

        # Объединяем расписания в единый список занятий
        group_info.unified_lessons = self._merge_schedules_to_lessons(group_info)

        return [group_info]

    def _detect_schedule_type(self, schedule: dict) -> str:
        """Определить тип расписания (лекции или семинары)."""
        data = schedule.get("data", {})
        lessons = data.get("scheduleLessonDtoList", [])

        if not lessons:
            return "unknown"

        # Проверяем первые несколько занятий
        lesson_types = []
        for lesson in lessons[:10]:
            lesson_type = lesson.get("lessonType", "").lower()
            lesson_types.append(lesson_type)

        # Определяем преобладающий тип
        if any("лекц" in lt for lt in lesson_types):
            return "lecture"
        if any("семинар" in lt or "практ" in lt for lt in lesson_types):
            return "seminar"

        return "unknown"

    def _extract_group_info_from_schedule(
        self, schedule: dict, group_number: str
    ) -> GroupInfo:
        """Извлечь информацию о группе из расписания."""
        data = schedule.get("data", {})
        lessons = data.get("scheduleLessonDtoList", [])

        if not lessons:
            return GroupInfo(
                number=group_number,
                speciality="Неизвестно",
                course=1,
                stream="а",
                semester="осенний",
                year="2024/2025",
            )

        first_lesson = lessons[0]

        # Извлекаем информацию
        speciality = first_lesson.get("speciality", "Неизвестно")
        course = int(first_lesson.get("courseNumber", 1))
        semester = first_lesson.get("semester", "осенний")
        year = first_lesson.get("academicYear", "2024/2025")

        # Определяем поток из номера группы
        stream = (
            group_number[-1] if group_number and group_number[-1].isalpha() else "а"
        )

        return GroupInfo(
            number=group_number,
            speciality=speciality,
            course=course,
            stream=stream,
            semester=semester,
            year=year,
        )

    def _extract_group_numbers_from_schedule(self, schedule: dict) -> list[str]:
        """Извлечь номера групп из расписания."""
        data = schedule.get("data", {})
        lessons = data.get("scheduleLessonDtoList", [])

        groups = set()
        for lesson in lessons:
            group = lesson.get("group")
            if group:
                groups.add(group)

        return list(groups)

    def _merge_schedules_to_lessons(self, group_info: GroupInfo) -> list[UnifiedLesson]:
        """Объединить расписания лекций и семинаров в единый список."""
        unified_lessons = []

        # Обрабатываем лекции
        if group_info.lecture_schedule:
            lectures = self._parse_lessons_from_schedule(
                group_info.lecture_schedule, "lecture", group_info.number
            )
            unified_lessons.extend(lectures)

        # Обрабатываем семинары
        if group_info.seminar_schedule:
            seminars = self._parse_lessons_from_schedule(
                group_info.seminar_schedule, "seminar", group_info.number
            )
            unified_lessons.extend(seminars)

        # Сортируем по времени
        unified_lessons.sort(key=lambda x: (x.week_number, x.day_of_week, x.time_start))

        return unified_lessons

    def _parse_lessons_from_schedule(
        self, schedule: dict, lesson_type: str, group_number: str
    ) -> list[UnifiedLesson]:
        """Парсить занятия из расписания."""
        data = schedule.get("data", {})
        lessons_data = data.get("scheduleLessonDtoList", [])

        lessons = []
        day_mapping = {
            "понедельник": 1,
            "вторник": 2,
            "среда": 3,
            "четверг": 4,
            "пятница": 5,
            "суббота": 6,
            "воскресенье": 7,
        }

        for lesson_data in lessons_data:
            # Фильтруем по группе
            lesson_group = lesson_data.get("group", "")
            if group_number not in lesson_group:
                continue

            lesson = UnifiedLesson(
                subject=lesson_data.get("subject", "Неизвестно"),
                type=lesson_type,
                teacher=lesson_data.get("teacher", "Неизвестно"),
                room=lesson_data.get("room", "Неизвестно"),
                time_start=lesson_data.get("timeStart", ""),
                time_end=lesson_data.get("timeEnd", ""),
                day_name=lesson_data.get("dayName", ""),
                day_of_week=day_mapping.get(lesson_data.get("dayName", "").lower(), 1),
                week_number=int(lesson_data.get("weekNumber", 1)),
                group=lesson_group,
                subgroup=lesson_data.get("subgroup"),
            )

            lessons.append(lesson)

        return lessons

    def get_week_schedule(
        self, group_info: GroupInfo, week_number: int | None = None
    ) -> dict[str, list[UnifiedLesson]]:
        """Получить расписание на неделю."""
        if week_number is None:
            week_number = (
                self.semester_detector.get_current_semester_info().current_week
            )

        # Фильтруем занятия по номеру недели
        week_lessons = [
            lesson
            for lesson in group_info.unified_lessons
            if lesson.week_number == week_number
        ]

        # Группируем по дням недели
        week_schedule = defaultdict(list)
        for lesson in week_lessons:
            week_schedule[lesson.day_name].append(lesson)

        # Сортируем занятия в каждом дне по времени
        for day_lessons in week_schedule.values():
            day_lessons.sort(key=lambda x: x.time_start)

        return dict(week_schedule)

    def format_group_schedule(
        self, group_info: GroupInfo, week_number: int | None = None
    ) -> str:
        """Отформатировать расписание группы для отображения."""
        semester_info = self.semester_detector.get_current_semester_info()
        week_schedule = self.get_week_schedule(
            group_info, week_number or semester_info.current_week
        )

        if not week_schedule:
            return f"📅 **Расписание группы {group_info.number}**\n\n❌ Занятий на неделе {week_number or semester_info.current_week} не найдено."

        result = f"📅 **Расписание группы {group_info.number}**\n"
        result += f"🗓 Неделя {week_number or semester_info.current_week} | {semester_info.name.title()} семестр {semester_info.year}\n\n"

        days_order = [
            "понедельник",
            "вторник",
            "среда",
            "четверг",
            "пятница",
            "суббота",
            "воскресенье",
        ]

        for day in days_order:
            if day in week_schedule:
                result += f"**{day.title()}**\n"

                for lesson in week_schedule[day]:
                    result += f"🕐 {lesson.time_range} | {lesson.full_info}\n\n"

                result += "\n"

        return result
