import datetime
import logging
from operator import attrgetter

from config import RINGS, WEEK_DAYS
from lesson import Lesson
from post_lesson import PostLesson

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def process_lessons_for_export(
    raw_lessons: list[Lesson], subgroup_name: str, first_monday: datetime.date,
) -> list[PostLesson]:
    """
    Обрабатывает, фильтрует, объединяет и преобразует сырые данные занятий
    в список объектов PostLesson.

    Args:
        raw_lessons: Список сырых объектов Lesson.
        subgroup_name: Имя подгруппы для фильтрации.
        first_monday: Дата начала расписания.

    Returns:
        Отфильтрованный, отсортированный и обработанный список объектов PostLesson.
    """


    # 1. Фильтрация по подгруппе
    def f_filter(lesson: Lesson) -> bool:
        return lesson.subgroup == subgroup_name

    filtered_lessons = [lesson for lesson in raw_lessons if f_filter(lesson)]
    processed_lessons: list[PostLesson] = []

    for lesson in filtered_lessons:
        week_num = int(lesson.weekNumber)
        day_index = WEEK_DAYS.get(lesson.dayName, 0)

        # Получаем данные о времени из единого источника
        lesson_type_key = "л" if "лекция" in lesson.lessonType.lower() else "с"

        # --- НОВАЯ НАДЕЖНАЯ ЛОГИКА ОБРАБОТКИ ВРЕМЕНИ ---
        # 1. Берем только время начала (часть строки до знака "-")
        start_time_str = lesson.pairTime.split("-")[0]
        t = start_time_str.split(".")
        lesson_start_time = datetime.time(int(t[0]), int(t[1]))

        # 2. Ищем номер пары по совпадению времени НАЧАЛА
        lesson_number = None
        for num, ring in enumerate(RINGS[lesson_type_key]):
            # Сверяем только с временем начала первой "половинки" пары
            if ring[0][0] == lesson_start_time:
                lesson_number = num
                break  # Нашли пару, выходим из цикла

        # 3. Если номер не найден, значит это вторая часть пары или неизвестное время -> пропускаем
        if lesson_number is None:
            continue
        # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

        date = first_monday + datetime.timedelta(weeks=week_num - 1, days=day_index)

        # Создаём чистый объект PostLesson
        post_lesson_meta = {
            "location": lesson.locationAddress,
            "department": lesson.departmentName,
        }
        post_lesson = PostLesson(
            date=date,
            lesson_number=lesson_number,
            lesson_type=lesson_type_key.upper(),
            subject_name=lesson.subjectName,
            metadata=post_lesson_meta,
            lesson_seq=1,
        )
        processed_lessons.append(post_lesson)

    # 3. Сортировка по дате и номеру занятия
    processed_lessons.sort(key=attrgetter("date", "lesson_number"))
    logger.info(f"raw_lessons={len(raw_lessons)};filtered_lessons={len(filtered_lessons)};processed_lessons={len(processed_lessons)}")
    return processed_lessons
