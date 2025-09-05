import datetime
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo
import ics
import rich
from config import RINGS
from post_lesson import PostLesson

def gen_ical(schedule_data: List[PostLesson], subgroup_name: str) -> None:
    """
    Генерирует файл iCal из списка объектов PostLesson.

    Args:
        schedule_data: Список объектов PostLesson.
        subgroup_name: Имя подгруппы для именования файла.
    """
    if not schedule_data:
        rich.print("[bold red]Нет данных для генерации iCal файла.[/bold red]")
        return
        
    calendar = ics.Calendar()
    moscow_tz = ZoneInfo('Europe/Moscow')

    for lesson in schedule_data:
        # 1. Получение времени начала и конца из RINGS
        lesson_type_key = lesson.lesson_type.lower()
        try:
            time_info = RINGS[lesson_type_key][lesson.lesson_number]
            start_time = time_info[0][0]
            end_time = time_info[1][1] 
        except (KeyError, IndexError):
            rich.print(f"[bold yellow]Предупреждение:[/bold yellow] Не удалось найти время для '{lesson.subject_name}' ({lesson.date}). Пропускаю.")
            continue

        # 2. Создание события
        event = ics.Event()
        event.begin = datetime.datetime.combine(lesson.date, start_time, tzinfo=moscow_tz)
        event.end = datetime.datetime.combine(lesson.date, end_time, tzinfo=moscow_tz)
        event.name = f"№{lesson.lesson_number + 1} {lesson.lesson_type} {lesson.subject_name}"
        event.created = datetime.datetime.now(tz=moscow_tz)

        # 3. Добавление метаданных
        event.location = lesson.metadata.get("location", "")
        event.categories = [{"Л": "Лекция", "С": "Семинар"}.get(lesson.lesson_type, "Занятие"), "СЗГМУ"]
        
        description_parts = []
        department = lesson.metadata.get("department")
        if department:
            description_parts.append(f"Кафедра: {department}")
        
        event.description = "\n".join(description_parts)
        calendar.events.add(event)

    # 4. Сохранение файла
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    filename = output_dir / f"{subgroup_name}.ics"
    
    if not calendar.events:
        rich.print(f"[bold yellow]Не создано ни одного события. Файл {filename} не будет сохранен.[/bold yellow]")
        return
        
    rich.print(f"Сохраняю файл: [cyan]{filename}[/cyan] ({len(calendar.events)} событий)")
    with filename.open("wb") as ical_file:
        ical_file.write(calendar.serialize().encode('utf-8'))