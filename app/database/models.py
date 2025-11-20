"""SQLAlchemy models for the database."""

from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, synonym


class Base(DeclarativeBase):
    """Base class for all models."""


class ScheduleImportStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ExportStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ExportFormat(str, Enum):
    EXCEL = "excel"
    ICS = "ics"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    access_level: Mapped[str] = mapped_column(String(16), default="guest")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="users")
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"), nullable=True,
    )
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Faculty(Base):
    """Faculty model."""

    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    short_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    users: Mapped[list[User]] = relationship(back_populates="group")
    faculty_obj: Mapped[Faculty | None] = relationship(back_populates="groups")
    faculty_id: Mapped[int | None] = mapped_column(
        ForeignKey("faculties.id"), nullable=True,
    )
    speciality_obj: Mapped[Optional["Speciality"]] = relationship(
        back_populates="groups",
    )
    speciality_id: Mapped[int | None] = mapped_column(
        ForeignKey("specialities.id"), nullable=True,
    )
    profiles: Mapped[list["UserProfile"]] = relationship(back_populates="group")
    schedule_lessons: Mapped[list["ScheduleLesson"]] = relationship(
        back_populates="group",
    )


class UserProfile(Base):
    """Per-user runtime preferences and notification settings."""

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"), nullable=True,
    )
    preferred_export_format: Mapped[str] = mapped_column(String(8), default="excel")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    student_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship(back_populates="profile")
    group: Mapped[Optional["Group"]] = relationship(back_populates="profiles")


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
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    name: Mapped[str] = mapped_column(
        String(64), unique=True,
    )  # "лекционного", "семинарского"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    lessons: Mapped[list["ScheduleLesson"]] = relationship(back_populates="lesson_type")


class Department(Base):
    """Кафедра."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    short_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    lecturers: Mapped[list["Lecturer"]] = relationship(back_populates="department")
    lessons: Mapped[list["ScheduleLesson"]] = relationship(back_populates="department")


class Lecturer(Base):
    """Преподаватель."""

    __tablename__ = "lecturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(128))
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True,
    )
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        back_populates="lecturers",
    )
    lessons: Mapped[list["ScheduleLesson"]] = relationship(back_populates="lecturer")

    # Backwards compatibility
    name = synonym("full_name")


class Room(Base):
    """Аудитория / помещение."""

    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    campus: Mapped[str | None] = mapped_column(String(64), nullable=True)
    building: Mapped[str | None] = mapped_column(String(64), nullable=True)
    room_number: Mapped[str] = mapped_column("number", String(32))
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Backwards compatibility aliases
    number = synonym("room_number")
    description = synonym("address")

    # Relationships
    lessons: Mapped[list["ScheduleLesson"]] = relationship(back_populates="classroom")


class Subject(Base):
    """Предмет."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    lessons: Mapped[list["ScheduleLesson"]] = relationship(back_populates="subject")


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
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Связи с справочниками
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"))
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"))
    speciality_id: Mapped[int] = mapped_column(ForeignKey("specialities.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="schedules")
    semester: Mapped["Semester"] = relationship(back_populates="schedules")
    speciality: Mapped["Speciality"] = relationship(back_populates="schedules")
    lessons: Mapped[list["ScheduleLesson"]] = relationship(back_populates="schedule")


class ScheduleLesson(Base):
    """Нормализованная запись занятия."""

    __tablename__ = "lessons"
    __table_args__ = (
        Index(
            "ux_schedule_lessons_group_date_start",
            "group_id",
            "date",
            "start_time",
            "subject_id",
            "classroom_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True)  # ID из API

    # Основная информация
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"), nullable=True,
    )
    day_name: Mapped[str | None] = mapped_column(
        String(8), nullable=True,
    )  # "пн", "вт"
    week_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )  # 1, 2, 3...
    pair_time: Mapped[str | None] = mapped_column(
        String(16), nullable=True,
    )  # "9:00-10:30"
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Связи с справочниками
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    lesson_type_id: Mapped[int] = mapped_column(ForeignKey("lesson_types.id"))
    lecturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("lecturers.id"), nullable=True,
    )
    classroom_id: Mapped[int | None] = mapped_column(
        ForeignKey("classrooms.id"), nullable=True,
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True,
    )

    # Дополнительная информация
    subgroup: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "241б"
    study_group: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
    )  # "МПФ"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    group: Mapped[Optional["Group"]] = relationship(back_populates="schedule_lessons")
    schedule: Mapped["Schedule"] = relationship(back_populates="lessons")
    subject: Mapped["Subject"] = relationship(back_populates="lessons")
    lesson_type: Mapped["LessonType"] = relationship(back_populates="lessons")
    lecturer: Mapped[Optional["Lecturer"]] = relationship(back_populates="lessons")
    classroom: Mapped[Optional["Room"]] = relationship(back_populates="lessons")
    department: Mapped[Optional["Department"]] = relationship(back_populates="lessons")

    # Spec-friendly aliases
    room_id = synonym("classroom_id")

    @property
    def room(self) -> Optional["Room"]:
        return self.classroom

    @room.setter
    def room(self, value: Optional["Room"]) -> None:
        self.classroom = value


# ============================================================================
# СИСТЕМНЫЕ ТАБЛИЦЫ
# ============================================================================


class ScheduleImportJob(Base):
    """История загрузок расписаний из внешних источников."""

    __tablename__ = "schedule_import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(
        String(16), default=ScheduleImportStatus.PENDING.value,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExportRequest(Base):
    """Запросы на экспорт расписания."""

    __tablename__ = "export_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    from_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    to_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    format: Mapped[str] = mapped_column(String(8), default=ExportFormat.EXCEL.value)
    status: Mapped[str] = mapped_column(String(16), default=ExportStatus.QUEUED.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
    group: Mapped["Group"] = relationship()


class NotificationJob(Base):
    """Планирование и отправка уведомлений о занятиях."""

    __tablename__ = "notification_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(16), default=NotificationStatus.PENDING.value,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship()
    lesson: Mapped["ScheduleLesson"] = relationship()


class Settings(Base):
    """System settings model."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )


class APISyncLog(Base):
    """Лог синхронизации с API."""

    __tablename__ = "api_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    sync_type: Mapped[str] = mapped_column(
        String(32),
    )  # "schedules", "faculties", "full"
    status: Mapped[str] = mapped_column(String(16))  # "success", "error", "partial"
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Backwards compatibility aliases (to be removed after service migration)
# ---------------------------------------------------------------------------

Lesson = ScheduleLesson
Classroom = Room
