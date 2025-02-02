"""Обработка таблица посещения бассейна, да простит меня Бог..."""

import csv
from pathlib import Path

FILE_PATH: Path = Path("./бассейн.csv")

def get_sw_dict(path: Path = FILE_PATH) -> dict:
    with path.open() as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i not in {0, 1}:
                print(*row)

get_sw_dict()
