import json
import logging

import requests

# Set up logging for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def find_schedule_ids(
    group_stream: list[str] | None = None,
    speciality: list[str] | None = None,
    course_number: list[str] | None = None,
    academic_year: list[str] | None = None,
    lesson_type: list[str] | None = None,
    semester: list[str] | None = None,
) -> list[int]:
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
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()

        if "content" in data:
            return [item["id"] for item in data["content"]]
        logger.error("API response is missing the 'content' key.")
        return []

    except requests.exceptions.RequestException as e:
        logger.exception(f"HTTP request error occurred: {e}")
        return []
    except json.JSONDecodeError:
        logger.exception("JSON decoding error: The response is not valid JSON.")
        return []


if __name__ == "__main__":
    ids = find_schedule_ids()
