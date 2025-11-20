from dataclasses import dataclass
from typing import Any


@dataclass
class Lesson:
    """
    A data class to represent a single lesson from the schedule API.

    All fields are included to match the exact API response structure,
    which embeds top-level schedule data within each lesson object.
    """

    academicYear: str
    auditoryNumber: str | None
    courseNumber: int
    dayName: str
    departmentName: str
    errorList: list[Any]
    fileName: str
    groupStream: str
    groupTypeName: str
    id: int
    lectorName: str | None
    lessonType: str
    locationAddress: str | None
    pairTime: str
    scheduleId: int
    semester: str
    speciality: str
    studyGroup: str
    subgroup: str | None
    subjectName: str
    weekNumber: int

    # The API can sometimes return 'lessonType' and 'lessonTypeName'
    # as the same value, this helps handle that.
    def __post_init__(self):
        # The API is not consistent with 'lessonTypeName' field,
        # so we ensure it's set if 'lessonType' exists.
        if self.lessonType and not hasattr(self, "lessonTypeName"):
            self.lessonTypeName = self.lessonType
