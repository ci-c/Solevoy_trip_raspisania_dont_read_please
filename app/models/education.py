"""
Модели образовательных сущностей.
"""

from enum import Enum
from typing import Optional
from pydantic import Field

from .base import BaseModel


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
            if word.lower() not in ['и', 'в', 'на', 'с', 'по', 'для', 'от', 'к']:
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