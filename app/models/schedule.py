"""Модели расписаний и занятий."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base import BaseModel
from .education import Semester


class ScheduleType(str, Enum):
    """Типы расписаний."""

    LECTURES = "lectures"
    SEMINARS = "seminars"
    PRACTICE = "practice"
    MIXED = "mixed"


class LessonType(str, Enum):
    """Типы занятий."""

    LECTURE = "lecture"
    SEMINAR = "seminar"
    PRACTICE = "practice"
    EXAM = "exam"
    CONSULTATION = "consultation"


class Schedule(BaseModel):
    """Расписание (источник данных)."""

    source_id: str | None = Field(None, description="ID из внешнего API")
    file_name: str | None = Field(None, description="Имя файла")
    schedule_type: ScheduleType = Field(..., description="Тип расписания")
    speciality_id: int | None = Field(None, description="ID специальности")
    course: int | None = Field(None, description="Курс")
    semester: Semester | None = Field(None, description="Семестр")
    academic_year: str | None = Field(None, description="Учебный год")
    raw_data: str | None = Field(None, description="Исходные данные в JSON")
    parsed_at: datetime | None = Field(None, description="Время парсинга")
    is_active: bool = Field(True, description="Активно ли расписание")


class Lesson(BaseModel):
    """Занятие (парсированное из расписания)."""

    schedule_id: int = Field(..., description="ID расписания")
    subject_id: int | None = Field(None, description="ID предмета")
    teacher_id: int | None = Field(None, description="ID преподавателя")
    room_id: int | None = Field(None, description="ID аудитории")
    group_id: int | None = Field(None, description="ID группы")

    lesson_type: LessonType = Field(..., description="Тип занятия")
    subgroup: str | None = Field(None, description="Подгруппа")

    week_number: int = Field(..., description="Номер недели")
    day_of_week: int = Field(..., description="День недели (1-7)")
    day_name: str | None = Field(None, description="Название дня")
    time_start: str = Field(..., description="Время начала")
    time_end: str = Field(..., description="Время окончания")

    duration_minutes: int | None = Field(None, description="Длительность в минутах")
    is_online: bool = Field(False, description="Онлайн занятие")
    notes: str | None = Field(None, description="Примечания")

    @property
    def time_range(self) -> str:
        """Временной диапазон занятия."""
        return f"{self.time_start}-{self.time_end}"

    def get_display_info(self) -> str:
        """Получить информацию для отображения."""
        type_emoji = {
            LessonType.LECTURE: "📚",
            LessonType.SEMINAR: "📝",
            LessonType.PRACTICE: "🔬",
            LessonType.EXAM: "📊",
            LessonType.CONSULTATION: "💬",
        }.get(self.lesson_type, "📋")

        subgroup_info = f" | Подгр. {self.subgroup}" if self.subgroup else ""
        return f"{type_emoji} {self.lesson_type}{subgroup_info}"
