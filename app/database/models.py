"""SQLAlchemy models for the database."""

from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Integer, Text, Boolean, Date, Time, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="users")
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )


class Faculty(Base):
    """Faculty model."""

    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    groups: Mapped[list["Group"]] = relationship(back_populates="faculty_obj")
    specialities: Mapped[list["Speciality"]] = relationship(back_populates="faculty")


class Group(Base):
    """Student group model."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    faculty: Mapped[str] = mapped_column(String(64))  # Legacy field
    speciality: Mapped[str] = mapped_column(String(128))  # Legacy field
    course: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    users: Mapped[list[User]] = relationship(back_populates="group")
    faculty_obj: Mapped[Optional[Faculty]] = relationship(back_populates="groups")
    faculty_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("faculties.id"), nullable=True
    )
    speciality_obj: Mapped[Optional["Speciality"]] = relationship(back_populates="groups")
    speciality_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("specialities.id"), nullable=True
    )


# ============================================================================
# СПРАВОЧНЫЕ ТАБЛИЦЫ
# ============================================================================

class AcademicYear(Base):
    """Учебный год."""
    
    __tablename__ = "academic_years"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(16), unique=True)  # "2024/2025"
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    semesters: Mapped[list["Semester"]] = relationship(back_populates="academic_year")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="academic_year")


class Semester(Base):
    """Семестр."""
    
    __tablename__ = "semesters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))  # "осенний", "весенний"
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"))
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="semesters")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="semester")


class Speciality(Base):
    """Специальность."""
    
    __tablename__ = "specialities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)  # "31.05.01"
    name: Mapped[str] = mapped_column(String(256))  # "лечебное дело"
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    faculty: Mapped["Faculty"] = relationship(back_populates="specialities")
    groups: Mapped[list["Group"]] = relationship(back_populates="speciality_obj")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="speciality")


class LessonType(Base):
    """Тип занятия."""
    
    __tablename__ = "lesson_types"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)  # "лекционного", "семинарского"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="lesson_type")


class Department(Base):
    """Кафедра."""
    
    __tablename__ = "departments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lecturers: Mapped[list["Lecturer"]] = relationship(back_populates="department")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="department")


class Lecturer(Base):
    """Преподаватель."""
    
    __tablename__ = "lecturers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    department: Mapped[Optional["Department"]] = relationship(back_populates="lecturers")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="lecturer")


class Classroom(Base):
    """Аудитория."""
    
    __tablename__ = "classrooms"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(32))  # "101", "А-201"
    building: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # "Главный корпус"
    address: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="classroom")


class Subject(Base):
    """Предмет."""
    
    __tablename__ = "subjects"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    short_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="subject")


# ============================================================================
# ОСНОВНЫЕ ТАБЛИЦЫ
# ============================================================================

class Schedule(Base):
    """Расписание (файл)."""
    
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True)  # ID из API
    file_name: Mapped[str] = mapped_column(String(256))
    form_type: Mapped[int] = mapped_column(Integer)  # 1=лекции, 2=практики, 3=смешанные
    status: Mapped[str] = mapped_column(String(32))  # "APPROVED", "DRAFT"
    is_uploaded_from_excel: Mapped[bool] = mapped_column(Boolean, default=False)
    update_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Связи с справочниками
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"))
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"))
    speciality_id: Mapped[int] = mapped_column(ForeignKey("specialities.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="schedules")
    semester: Mapped["Semester"] = relationship(back_populates="schedules")
    speciality: Mapped["Speciality"] = relationship(back_populates="schedules")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="schedule")


class Lesson(Base):
    """Занятие."""
    
    __tablename__ = "lessons"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True)  # ID из API
    
    # Основная информация
    day_name: Mapped[str] = mapped_column(String(8))  # "пн", "вт", "ср"
    week_number: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...
    pair_time: Mapped[str] = mapped_column(String(16))  # "9:00-10:30"
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    # Связи с справочниками
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    lesson_type_id: Mapped[int] = mapped_column(ForeignKey("lesson_types.id"))
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"), nullable=True)
    classroom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    
    # Дополнительная информация
    subgroup: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # "241б"
    study_group: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # "МПФ"
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    schedule: Mapped["Schedule"] = relationship(back_populates="lessons")
    subject: Mapped["Subject"] = relationship(back_populates="lessons")
    lesson_type: Mapped["LessonType"] = relationship(back_populates="lessons")
    lecturer: Mapped[Optional["Lecturer"]] = relationship(back_populates="lessons")
    classroom: Mapped[Optional["Classroom"]] = relationship(back_populates="lessons")
    department: Mapped[Optional["Department"]] = relationship(back_populates="lessons")


# ============================================================================
# СИСТЕМНЫЕ ТАБЛИЦЫ
# ============================================================================

class Settings(Base):
    """System settings model."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class APISyncLog(Base):
    """Лог синхронизации с API."""
    
    __tablename__ = "api_sync_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sync_type: Mapped[str] = mapped_column(String(32))  # "schedules", "faculties", "full"
    status: Mapped[str] = mapped_column(String(16))  # "success", "error", "partial"
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
