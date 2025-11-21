"""Модели образовательных сущностей."""

from datetime import datetime
from enum import Enum

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
    full_name: str | None = Field(None, description="Полное название")
    faculty: str | None = Field(None, description="Факультет")
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
    current_semester: Semester | None = Field(None, description="Текущий семестр")
    academic_year: str | None = Field(None, description="Учебный год (2024/2025)")
    is_active: bool = Field(True, description="Активна ли группа")


class Subject(BaseModel):
    """Учебный предмет."""

    name: str = Field(..., description="Название предмета")
    code: str | None = Field(None, description="Код предмета")
    speciality_id: int = Field(..., description="ID специальности")
    course: int = Field(..., description="Курс")
    semester: Semester = Field(..., description="Семестр")
    credits: int | None = Field(None, description="Количество кредитов")
    hours_total: int | None = Field(None, description="Всего часов")
    hours_lectures: int | None = Field(None, description="Часов лекций")
    hours_seminars: int | None = Field(None, description="Часов семинаров")
    hours_practice: int | None = Field(None, description="Часов практики")


class Teacher(BaseModel):
    """Преподаватель."""

    full_name: str = Field(..., description="ФИО преподавателя")
    short_name: str | None = Field(None, description="Краткое имя")
    department: str | None = Field(None, description="Кафедра")
    position: str | None = Field(None, description="Должность")
    email: str | None = Field(None, description="Email")


class Room(BaseModel):
    """Аудитория."""

    number: str = Field(..., description="Номер аудитории")
    building: str | None = Field(None, description="Корпус")
    floor: int | None = Field(None, description="Этаж")
    capacity: int | None = Field(None, description="Вместимость")
    equipment: str | None = Field(None, description="Оборудование (JSON)")
    room_type: str | None = Field(None, description="Тип аудитории")


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

    id: int | None = Field(None, description="ID записи")
    group_id: int = Field(..., description="ID группы")
    date: datetime = Field(..., description="Дата занятия")
    week_number: int = Field(..., description="Номер недели")
    day_of_week: int = Field(..., description="День недели (1-7)")
    lesson_number: int = Field(..., description="Номер пары")
    subject_name: str = Field(..., description="Название предмета")
    lesson_type: LessonType = Field(..., description="Тип занятия")
    teacher_name: str | None = Field(None, description="Преподаватель")
    room_number: str | None = Field(None, description="Номер аудитории")
    building: str | None = Field(None, description="Корпус")
    start_time: str | None = Field(None, description="Время начала")
    end_time: str | None = Field(None, description="Время окончания")
    is_cancelled: bool = Field(False, description="Отменено ли занятие")
    notes: str | None = Field(None, description="Примечания")
    created_at: datetime | None = Field(None, description="Время создания")
    updated_at: datetime | None = Field(None, description="Время обновления")


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

    id: int | None = Field(None, description="ID оценки")
    student_id: int = Field(..., description="ID студента")
    subject_name: str = Field(..., description="Название предмета")
    grade_type: GradeType = Field(..., description="Тип оценки")
    grade_value: str = Field(..., description="Значение оценки")
    max_grade: str | None = Field(None, description="Максимальная оценка")
    date_recorded: datetime = Field(..., description="Дата выставления")
    semester: str | None = Field(None, description="Семестр")
    teacher_name: str | None = Field(None, description="Преподаватель")
    notes: str | None = Field(None, description="Примечания")
    created_at: datetime | None = Field(None, description="Время создания")
    updated_at: datetime | None = Field(None, description="Время обновления")


class AttendanceStatus(str, Enum):
    """Статус посещаемости."""

    PRESENT = "present"  # Присутствует
    ABSENT = "absent"  # Отсутствует
    LATE = "late"  # Опоздание
    EXCUSED = "excused"  # Уважительная причина


class AttendanceRecord(BaseModel):
    """Запись посещаемости."""

    id: int | None = Field(None, description="ID записи")
    student_id: int = Field(..., description="ID студента")
    schedule_id: int = Field(..., description="ID занятия в расписании")
    status: AttendanceStatus = Field(..., description="Статус посещаемости")
    notes: str | None = Field(None, description="Примечания")
    recorded_by: int | None = Field(None, description="Кто записал")
    created_at: datetime | None = Field(None, description="Время создания")
    updated_at: datetime | None = Field(None, description="Время обновления")
