"""Обработка таблица посещения бассейна, да простит меня Бог..."""

import csv
from pathlib import Path

from rich import print  # noqa: A004


FILE_PATH: Path = Path("./бассейн.csv")

class GroupInterval:
    def __init__(self, start: str, end: str | None) -> None:
        """Handle group intervals like '104' (104А, 104Б) or '205Б-206' (205Б, 206А, 206Б).

        Args:
            start (str): Starting group number
            end (str | None): Ending group number
        """
        self.start_g: str = start
        if len(start) == 3:
            self.start_g += "А"
        self.end_g: str | None = end
        if end and len(end) == 3:
            self.end_g += "Б"
        if not end and len(start) == 3:
            self.end_g = start + "Б"


    @classmethod
    def from_str(cls, s: str) -> 'GroupInterval':
        """Create GroupInterval from string like '104' or '205Б-206'.

        Args:
            s (str): Input string representing group interval

        Returns:
            GroupInterval: New instance

        """
        parts = s.split('-')
        start = parts[0]
        end = parts[1] if len(parts) > 1 else None
        return cls(start, end)

    @staticmethod
    def __increment(gr: str) -> str:
        if gr.endswith('А'):
            return gr[:-1] + 'Б'
        elif gr.endswith('Б'):
            return str(int(gr[:-1]) + 1) + 'А'
        else:
            return gr + 'А'

    def __iter__(self):
        current = self.start_g
        while True:
            yield current
            if self.end_g is None or current == self.end_g:
                break
            current = self.__increment(current)

    def __str__(self):
        if self.end_g:
            return f"{self.start_g}-{self.end_g}"
        return self.start_g


def time_correction(s: str) -> str:
    if not s:
        return None
    s = s.replace(".", ":")
    s = s.replace(",", "")
    if len(s) <= 2:
        s += ":"
    ss = s.split(":")
    for i in [0, 1]:
        if len(ss[i]) == 1:
            x = "0" + ss[i] if not i else ss[i] + "0"
            ss[i] = x
        elif not ss[i]:
            ss[i] = "00"
    s = ":".join(ss)
    return s


def week_correction(s: str) -> int:

    VARIATIONS = {
        0: ["mon", "monday", "пн", "понедельник"],
        1: ["tue", "tuesday", "вт", "вторник"],
        2: ["wed", "wednesday", "ср", "среда"],
        3: ["thu", "thursday", "чт", "четверг"],
        4: ["fri", "friday", "пт", "пятница"],
        5: ["sat", "saturday", "сб", "суббота"],
        6: ["sun", "sunday", "вс", "воскресенье"],
    }

    s = s.replace(",", "").replace(" ", "")
    s = s.lower()
    for i in range(7):
        if s in VARIATIONS[i]:
            s = i
            break
    return s


def parse_cell(cell: str) -> list[GroupInterval]:
    """Parse cell content into list of GroupIntervals.

    Args:
        cell (str): Cell content to parse

    Returns:
        list[GroupInterval]: List of parsed group intervals

    """
    cell = cell.replace(" ", "")
    out = []
    for i in cell.split(","):
        if i:
            #out.append(GroupInterval.from_str(i))
            for j in GroupInterval.from_str(i):
                out.append(j)
    return out

def get_sw_dict(path: Path = FILE_PATH) -> dict:
    out: dict = {}
    with path.open() as f:
        reader = csv.reader(f)
        # Skip header rows
        next(reader)
        next(reader)

        week_day = None
        time_slot = None

        for row in reader:
            if not row:
                continue

            week2gr: dict[int, GroupInterval] = {}

            # Handle week day
            if row[0]:
                week_day = week_correction(row[0].replace("\n", ","))

            # Handle time slot
            if row[1]:
                time_slot = time_correction(row[1].replace("\n", ","))
            else:
                continue

            # Process groups
            for j, cell in enumerate(row[2:], start=1):
                cell = cell.replace("\n", ",")
                if not cell:
                    continue
                week2gr[j] = parse_cell(cell)

            # Update output dictionary
            if week_day not in out:
                out[week_day] = {}
            out[week_day][time_slot] = week2gr

    return out


if __name__ == "__main__":
    print(get_sw_dict())
