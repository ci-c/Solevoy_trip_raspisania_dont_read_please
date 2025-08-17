"""Пффф, а знал что всё это надо будет переписать нормально"""

from dataclasses import dataclass
from datetime import date, time
from enum import Enum
from typing import Any, Union
import csv
from pathlib import Path

FIRST_DATE = date(2025, 2, 3)  # Monday
LAST_DATE = date(2025, 8, 30)
WEEK_DAYS = {"пн": 1, "вт": 2, "ср": 3, "чт": 4, "пт": 5, "сб": 6, "вс": 7}


class LessonType(Enum):
    """Enumeration representing different types of lessons."""
    LECTURE = 0
    SEMINAR = 1


def expand_interval(value: str) -> list[int]:
    """Expand a range string like '1-3' into a list of integers [1, 2, 3]."""
    start, end = map(int, value.split("-"))
    return list(range(start, end + 1))


def process_schedule_cell(cell: str) -> list[int]:
    """Process the schedule cell string and convert it into a list of week numbers."""
    values = cell.replace(" ", "").split(",")
    result = []
    for value in values:
        if "-" in value:
            result.extend(expand_interval(value))
        else:
            result.append(int(value) if value.isdigit() else value)
    return result


class ScheduleTable:
    def __init__(self, file_path: Path):
        """Initialize the processor by reading the input file.

        The input file is expected to have columns:
            0 - Day (e.g., "пн", "вт", etc.)
            1 - Start Time
            2 - Subject
            3 - Weeks (e.g., "1,3-5")
            4 - Location
        """
        self._file_path = file_path
        self.schedule_data = self._process_file()

    def _process_file(self) -> list[list[Union[str, int, list[int]]]]:
        if self._file_path.suffix.lower() == ".csv":
            return self._process_csv_file()
        elif self._file_path.suffix.lower() in (".xlsx", ".xls"):
            return self._process_xlsx_file()
        else:
            raise ValueError("Unsupported file format")
    



@dataclass
class Lesson:
    """Dataclass for lesson data.

    Represents a lesson with various attributes such as group number,
    course details, timing information, and other related data.
    """

    group_num: int
    cuorse_name: str
    cuorse_num: int
    group_thred: str
    date: date
    start_time_1: time
    end_time_1: time
    start_time_2: time
    end_time_2: time
    type_: LessonType
    subject: str
    week_num: int
    lesson_number: str
    weekday: int
    SWP_A: bool
    SWP_B: bool
    other_dict: dict[str, Any]


def walk_days():
    current_date: date = FIRST_DATE
    week_num: int = 1
    while current_date <= LAST_DATE:
        if current_date.weekday() == 0:
            week_num += 1
        weekday = current_date.weekday()

        print(f"Week {week_num}, {current_date}")

        current_date += 1
