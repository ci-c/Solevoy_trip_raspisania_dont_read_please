"""Модели данных для СЗГМУ Schedule Bot."""

from .academic import Attendance, Grade, Homework
from .base import BaseModel
from .education import Room, Speciality, StudyGroup, Subject, Teacher
from .invitation import Invitation, InvitationUsage
from .schedule import Lesson, Schedule
from .system import ActivityLog, SearchCache, Setting
from .user import StudentProfile, Subscription, User

__all__ = [
    "ActivityLog",
    "Attendance",
    "BaseModel",
    "Grade",
    "Homework",
    "Invitation",
    "InvitationUsage",
    "Lesson",
    "Room",
    "Schedule",
    "SearchCache",
    "Setting",
    "Speciality",
    "StudentProfile",
    "StudyGroup",
    "Subject",
    "Subscription",
    "Teacher",
    "User",
]
