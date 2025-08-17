import requests
import json
import logging
from typing import Dict, List, Optional
from lesson import Lesson

# Set up logging for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# A simple log handler for console output without a custom formatter
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def get_schedule_data(schedule_id: int) -> Optional[Dict]:
    """
    Fetches schedule data from the API by its ID.
    
    Args:
        schedule_id: The ID of the schedule to fetch.
        
    Returns:
        A dictionary with the schedule data or None if an error occurs.
    """
    api_url = f'https://frsview.szgmu.ru/api/xlsxSchedule/findById?xlsxScheduleId={schedule_id}'
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        # Log general schedule parameters
        logger.info("-" * 20)
        logger.info("General Schedule Information:")
        logger.info(f"  File Name: {data.get('fileName')}")
        logger.info(f"  Form Type: {data.get('formType')}")
        logger.info(f"  Schedule Status: {data.get('scheduleStatus', {}).get('name')}")
        logger.info("-" * 20)

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error occurred: {e}")
        return None
    except json.JSONDecodeError:
        logger.error("JSON decoding error: The response is not valid JSON.")
        return None

def process_lessons(schedule_data: Dict) -> List[Lesson]:
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
    return lessons

def main():
    """
    Main function to fetch, process, and display the schedule.
    """
    schedule_id = 576
    subgroup_name = "232б"
    
    schedule_data = get_schedule_data(schedule_id)
    
    if schedule_data:
        all_lessons = process_lessons(schedule_data)
        
        filtered_lessons = [
            lesson for lesson in all_lessons if lesson.subgroup == subgroup_name
        ]
        
        if not filtered_lessons:
            logger.info(f"No lessons found for subgroup {subgroup_name}.")
            return

        # Define the order of days
        day_order = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
        day_map = {day: i for i, day in enumerate(day_order)}
        
        # Group lessons by week
        lessons_by_week = {}
        for lesson in filtered_lessons:
            week_number = lesson.weekNumber
            if week_number not in lessons_by_week:
                lessons_by_week[week_number] = []
            lessons_by_week[week_number].append(lesson)
        
        # Sort weeks and then lessons within each week
        sorted_weeks = sorted(lessons_by_week.keys(), key=lambda x: int(x) if isinstance(x, str) and x.isdigit() else float('inf'))
        
        for week in sorted_weeks:
            print(f"\n--- Неделя {week} ---")
            
            # Sort lessons within the week by day and then by time
            sorted_lessons = sorted(
                lessons_by_week[week],
                key=lambda lesson: (
                    day_map.get(lesson.dayName, len(day_order)),
                    lesson.pairTime or ''
                )
            )
            
            current_day = None
            for lesson in sorted_lessons:
                if lesson.dayName and lesson.dayName != current_day:
                    print(f"\n  --- {lesson.dayName.upper()} ---")
                    current_day = lesson.dayName
                
                print(f"- {lesson.pairTime}: {lesson.subjectName}")
                if lesson.auditoryNumber:
                    print(f"  Аудитория: {lesson.auditoryNumber}")
                if lesson.locationAddress:
                    print(f"  Адрес: {lesson.locationAddress}")
                if lesson.lectorName:
                    print(f"  Преподаватель: {lesson.lectorName}")
                print("-" * 10)
    else:
        logger.error("Could not fetch schedule data.")

if __name__ == "__main__":
    main()
