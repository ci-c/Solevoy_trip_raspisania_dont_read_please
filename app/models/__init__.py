"""
Модели данных для СЗГМУ Schedule Bot.
"""

from .base import BaseModel
from .user import User, StudentProfile, Subscription
from .invitation import Invitation, InvitationUsage
from .education import Speciality, StudyGroup, Subject, Teacher, Room
from .schedule import Schedule, Lesson
from .academic import Grade, Attendance, Homework
from .system import Setting, ActivityLog, SearchCache

__all__ = [
    "BaseModel",
    "User", "StudentProfile", "Subscription",
    "Invitation", "InvitationUsage", 
    "Speciality", "StudyGroup", "Subject", "Teacher", "Room",
    "Schedule", "Lesson",
    "Grade", "Attendance", "Homework",
    "Setting", "ActivityLog", "SearchCache"
]