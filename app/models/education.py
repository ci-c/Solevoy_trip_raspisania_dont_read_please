"""
Модели образовательных сущностей.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import Field

from app.models.base import BaseModel


class DegreeType(str, Enum):
    """Типы образовательных программ."""

    BACHELOR = "bachelor"
    SPECIALITY = "speciality"
    MASTER = "master"


class Semester(str, Enum):
    """Семестры."""

    AUTUMN = "осенний"
    SPRING = "весенний"


class Speciality(BaseModel):
    """Направление подготовки (специальность)."""

    code: str = Field(..., description="Код специальности (31.05.01)")
    name: str = Field(..., description="Название специальности")
    full_name: Optional[str] = Field(None, description="Полное название")
    faculty: Optional[str] = Field(None, description="Факультет")
    degree_type: DegreeType = Field(DegreeType.SPECIALITY, description="Тип программы")
    study_years: int = Field(6, description="Количество лет обучения")

    @property
    def abbreviation(self) -> str:
        """Создать аббревиатуру для длинного названия."""
        if len(self.name) <= 30:
            return self.name

        # Создаем аббревиатуру из первых букв слов
        words = self.name.split()
        if len(words) <= 2:
            return self.name[:30]

        # Берем первое слово полностью + аббревиатуры остальных
        abbrev = words[0]
        for word in words[1:]:
            if word.lower() not in ["и", "в", "на", "с", "по", "для", "от", "к"]:
                abbrev += f" {word[0].upper()}."

        return abbrev[:40]  # Ограничиваем до 40 символов


class StudyGroup(BaseModel):
    """Группа студентов."""

    number: str = Field(..., description="Номер группы (103а)")
    course: int = Field(..., description="Курс")
    stream: str = Field(..., description="Поток (а, б, в)")
    speciality_id: int = Field(..., description="ID специальности")
    current_semester: Optional[Semester] = Field(None, description="Текущий семестр")
    academic_year: Optional[str] = Field(None, description="Учебный год (2024/2025)")
    is_active: bool = Field(True, description="Активна ли группа")


class Subject(BaseModel):
    """Учебный предмет."""

    name: str = Field(..., description="Название предмета")
    code: Optional[str] = Field(None, description="Код предмета")
    speciality_id: int = Field(..., description="ID специальности")
    course: int = Field(..., description="Курс")
    semester: Semester = Field(..., description="Семестр")
    credits: Optional[int] = Field(None, description="Количество кредитов")
    hours_total: Optional[int] = Field(None, description="Всего часов")
    hours_lectures: Optional[int] = Field(None, description="Часов лекций")
    hours_seminars: Optional[int] = Field(None, description="Часов семинаров")
    hours_practice: Optional[int] = Field(None, description="Часов практики")


class Teacher(BaseModel):
    """Преподаватель."""

    full_name: str = Field(..., description="ФИО преподавателя")
    short_name: Optional[str] = Field(None, description="Краткое имя")
    department: Optional[str] = Field(None, description="Кафедра")
    position: Optional[str] = Field(None, description="Должность")
    email: Optional[str] = Field(None, description="Email")


class Room(BaseModel):
    """Аудитория."""

    number: str = Field(..., description="Номер аудитории")
    building: Optional[str] = Field(None, description="Корпус")
    floor: Optional[int] = Field(None, description="Этаж")
    capacity: Optional[int] = Field(None, description="Вместимость")
    equipment: Optional[str] = Field(None, description="Оборудование (JSON)")
    room_type: Optional[str] = Field(None, description="Тип аудитории")


class LessonType(str, Enum):
    """Типы занятий."""

    LECTURE = "лекция"
    SEMINAR = "семинар"
    PRACTICE = "практика"
    LAB = "лабораторная"
    EXAM = "экзамен"
    OFFSET = "зачет"


class Schedule(BaseModel):
    """Расписание занятий."""

    id: Optional[int] = Field(None, description="ID записи")
    group_id: int = Field(..., description="ID группы")
    date: datetime = Field(..., description="Дата занятия")
    week_number: int = Field(..., description="Номер недели")
    day_of_week: int = Field(..., description="День недели (1-7)")
    lesson_number: int = Field(..., description="Номер пары")
    subject_name: str = Field(..., description="Название предмета")
    lesson_type: LessonType = Field(..., description="Тип занятия")
    teacher_name: Optional[str] = Field(None, description="Преподаватель")
    room_number: Optional[str] = Field(None, description="Номер аудитории")
    building: Optional[str] = Field(None, description="Корпус")
    start_time: Optional[str] = Field(None, description="Время начала")
    end_time: Optional[str] = Field(None, description="Время окончания")
    is_cancelled: bool = Field(False, description="Отменено ли занятие")
    notes: Optional[str] = Field(None, description="Примечания")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class GradeType(str, Enum):
    """Типы оценок."""

    TSB = "ТСБ"  # Тематическое собеседование
    OSB = "ОСБ"  # Оценочное собеседование
    KNL = "КНЛ"  # Контрольная лекция
    KNS = "КНС"  # Контрольная семинар
    EXAM = "экзамен"
    OFFSET = "зачет"
    HOMEWORK = "домашнее задание"
    ESSAY = "реферат"


class Grade(BaseModel):
    """Оценка студента."""

    id: Optional[int] = Field(None, description="ID оценки")
    student_id: int = Field(..., description="ID студента")
    subject_name: str = Field(..., description="Название предмета")
    grade_type: GradeType = Field(..., description="Тип оценки")
    grade_value: str = Field(..., description="Значение оценки")
    max_grade: Optional[str] = Field(None, description="Максимальная оценка")
    date_recorded: datetime = Field(..., description="Дата выставления")
    semester: Optional[str] = Field(None, description="Семестр")
    teacher_name: Optional[str] = Field(None, description="Преподаватель")
    notes: Optional[str] = Field(None, description="Примечания")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class AttendanceStatus(str, Enum):
    """Статус посещаемости."""

    PRESENT = "present"  # Присутствует
    ABSENT = "absent"  # Отсутствует
    LATE = "late"  # Опоздание
    EXCUSED = "excused"  # Уважительная причина


class AttendanceRecord(BaseModel):
    """Запись посещаемости."""

    id: Optional[int] = Field(None, description="ID записи")
    student_id: int = Field(..., description="ID студента")
    schedule_id: int = Field(..., description="ID занятия в расписании")
    status: AttendanceStatus = Field(..., description="Статус посещаемости")
    notes: Optional[str] = Field(None, description="Примечания")
    recorded_by: Optional[int] = Field(None, description="Кто записал")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")
