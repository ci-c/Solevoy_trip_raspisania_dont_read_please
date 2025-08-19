import requests
import json
import logging
from typing import Dict, List, Optional

# Set up logging for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        response = requests.post(url, headers=headers, data=json.dumps(payload))
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


if __name__ == "__main__":
    ids = find_schedule_ids()
    print(ids)