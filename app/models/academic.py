"""Academic activity models for SZGMU."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from pydantic import Field

from .base import BaseModel


class Faculty(BaseModel):
    """Faculty model."""

    faculty_id: int = Field(..., description="Faculty ID")
    name: str = Field(..., description="Faculty name")
    short_name: str = Field("", description="Faculty short name")
    code: str = Field("", description="Faculty code")


class Speciality(BaseModel):
    """Speciality model."""

    code: str = Field(
        ...,
        description="Speciality code",
        json_schema_extra={"pattern": r"^\d{2}\.\d{2}\.\d{2}$"},
    )
    name: str = Field(..., description="Speciality name")
    full_name: str = Field(..., description="Full speciality name with code")
    faculty_id: int = Field(..., description="ID of associated faculty")
    degree_type: str = Field("speciality", description="Type of degree")


class GradeType(str, Enum):
    """Types of grades."""

    CURRENT = "current"
    MIDTERM = "midterm"
    FINAL = "final"
    EXAM = "exam"


class HomeworkStatus(str, Enum):
    """Статусы домашних заданий."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class Grade(BaseModel):
    """Оценка студента."""

    student_id: int = Field(..., description="ID студента")
    subject_id: int = Field(..., description="ID предмета")
    grade: int = Field(..., description="Оценка (2-5)", ge=2, le=5)
    grade_type: GradeType = Field(GradeType.CURRENT, description="Тип оценки")
    control_point: Optional[str] = Field(None, description="Контрольная точка")
    date_received: date = Field(
        default_factory=date.today, description="Дата получения"
    )
    teacher_id: Optional[int] = Field(None, description="ID преподавателя")
    notes: Optional[str] = Field(None, description="Примечания")


class Attendance(BaseModel):
    """Посещаемость студента."""

    student_id: int = Field(..., description="ID студента")
    lesson_id: int = Field(..., description="ID занятия")
    is_present: bool = Field(..., description="Присутствовал ли студент")
    is_excused: bool = Field(False, description="Уважительная причина")
    excuse_reason: Optional[str] = Field(None, description="Причина отсутствия")
    excuse_document: Optional[str] = Field(
        None, description="Документ об уважительной причине"
    )
    date_marked: date = Field(default_factory=date.today, description="Дата отметки")


class Homework(BaseModel):
    """Домашнее задание."""

    student_id: int = Field(..., description="ID студента")
    subject_id: int = Field(..., description="ID предмета")
    title: str = Field(..., description="Название задания")
    description: Optional[str] = Field(None, description="Описание")
    due_date: Optional[date] = Field(None, description="Срок сдачи")
    status: HomeworkStatus = Field(HomeworkStatus.PENDING, description="Статус")
    priority: int = Field(3, description="Приоритет (1-5)", ge=1, le=5)
    completed_at: Optional[datetime] = Field(None, description="Время выполнения")
