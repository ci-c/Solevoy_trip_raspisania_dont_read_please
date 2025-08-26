"""File processing for CSV and XLSX schedule files (v1 compatibility)."""

import csv
from pathlib import Path
import openpyxl

from .config import WEEK_DAYS, SCHEDULE_COLUMN_INDEX


def expand_interval(interval: str) -> list[int]:
    """Expand a range interval into a list of integers.

    Args:
        interval (str): The interval string in format "start-end"

    Returns:
        list[int]: List of integers in the interval
    """
    start, end = map(int, interval.split("-"))
    return list(range(start, end + 1))


def process_schedule_cell(cell: str) -> list[int]:
    """Process a schedule cell and expand any intervals.

    Args:
        cell (str): The schedule cell content

    Returns:
        list: Processed schedule data with expanded intervals
    """
    values = cell.replace(" ", "").split(",")
    result: list[int] = []

    for value in values:
        if "-" in value:
            result.extend(expand_interval(value))
        else:
            result.append(int(value) if value.isdigit() else value)

    return result


def process_csv_file(file_path: Path) -> list:
    """Process a single CSV file and return the schedule data.

    Args:
        file_path (Path): The path to the CSV file to process.

    Returns:
        list: The processed schedule data, excluding the header row.
    """
    schedule_data: list[list[str | int | list[int]]] = []

    with file_path.open() as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        previous_row = next(csv_reader)  # Read header
        schedule_data.append(previous_row)

        for current_row in csv_reader:
            for index, cell in enumerate(current_row):
                if not cell and previous_row:
                    current_row[index] = previous_row[index]
                if index == SCHEDULE_COLUMN_INDEX and cell:
                    current_row[index] = process_schedule_cell(cell)
                elif index == 0 and cell:
                    current_row[index] = WEEK_DAYS[cell.lower()]

            previous_row = current_row.copy()
            schedule_data.append(current_row)

    return schedule_data[1:]


def process_xlsx_file(file_path: Path) -> list:
    """Process a single XLSX file and return the schedule data.

    Args:
        file_path (Path): Path to XLSX file to process

    Returns:
        list: Processed schedule data, excluding header row
    """
    schedule_data: list[list[str | int | list[int]]] = []
    workbook = openpyxl.load_workbook(file_path)
    worksheet = workbook.active

    previous_row = []
    SCHEDULE_COLUMN_INDEX = 3  # Local constant for this function

    # Skip header row if needed
    start_row = 2 if worksheet[1][0].value == "пн" else 1

    for row in worksheet.iter_rows(min_row=start_row, values_only=True):
        current_row = list(row)

        # Skip empty rows
        if not any(current_row):
            continue

        # Convert day name to number
        if current_row[0]:
            current_row[0] = WEEK_DAYS[current_row[0].lower().strip()]

        # Process schedule cells
        for index, cell in enumerate(current_row):
            if not cell and previous_row:
                current_row[index] = previous_row[index]

            # Process schedule intervals
            if index == SCHEDULE_COLUMN_INDEX and cell:
                current_row[index] = process_schedule_cell(str(cell))

        # Clean numeric values
        if isinstance(current_row[2], (int, float)):
            current_row[2] = int(current_row[2])

        previous_row = current_row.copy()
        schedule_data.append(current_row)

    return schedule_data


