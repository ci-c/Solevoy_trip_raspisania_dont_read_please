from dataclasses import dataclass
from datetime import date

@dataclass
class PostLesson:
    """
    Модель для очищенных данных занятия, готовых к экспорту.
    """
    date: date
    lesson_number: int ## 0 - 4 или 0 - 1
    lesson_type: str
    subject_name: str
    lesson_seq: int
    metadata: dict[str, str]