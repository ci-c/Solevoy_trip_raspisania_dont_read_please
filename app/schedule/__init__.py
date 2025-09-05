"""
Модули для работы с расписаниями и API СЗГМУ.
"""

from .api_client import APIClient
from .semester_detector import SemesterDetector
from .group_search import GroupSearchService

__all__ = [
    "APIClient",
    "SemesterDetector", 
    "GroupSearchService"
]