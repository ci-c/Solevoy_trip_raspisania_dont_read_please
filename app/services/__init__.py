"""Асинхронные сервисы для работы с данными."""

from .academic_service import AcademicService
from .education_service import EducationService
from .invitation_service import InvitationService
from .schedule_service import ScheduleService
from .user_service import UserService

__all__ = [
    "AcademicService",
    "EducationService",
    "InvitationService",
    "ScheduleService",
    "UserService",
]
