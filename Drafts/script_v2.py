"""Script for processing CSV/XLSX files with schedule data (OOP version)."""

from abc import ABC, abstractmethod
import csv
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any, Protocol
import ics
import openpyxl
import rich

class ScheduleConfig:
    """Configuration container for schedule processing."""
    ADD_BREAKS: bool = False
    ADD_MARK: bool = True
    FIRST_DATE = datetime.date(2025, 2, 3)
    EXPECTED_FILENAME_PARTS: tuple[int] = (4, 5)
    SCHEDULE_COLUMN_INDEX: int = 3
    WIDTH_COLUMNS: list[int] = [8, 12, 4, 4, 16, 4, 20]
    
    RINGS = {
        "s": {
            "9:00": [datetime.time(9, 0), datetime.time(10, 30), datetime.time(10, 45), datetime.time(12, 15), [1,2]],
            "13:10": [datetime.time(13, 10), datetime.time(14, 40), datetime.time(14, 55), datetime.time(16, 25], [3,4]],
        },
        # ... остальные конфигурации
    }

class FileProcessor(ABC):
    """Base class for file processors."""
    def __init__(self, config: ScheduleConfig):
        self.config = config
    
    @abstractmethod
    def process(self, file_path: Path) -> list:
        """Process file and return schedule data."""
        pass

class CSVProcessor(FileProcessor):
    """CSV file processor."""
    def process(self, file_path: Path) -> list:
        schedule_data = []
        with file_path.open() as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            # ... исходная логика обработки CSV
        return schedule_data

class XLSXProcessor(FileProcessor):
    """XLSX file processor."""
    def process(self, file_path: Path) -> list:
        schedule_data = []
        workbook = openpyxl.load_workbook(file_path)
        # ... исходная логика обработки XLSX
        return schedule_data

class ScheduleData:
    """Container for processed schedule data."""
    def __init__(self):
        self.lecture: dict = {}
        self.seminar: dict = {}

    def add_data(self, data_type: str, identifier: tuple, data: list):
        if data_type == "л":
            self.lecture[identifier] = data
        elif data_type == "с":
            self.seminar[identifier] = data

class ScheduleGenerator:
    """Main schedule generator."""
    def __init__(self, config: ScheduleConfig):
        self.config = config
        self.file_processors = {
            ".csv": CSVProcessor(config),
            ".xlsx": XLSXProcessor(config)
        }
        self.schedule_data = ScheduleData()

    def process_files(self, input_dir: Path = Path("./input")):
        for ext, processor in self.file_processors.items():
            for file_path in input_dir.glob(f"*{ext}"):
                self._process_single_file(file_path, processor)

    def _process_single_file(self, file_path: Path, processor: FileProcessor):
        filename_parts = file_path.stem.lower().split("_")
        data_type = filename_parts[0]
        identifier = self._create_identifier(filename_parts, data_type)
        
        schedule_data = processor.process(file_path)
        self.schedule_data.add_data(data_type, identifier, schedule_data)
        rich.print(f"Processed file: {file_path}")

    def _create_identifier(self, parts: list, data_type: str) -> tuple:
        # ... логика создания идентификатора

class ExcelExporter:
    """Excel file exporter."""
    def __init__(self, config: ScheduleConfig):
        self.config = config
    
    def export(self, schedule: list, identifier: str):
        workbook = openpyxl.Workbook()
        # ... исходная логика генерации Excel
        workbook.save(f"output/{identifier}.xlsx")

class ICalExporter:
    """iCalendar file exporter."""
    def __init__(self, config: ScheduleConfig):
        self.config = config
    
    def export(self, schedule: list, identifier: str):
        calendar = ics.Calendar()
        # ... исходная логика генерации ICS
        Path(f"output/{identifier}.ics").write_bytes(str(calendar.serialize()).encode())

class ExportManager:
    """Manages export to different formats."""
    def __init__(self, config: ScheduleConfig):
        self.config = config
        self.exporters = {
            "excel": ExcelExporter(config),
            "ical": ICalExporter(config)
        }

    def export_all(self, schedule: list, identifier: str):
        for exporter in self.exporters.values():
            exporter.export(schedule, identifier)

def main() -> None:
    """Main execution flow."""
    config = ScheduleConfig()
    generator = ScheduleGenerator(config)
    exporter = ExportManager(config)

    generator.process_files()
    
    for s_id, s_schedule in generator.schedule_data.seminar.items():
        combined = self._combine_schedules(s_schedule, generator.schedule_data.lecture)
        exporter.export_all(combined, s_id)


if __name__ == "__main__":
    main()
