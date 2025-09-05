"""API client for schedule data."""

import requests
import json
import logging
from typing import Dict, List, Optional
from .models import Lesson

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
    url = 'https://frsview.szgmu.ru/api/xlsxSchedule/findAll/0'
    
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
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # Добавляем тайм-аут 10 секунд для API запросов
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'content' in data:
            found_ids = [item['id'] for item in data['content']]
            return found_ids
        else:
            logger.error("API response is missing the 'content' key.")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error occurred: {e}")
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
    api_url = f'https://frsview.szgmu.ru/api/xlsxSchedule/findById?xlsxScheduleId={schedule_id}'
    
    try:
        # Добавляем тайм-аут 15 секунд для загрузки данных расписания
        response = requests.get(api_url, timeout=15)
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
        #logger.info(f"  Keys: {data.keys()}")
        if data.get('scheduleLessonDtoList'):
            logger.info(f"  Sample Lesson: {data.get('scheduleLessonDtoList', [])[0]}")
        logger.info("-" * 20)

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error occurred: {e}")
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
    if 'scheduleLessonDtoList' in schedule_data:
        for lesson_dict in schedule_data['scheduleLessonDtoList']:
            try:
                lesson_obj = Lesson(**lesson_dict)
                lessons.append(lesson_obj)
            except TypeError as e:
                logger.error(f"Error creating Lesson object due to missing fields: {e}")
                logger.error(f"Skipping this lesson entry with keys: {list(lesson_dict.keys())}")
                continue
    logger.info(f"Processed {len(lessons)} lessons")
    return lessons


async def get_available_filters() -> Dict[str, List[str]]:
    """Get available filters for the bot interface."""
    # Return static options to avoid API timeout issues
    # TODO: Implement dynamic loading with timeout protection
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
                "Клиническая психология"
            ],
            "Поток": ["а", "б", "в", "г"],
            "Семестр": ["весенний", "осенний"],
            "Учебный год": ["2024/2025", "2025/2026"]
        }
    except Exception as e:
        logger.error(f"Error loading filters: {e}")
        # Fallback to minimal filters
        return {
            "Курс": ["1", "2", "3", "4", "5", "6"],
            "Специальность": ["Лечебное дело", "Педиатрия"],
            "Поток": ["а", "б", "в"]
        }


async def search_schedules(selected_filters: Dict[str, List[str]]) -> List[Dict]:
    """Search schedules based on selected filters."""
    # Map bot filters to API parameters
    course_number = selected_filters.get("Курс", [])
    speciality = selected_filters.get("Специальность", [])
    group_stream = selected_filters.get("Поток", [])
    semester = selected_filters.get("Семестр", [])
    academic_year = selected_filters.get("Учебный год", [])
    
    # Find schedule IDs
    schedule_ids = find_schedule_ids(
        group_stream=group_stream,
        speciality=speciality,
        course_number=course_number,
        academic_year=academic_year,
        semester=semester
    )
    
    if not schedule_ids:
        return []
    
    # Get schedule data for each ID and format for display
    results = []
    for schedule_id in schedule_ids[:10]:  # Limit to first 10 results
        schedule_data = get_schedule_data(schedule_id)
        if schedule_data:
            # Extract meaningful display name from schedule data
            lessons = schedule_data.get('scheduleLessonDtoList', [])
            if lessons:
                first_lesson = lessons[0]
                speciality_name = first_lesson.get('speciality', 'Unknown')
                course_num = first_lesson.get('courseNumber', 'Unknown')
                stream = first_lesson.get('groupStream', 'Unknown')
                semester_name = first_lesson.get('semester', 'Unknown')
                year = first_lesson.get('academicYear', 'Unknown')
                
                display_name = f"{speciality_name} - {course_num} курс, {stream} поток, {semester_name} {year}"
            else:
                file_name = schedule_data.get('fileName', f'Schedule {schedule_id}')
                display_name = file_name
            
            results.append({
                'id': schedule_id,
                'display_name': display_name,
                'data': schedule_data
            })
    
    return results