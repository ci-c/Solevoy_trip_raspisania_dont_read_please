"""Core functionality for schedule processing."""

import datetime
import logging
from pathlib import Path
from typing import List, Optional

from .api import find_schedule_ids, get_schedule_data, process_lessons
from .config import WEEK_DAYS
from .generator import process_lessons_for_export, gen_excel_file, gen_ical
from .models import Lesson

logger = logging.getLogger(__name__)


def process_api_schedule(
    speciality: List[str],
    semester: List[str], 
    course_number: List[str],
    academic_year: List[str],
    subgroup_name: str,
    group_stream: Optional[List[str]] = None
) -> bool:
    """
    Main function for getting, processing and exporting schedule from API.
    
    Args:
        speciality: List of specialties
        semester: List of semesters
        course_number: List of course numbers
        academic_year: List of academic years
        subgroup_name: Subgroup name for filtering
        group_stream: Optional list of group streams
        
    Returns:
        True if successful, False otherwise
    """
    # Find schedule IDs
    schedule_ids = find_schedule_ids(
        speciality=speciality,
        semester=semester,
        course_number=course_number,
        academic_year=academic_year,
        group_stream=group_stream
    )
    logger.info(f"Found IDs: {schedule_ids}")
    
    if not schedule_ids:
        logger.error("No schedule IDs found. Terminating.")
        return False
    
    # 1. Get raw data
    schedule_data: list[dict] = []
    for schedule_id in schedule_ids:
        data = get_schedule_data(schedule_id)
        if data is not None:
            schedule_data.append(data)
        else:
            logger.warning("Error getting raw schedule")
    logger.info(f"Schedule data length: {len(schedule_data)}")
    
    if not schedule_data:
        logger.error("Could not get schedule data. Terminating.")
        return False

    all_lessons: list[Lesson] = []
    for sch in schedule_data:
        all_lessons.extend(process_lessons(sch))
    
    if not all_lessons:
        logger.info("No lessons found to determine start date. Terminating.")
        return False

    # 2. Determine first schedule date
    earliest_lesson = min(all_lessons, key=lambda x: (int(x.weekNumber), WEEK_DAYS.get(x.dayName, 999)))
    first_day_index = WEEK_DAYS.get(earliest_lesson.dayName, 0)

    semester_num: int = 0 if earliest_lesson.semester == "осенний" else 1
    year: int = int(earliest_lesson.academicYear.split("/")[semester_num])
    month: int = [9, 2][semester_num]
    first_monday_of_semester: datetime.date = datetime.date(year, month, 1)
    while first_monday_of_semester.weekday() != first_day_index:
        first_monday_of_semester += datetime.timedelta(days=1)

    first_date = first_monday_of_semester + datetime.timedelta(days=first_day_index)
    
    logger.info(f"Automatically determined first schedule date: {first_date}")
    
    # 3. Process data
    processed_lessons = process_lessons_for_export(all_lessons, subgroup_name, first_monday_of_semester)
    
    if not processed_lessons:
        logger.info(f"No lessons found for subgroup {subgroup_name} after processing. Terminating.")
        return False
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 4. Generate files
    gen_excel_file(processed_lessons, subgroup_name)
    gen_ical(processed_lessons, subgroup_name)
    
    return True


def process_file_schedule(input_dir: str = "input", output_dir: str = "output") -> bool:
    """
    Process schedule from local files (CSV/XLSX).
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        
    Returns:
        True if successful, False otherwise
    """
    
    # This would need implementation similar to original script.py
    # For now, return False to indicate not implemented
    logger.warning("File processing not yet implemented in new structure")
    return False