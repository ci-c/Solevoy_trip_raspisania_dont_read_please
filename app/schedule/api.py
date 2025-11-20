"""API client for SZGMU schedule data.

Зона ответственности:
- Взаимодействие с внешним API СЗГМУ для получения данных расписания
- Поиск расписаний по фильтрам (курс, специальность, поток, семестр)
- Загрузка детальной информации о расписаниях по ID
- Парсинг данных занятий и преобразование в объекты модели
- Обеспечение надежности запросов с тайм-аутами и обработкой ошибок
"""

import json
import logging
from typing import Any

import httpx

from app.schedule.models import Lesson

# Set up logging for the module
logger = logging.getLogger(__name__)


def find_schedule_ids(
    group_stream: list[str] | None = None,
    speciality: list[str] | None = None,
    course_number: list[str] | None = None,
    academic_year: list[str] | None = None,
    lesson_type: list[str] | None = None,
    semester: list[str] | None = None,
) -> list[int]:
    """Searches for schedule IDs by sending a POST request to the API with specified parameters.

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
            return [item["id"] for item in data["content"]]
        logger.error("API response is missing the 'content' key.")
        return []

    except httpx.HTTPStatusError as e:
        logger.exception(
            "Schedule ID request failed with status %s", e.response.status_code,
        )
        return []
    except httpx.RequestError as e:
        logger.exception("HTTP request error occurred: %s", e)
        return []
    except Exception as e:
        logger.exception("Unexpected error searching schedule IDs: %s", e)
        return []
    except json.JSONDecodeError:
        logger.exception("JSON decoding error: The response is not valid JSON.")
        return []


def get_schedule_data(schedule_id: int) -> dict | None:
    """Fetches schedule data from the API by its ID.

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
        logger.info("  File Name: %s", data.get("fileName"))
        logger.debug("  xlsxHeaderDto: %s", data.get("xlsxHeaderDto"))
        logger.info("  Form Type: %s", data.get("formType"))
        logger.info("  updateTime: %s", data.get("updateTime"))
        logger.info("  isUploadedFromExcel: %s", data.get("isUploadedFromExcel"))
        logger.info("  Schedule Status: %s", data.get("statusId"))
        # logger.info(f"  Keys: {data.keys()}")
        if data.get("scheduleLessonDtoList"):
            logger.info("  Sample Lesson: %s", data.get("scheduleLessonDtoList", [])[0])
        logger.info("-" * 20)

        return data
    except httpx.HTTPStatusError as e:
        logger.exception(
            "Schedule data request failed with status %s",
            e.response.status_code,
        )
        return None
    except httpx.RequestError as e:
        logger.exception("HTTP request error occurred: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error fetching schedule data: %s", e)
        return None
    except json.JSONDecodeError:
        logger.exception("JSON decoding error: The response is not valid JSON.")
        return None


def process_lessons(schedule_data: dict) -> list[Lesson]:
    """Processes a list of lesson dictionaries, converts them to Lesson objects,
    and returns a list of all lessons.

    Args:
        schedule_data: A dictionary containing schedule data.

    Returns:
        A list of Lesson objects.

    """
    lessons: list[Lesson] = []
    if "scheduleLessonDtoList" in schedule_data:
        for lesson_dict in schedule_data["scheduleLessonDtoList"]:
            try:
                lesson_obj = Lesson(**lesson_dict)
                lessons.append(lesson_obj)
            except TypeError as e:
                logger.exception("Error creating Lesson object due to missing fields: %s", e)
                logger.exception(
                    "Skipping this lesson entry with keys: %s", list(lesson_dict.keys()),
                )
                continue
    logger.info("Processed %s lessons", len(lessons))
    return lessons


async def get_available_filters() -> dict[str, list[str]]:
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
        logger.exception("Error loading filters: %s", e)
        # Fallback to minimal filters
        return {
            "Курс": ["1", "2", "3", "4", "5", "6"],
            "Специальность": ["Лечебное дело", "Педиатрия"],
            "Поток": ["а", "б", "в"],
        }


async def search_schedules(selected_filters: dict[str, list[str]]) -> list[dict]:
    """Search schedules based on selected filters."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    logger.info("Starting schedule search with filters: %s", selected_filters)

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
            "API parameters: course=%s, speciality=%s, stream=%s",
            course_number, speciality, group_stream,
        )

        loop = asyncio.get_event_loop()
        results: list[dict[str, Any]] = []

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
            except TimeoutError:
                logger.exception("Schedule IDs search timed out")
                return []

            logger.info("Found %s schedule IDs", len(schedule_ids))

            if not schedule_ids:
                logger.warning("No schedule IDs found")
                return []

            max_schedules = min(5, len(schedule_ids))

            for i, schedule_id in enumerate(schedule_ids[:max_schedules]):
                logger.info(
                    "Processing schedule %s/%s: ID %s",
                    i + 1, max_schedules, schedule_id,
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
                                "fileName", f"Schedule {schedule_id}",
                            )

                        results.append(
                            {
                                "id": schedule_id,
                                "display_name": display_name,
                                "data": schedule_data,
                            },
                        )
                        logger.info(
                            "Successfully processed schedule %s", schedule_id,
                        )
                    else:
                        logger.warning("No data for schedule %s", schedule_id)

                except TimeoutError:
                    logger.warning("Timeout getting data for schedule %s", schedule_id)
                    continue
                except Exception as e:
                    logger.exception("Error processing schedule %s: %s", schedule_id, e)
                    continue

        logger.info("Returning %s processed schedules", len(results))
        return results

    except Exception as e:
        logger.exception("Critical error in search_schedules: %s", e)
        logger.exception("Traceback: %s", e.__traceback__)
        return []
