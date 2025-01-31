"""Script for processing schedule data with improved structure and maintainability."""

import csv
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias

import ics
import openpyxl
import rich
from zoneinfo import ZoneInfo

TimeSlot: TypeAlias = list[datetime.time]

@dataclass
class ScheduleConfig:
    """Configuration settings for schedule processing."""
    add_breaks: bool = False
    first_date: datetime.date = datetime.date(2025, 2, 3)  # Monday
    expected_filename_parts: tuple[int, ...] = (4, 5)
    schedule_column_index: int = 3
    width_columns: list[int] = [8, 12, 4, 4, 16, 4, 20]

@dataclass
class TimeSlotConfig:
    """Time slot configuration for different schedule types."""
    start: datetime.time
    end: datetime.time
    break_start: datetime.time
    break_end: datetime.time
    periods: str

    @classmethod
    def from_list(cls, data: list) -> "TimeSlotConfig":
        """Create TimeSlotConfig from list of values."""
        return cls(data[0], data[1], data[2], data[3], data[4])

class ScheduleRings:
    """Schedule time slots configuration."""
    
    def __init__(self) -> None:
        self.seminar = {
            "9:00": [datetime.time(9, 0), datetime.time(10, 30), 
                    datetime.time(10, 45), datetime.time(12, 15), '1,2'],
            "13:10": [datetime.time(13, 10), datetime.time(14, 40),
                     datetime.time(14, 55), datetime.time(16, 25), '3,4'],
        }
        
        self.lecture = {
            "9:00": [datetime.time(9, 0), datetime.time(9, 45),
                    datetime.time(9, 50), datetime.time(10, 35), '1'],
            "10:55": [datetime.time(10, 55), datetime.time(11, 40),
                     datetime.time(11, 45), datetime.time(12, 30), '2'],
            "13:10": [datetime.time(13, 10), datetime.time(13, 55),
                     datetime.time(14, 0), datetime.time(14, 45), '3'],
            "15:00": [datetime.time(15, 0), datetime.time(15, 45),
                     datetime.time(15, 50), datetime.time(16, 35), '4'],
            "16:45": [datetime.time(16, 45), datetime.time(17, 30),
                     datetime.time(17, 35), datetime.time(18, 20), '5'],
        }

    def get_slots(self, schedule_type: str) -> dict[str, list]:
        """Get time slots for specified schedule type."""
        return self.lecture if schedule_type == 'l' else self.seminar

class WeekDays:
    """Weekday mappings."""
    
    DAYS_TO_NUM = {'пн': 0, 'вт': 1, 'ср': 2, 'чт': 3, 'пт': 4, 'сб': 5, 'вс': 6}
    NUM_TO_DAYS = {
        0: 'Пн', 1: 'Вт', 2: 'Ср',
        3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'
    }

class ScheduleProcessor:
    """Main schedule processing class."""

    def __init__(self) -> None:
        self.config = ScheduleConfig()
        self.rings = ScheduleRings()
        self.week_days = WeekDays()

    def process_schedule_file(self, file_path: Path) -> tuple[tuple[str, ...], list[Any]]:
        """Process a single schedule file and return its data."""
        file_name = file_path.stem.lower()
        filename_parts = file_name.split("_")
        
        if len(filename_parts) not in self.config.expected_filename_parts:
            raise ValueError(f"Invalid filename format: {file_name}")
            
        schedule_type = filename_parts[0]
        if schedule_type not in ('л', 'с'):
            raise ValueError(f"Unknown schedule type: {schedule_type}")
            
        id_parts = tuple(filename_parts[1:3])
        if schedule_type == 'с':
            id_parts += (filename_parts[4],)
            
        schedule_data = self._read_csv_file(file_path)
        return id_parts, schedule_data

    def _read_csv_file(self, file_path: Path) -> list[Any]:
        """Read and process CSV file content."""
        schedule_data = []
        
        with file_path.open() as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)
            schedule_data.append(header)
            
            previous_row = None
            for row in csv_reader:
                processed_row = self._process_row(row, previous_row)
                schedule_data.append(processed_row)
                previous_row = processed_row.copy()
                
        return schedule_data[1:]

    def _process_row(self, row: list[str], previous_row: list[str] | None) -> list[Any]:
        """Process a single row of schedule data."""
        processed_row = row.copy()
        
        for i, cell in enumerate(processed_row):
            if not cell and previous_row:
                processed_row[i] = previous_row[i]
                
            if i == self.config.schedule_column_index and cell:
                processed_row[i] = self._expand_schedule_cell(cell)
            elif i == 0 and cell:
                processed_row[i] = self.week_days.DAYS_TO_NUM[cell.lower()]
                
        return processed_row

    def _expand_schedule_cell(self, cell: str) -> list[int]:
        """Expand schedule cell values into list of integers."""
        values = cell.replace(" ", "").split(",")
        result = []
        
        for value in values:
            if "-" in value:
                start, end = map(int, value.split("-"))
                result.extend(range(start, end + 1))
            else:
                result.append(int(value))
                
        return result

# Additional classes for Excel and iCal generation would follow...

def main() -> None:
    """Execute the main schedule processing functionality."""
    processor = ScheduleProcessor()
    excel_generator = ExcelGenerator()
    ical_generator = ICalGenerator()
    
    schedules = {"l": {}, "s": {}}
    
    for file_path in Path("./input").glob("*.csv"):
        try:
            id_parts, schedule_data = processor.process_schedule_file(file_path)
            schedule_type = "l" if file_path.stem.startswith("л") else "s"
            schedules[schedule_type][id_parts] = schedule_data
            rich.print(f"Processed file: {file_path}")
        except ValueError as e:
            rich.print(f"Error processing {file_path}: {e}")
            
    # Generate output files
    for s_id, s_schedule in schedules["s"].items():
        combined_schedule = processor.combine_schedules(
            s_schedule,
            schedules["l"][s_id[:2]]
        )
        excel_generator.generate(combined_schedule, s_id)
        ical_generator.generate(combined_schedule, s_id)

if __name__ == "__main__":
    main()
