import datetime
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from config import WEEK_DAYS
from get_raw import get_schedule_data, process_lessons
from get_id import find_schedule_ids
from ical import gen_ical
from processing import process_lessons_for_export
from xlsx import gen_excel_file
from lesson import Lesson

# --- Настройка логирования ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    """
    Главная функция для получения, обработки и экспорта расписания.
    """
    # Константы для запуска
    schedule_ids = find_schedule_ids(speciality=["32.05.01 медико-профилактическое дело"],
                                semester=["весенний"],
                                course_number=["2"],
                                academic_year=["2024/2025"],
                                )
    logger.info(f"Finded ids:{schedule_ids}")
    subgroup_name = "202б"
    
    # 1. Получение сырых данных
    schedule_data: list[dict] = []
    for schedule_id in schedule_ids:
        data = get_schedule_data(schedule_id)
        if data is not None:
            schedule_data.append(data)
        else:
            logger.warning("Eror in getting raw sch")
    logger.info(f"Sch len: {len(schedule_data)}")
    
    if not schedule_data:
        logger.error("Не удалось получить данные расписания. Завершение работы.")
        return

    all_lessons: list[Lesson] = []
    for sch in schedule_data:
        all_lessons.extend(process_lessons(sch))
    
    if not all_lessons:
        logger.info("Не найдено занятий для определения даты начала. Завершение работы.")
        return

    # 2. Определение первой даты расписания (логика остаётся здесь)
    earliest_lesson = min(all_lessons, key=lambda x: (int(x.weekNumber), WEEK_DAYS.get(x.dayName, 999)))
    first_week_number = int(earliest_lesson.weekNumber)
    first_day_index = WEEK_DAYS.get(earliest_lesson.dayName, 0)

    semestr_num: int = 0 if earliest_lesson.semester == "осенний" else 1
    year: int = int(earliest_lesson.academicYear.split("/")[semestr_num])
    month: int = [9, 2][semestr_num]
    first_monday_of_semestr: datetime.datetime = datetime.datetime(year, month, 1, tzinfo=ZoneInfo('Europe/Moscow'))

    first_date = first_monday_of_semestr + datetime.timedelta(weeks=first_week_number - 1, days=first_day_index)
    
    logger.info(f"Автоматически определена первая дата расписания: {first_date}")
    
    # 3. Обработка данных
    processed_lessons = process_lessons_for_export(all_lessons, subgroup_name, first_date)
    
    if not processed_lessons:
        logger.info(f"Не найдено занятий для подгруппы {subgroup_name} после обработки. Завершение работы.")
        return
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 4. Генерация файлов
    gen_excel_file(processed_lessons, subgroup_name)
    gen_ical(processed_lessons, subgroup_name)


if __name__ == "__main__":
    main()
