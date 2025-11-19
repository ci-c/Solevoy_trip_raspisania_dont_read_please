"""
API client for SZGMU schedule data.

Зона ответственности:
- Взаимодействие с внешним API СЗГМУ для получения данных расписания
- Поиск расписаний по фильтрам (курс, специальность, поток, семестр)
- Загрузка детальной информации о расписаниях по ID
- Парсинг данных занятий и преобразование в объекты модели
- Обеспечение надежности запросов с тайм-аутами и обработкой ошибок
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.schedule.models import Lesson

# Set up logging for the module
logger = logging.getLogger(__name__)


def find_schedule_ids(
    group_stream: List[str] | None = None,
    speciality: List[str] | None = None,
    course_number: List[str] | None = None,
    academic_year: List[str] | None = None,
    lesson_type: Optional[List[str]] = None,
    semester: Optional[List[str]] = None,
) -> List[int]:
    """
    Searches for schedule IDs by sending a POST request to the API with specified parameters.

    Args:
        group_stream: List of group streams (e.g., ['в']).
        speciality: List of specialties (e.g., ['31.05.01 лечебное дело']).
        course_number: List of course numbers (e.g., ['2']).
        academic_year: List of academic years (e.g., ['2024/2025']).
        lesson_type: Optional list of lesson types (e.g., ['семинарского']).
        semester: Optional list of semesters (e.g., ['весенний']).

    Returns:
        A list of found schedule IDs or an empty list if an error occurs.
    """
    url = "https://frsview.szgmu.ru/api/xlsxSchedule/findAll/0"

    if lesson_type is None:
        lesson_type = []
    if semester is None:
        semester = []

    payload = {
        "groupStream": group_stream,
        "speciality": speciality,
        "courseNumber": course_number,
        "academicYear": academic_year,
        "lessonType": lesson_type,
        "semester": semester,
    }

    headers = {"Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        if "content" in data:
            found_ids = [item["id"] for item in data["content"]]
            return found_ids
        else:
            logger.error("API response is missing the 'content' key.")
            return []

    except httpx.HTTPStatusError as e:
        logger.error(
            "Schedule ID request failed with status %s", e.response.status_code
        )
        return []
    except httpx.RequestError as e:
        logger.error(f"HTTP request error occurred: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error searching schedule IDs: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("JSON decoding error: The response is not valid JSON.")
        return []


def get_schedule_data(schedule_id: int) -> dict | None:
    """
    Fetches schedule data from the API by its ID.

    Args:
        schedule_id: The ID of the schedule to fetch.

    Returns:
        A dictionary with the schedule data or None if an error occurs.
    """
    api_url = f"https://frsview.szgmu.ru/api/xlsxSchedule/findById?xlsxScheduleId={schedule_id}"

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(api_url)
            response.raise_for_status()
            data = response.json()

        # Log general schedule parameters
        logger.info("-" * 20)
        logger.info("General Schedule Information:")
        logger.info(f"  File Name: {data.get('fileName')}")
        logger.debug(f"  xlsxHeaderDto: {data.get('xlsxHeaderDto')}")
        logger.info(f"  Form Type: {data.get('formType')}")
        logger.info(f"  updateTime: {data.get('updateTime')}")
        logger.info(f"  isUploadedFromExcel: {data.get('isUploadedFromExcel')}")
        logger.info(f"  Schedule Status: {data.get('statusId')}")
        # logger.info(f"  Keys: {data.keys()}")
        if data.get("scheduleLessonDtoList"):
            logger.info(f"  Sample Lesson: {data.get('scheduleLessonDtoList', [])[0]}")
        logger.info("-" * 20)

        return data
    except httpx.HTTPStatusError as e:
        logger.error(
            "Schedule data request failed with status %s",
            e.response.status_code,
        )
        return None
    except httpx.RequestError as e:
        logger.error(f"HTTP request error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching schedule data: {e}")
        return None
    except json.JSONDecodeError:
        logger.error("JSON decoding error: The response is not valid JSON.")
        return None


def process_lessons(schedule_data: Dict) -> list[Lesson]:
    """
    Processes a list of lesson dictionaries, converts them to Lesson objects,
    and returns a list of all lessons.

    Args:
        schedule_data: A dictionary containing schedule data.

    Returns:
        A list of Lesson objects.
    """
    lessons: List[Lesson] = []
    if "scheduleLessonDtoList" in schedule_data:
        for lesson_dict in schedule_data["scheduleLessonDtoList"]:
            try:
                lesson_obj = Lesson(**lesson_dict)
                lessons.append(lesson_obj)
            except TypeError as e:
                logger.error(f"Error creating Lesson object due to missing fields: {e}")
                logger.error(
                    f"Skipping this lesson entry with keys: {list(lesson_dict.keys())}"
                )
                continue
    logger.info(f"Processed {len(lessons)} lessons")
    return lessons


async def get_available_filters() -> Dict[str, List[str]]:
    """Get available filters for the bot interface."""
    # Return static options to avoid API timeout issues
    # TODO Implement dynamic loading with timeout protection
    logger.info("Loading static filters for bot interface")

    try:
        return {
            "Курс": ["1", "2", "3", "4", "5", "6"],
            "Специальность": [
                "Лечебное дело",
                "Медико-профилактическое дело",
                "Фармация",
                "Педиатрия",
                "Стоматология",
                "Биотехнология",
                "Клиническая психология",
            ],
            "Поток": ["а", "б", "в", "г"],
            "Семестр": ["весенний", "осенний"],
            "Учебный год": ["2024/2025", "2025/2026"],
        }
    except Exception as e:
        logger.error(f"Error loading filters: {e}")
        # Fallback to minimal filters
        return {
            "Курс": ["1", "2", "3", "4", "5", "6"],
            "Специальность": ["Лечебное дело", "Педиатрия"],
            "Поток": ["а", "б", "в"],
        }


async def search_schedules(selected_filters: Dict[str, List[str]]) -> List[Dict]:
    """Search schedules based on selected filters."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    logger.info(f"Starting schedule search with filters: {selected_filters}")

    try:
        # Map bot filters to API parameters
        course_number = selected_filters.get("Курс", [])
        speciality = selected_filters.get("Специальность", [])
        group_stream = selected_filters.get("Поток", [])
        semester = selected_filters.get("Семестр", [])
        academic_year = selected_filters.get("Учебный год", [])
        group = selected_filters.get("Группа", [])

        # Если есть группа, пробуем извлечь параметры из номера группы
        if group and not course_number:
            for group_num in group:
                # Извлекаем курс из номера группы (например, из "103а" -> "1")
                if group_num and group_num[0].isdigit():
                    course_number = [group_num[0]]
                    break

        logger.info(
            f"API parameters: course={course_number}, speciality={speciality}, stream={group_stream}"
        )

        loop = asyncio.get_event_loop()
        results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor() as executor:
            # Find schedule IDs с защитой от блокировки
            def _find_schedule_ids_sync():
                return find_schedule_ids(
                    group_stream=group_stream,
                    speciality=speciality,
                    course_number=course_number,
                    academic_year=academic_year,
                    semester=semester,
                )

            try:
                schedule_ids = await asyncio.wait_for(
                    loop.run_in_executor(executor, _find_schedule_ids_sync),
                    timeout=20.0,
                )
            except asyncio.TimeoutError:
                logger.error("Schedule IDs search timed out")
                return []

            logger.info(f"Found {len(schedule_ids)} schedule IDs")

            if not schedule_ids:
                logger.warning("No schedule IDs found")
                return []

            max_schedules = min(5, len(schedule_ids))

            for i, schedule_id in enumerate(schedule_ids[:max_schedules]):
                logger.info(
                    f"Processing schedule {i + 1}/{max_schedules}: ID {schedule_id}"
                )

                def _get_schedule_data_sync():
                    return get_schedule_data(schedule_id)

                try:
                    schedule_data = await asyncio.wait_for(
                        loop.run_in_executor(executor, _get_schedule_data_sync),
                        timeout=15.0,
                    )

                    if schedule_data:
                        lessons = schedule_data.get("scheduleLessonDtoList", [])
                        if lessons:
                            first_lesson = lessons[0]
                            speciality_name = first_lesson.get("speciality", "Unknown")
                            course_num = first_lesson.get("courseNumber", "Unknown")
                            stream = first_lesson.get("groupStream", "Unknown")
                            semester_name = first_lesson.get("semester", "Unknown")
                            year = first_lesson.get("academicYear", "Unknown")

                            display_name = (
                                f"{speciality_name} - {course_num} курс, {stream} поток, "
                                f"{semester_name} {year}"
                            )

                            if group:
                                group_found = False
                                for lesson in lessons[:10]:
                                    lesson_group = lesson.get("group", "")
                                    if any(
                                        g.lower() in lesson_group.lower() for g in group
                                    ):
                                        group_found = True
                                        break
                                if not group_found:
                                    logger.info(
                                        "Schedule %s doesn't contain requested group",
                                        schedule_id,
                                    )
                                    continue
                        else:
                            display_name = schedule_data.get(
                                "fileName", f"Schedule {schedule_id}"
                            )

                        results.append(
                            {
                                "id": schedule_id,
                                "display_name": display_name,
                                "data": schedule_data,
                            }
                        )
                        logger.info(
                            "Successfully processed schedule %s", schedule_id
                        )
                    else:
                        logger.warning("No data for schedule %s", schedule_id)

                except asyncio.TimeoutError:
                    logger.warning("Timeout getting data for schedule %s", schedule_id)
                    continue
                except Exception as e:
                    logger.error(f"Error processing schedule {schedule_id}: {e}")
                    continue

        logger.info(f"Returning {len(results)} processed schedules")
        return results

    except Exception as e:
        logger.error(f"Critical error in search_schedules: {e}")
        logger.error(f"Traceback: {e.__traceback__}")
        return []
