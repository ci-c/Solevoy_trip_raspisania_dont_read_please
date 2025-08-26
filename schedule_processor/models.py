"""Data models for schedule processing."""

from dataclasses import dataclass
from datetime import date, time
from typing import Optional, List, Any


@dataclass
class Lesson:
    """
    A data class to represent a single lesson from the schedule API.
    
    All fields are included to match the exact API response structure,
    which embeds top-level schedule data within each lesson object.
    """
    academicYear: str
    auditoryNumber: Optional[str]
    courseNumber: int
    dayName: str
    departmentName: str
    errorList: List[Any]
    fileName: str
    groupStream: str
    groupTypeName: str
    id: int
    lectorName: Optional[str]
    lessonType: str
    locationAddress: Optional[str]
    pairTime: str
    scheduleId: int
    semester: str
    speciality: str
    studyGroup: str
    subgroup: Optional[str]
    subjectName: str
    weekNumber: int
    
    # The API can sometimes return 'lessonType' and 'lessonTypeName'
    # as the same value, this helps handle that.
    def __post_init__(self):
        # The API is not consistent with 'lessonTypeName' field,
        # so we ensure it's set if 'lessonType' exists.
        if self.lessonType and not hasattr(self, 'lessonTypeName'):
            self.lessonTypeName = self.lessonType


@dataclass
class ProcessedLesson:
    """Processed lesson data for export."""
    week: int
    date: date
    time_slot: List[time]
    lesson_numbers: str
    type_: str
    subject: str
    location: Optional[str] = None
    lecturer: Optional[str] = None