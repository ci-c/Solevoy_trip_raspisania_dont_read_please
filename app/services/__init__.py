"""
Асинхронные сервисы для работы с данными.
"""

from .user_service import UserService
from .invitation_service import InvitationService
from .education_service import EducationService
from .schedule_service import ScheduleService
from .academic_service import AcademicService

__all__ = [
    "UserService",
    "InvitationService", 
    "EducationService",
    "ScheduleService",
    "AcademicService"
]