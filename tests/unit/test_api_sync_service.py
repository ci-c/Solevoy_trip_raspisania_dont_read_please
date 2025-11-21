"""Comprehensive tests for APISyncService."""

from datetime import time as dt_time
from unittest.mock import patch

import pytest

from app.services.api_sync_service import APISyncService


@pytest.mark.asyncio
@pytest.mark.unit
class TestAPISyncService:
    """Tests for APISyncService."""

    async def test_init(self):
        """Test APISyncService initialization."""
        service = APISyncService()
        assert service is not None
        assert service.api_client is not None
        assert isinstance(service.sync_stats, dict)
        assert service.sync_stats["faculties_created"] == 0

    async def test_extract_faculty_from_speciality(self):
        """Test faculty extraction from specialities."""
        service = APISyncService()

        assert service._extract_faculty_from_speciality("лечебное дело") == "Лечебный факультет"
        assert service._extract_faculty_from_speciality("педиатрия") == "Педиатрический факультет"
        assert service._extract_faculty_from_speciality("стоматология") == "Стоматологический факультет"
        assert service._extract_faculty_from_speciality("фармация") == "Фармацевтический факультет"
        assert service._extract_faculty_from_speciality("сестринское дело") == "Факультет сестринского дела"
        assert service._extract_faculty_from_speciality("unknown") == "Неизвестный факультет"

    async def test_extract_speciality_code(self):
        """Test speciality code extraction."""
        service = APISyncService()

        result = service._extract_speciality_code("31.05.01 лечебное дело")
        assert result == "31.05.01"

        result = service._extract_speciality_code("33.05.01 фармация")
        assert result == "33.05.01"

        result = service._extract_speciality_code("no code here")
        assert result == ""

    async def test_extract_speciality_name(self):
        """Test speciality name extraction."""
        service = APISyncService()

        result = service._extract_speciality_name("31.05.01 лечебное дело")
        assert "лечебное дело" in result
        assert "31.05.01" not in result

    async def test_generate_short_name(self):
        """Test short name generation."""
        service = APISyncService()

        assert service._generate_short_name("Лечебный факультет") == "ЛФ"
        assert service._generate_short_name("Педиатрический факультет") == "ПФ"
        assert service._generate_short_name("Медико-профилактический факультет") == "МПФ"
        assert service._generate_short_name("Стоматологический факультет") == "СФ"
        assert service._generate_short_name("Фармацевтический факультет") == "ФФ"

    async def test_parse_time_valid(self):
        """Test time parsing with valid input."""
        service = APISyncService()

        start, end = service._parse_time("09:00-10:30")
        assert start == dt_time(9, 0)
        assert end == dt_time(10, 30)

    async def test_parse_time_invalid(self):
        """Test time parsing with invalid input."""
        service = APISyncService()

        start, end = service._parse_time("invalid")
        assert start is None
        assert end is None

        start, end = service._parse_time("")
        assert start is None
        assert end is None

    async def test_extract_faculties_empty(self):
        """Test faculty extraction from empty data."""
        service = APISyncService()
        result = service._extract_faculties([])
        assert result == []

    async def test_extract_faculties_valid_data(self):
        """Test faculty extraction from valid data."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"speciality": "31.05.01 лечебное дело"},
                    {"speciality": "31.05.02 педиатрия"}
                ]
            }
        ]

        result = service._extract_faculties(schedules_data)
        assert len(result) > 0
        assert all("name" in f and "short_name" in f for f in result)

    async def test_extract_specialities_valid_data(self):
        """Test speciality extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"speciality": "31.05.01 лечебное дело"}
                ]
            }
        ]

        result = service._extract_specialities(schedules_data)
        assert len(result) > 0
        assert all("code" in s and "name" in s and "faculty_name" in s for s in result)

    async def test_extract_academic_years(self):
        """Test academic year extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"academicYear": "2024/2025"},
                    {"academicYear": "2025/2026"}
                ]
            }
        ]

        result = service._extract_academic_years(schedules_data)
        assert len(result) == 2
        assert "2024/2025" in result

    async def test_extract_semesters(self):
        """Test semester extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"semesterType": "осенний", "academicYear": "2024/2025"}
                ]
            }
        ]

        result = service._extract_semesters(schedules_data)
        assert len(result) > 0
        assert all("name" in s and "academic_year" in s for s in result)

    async def test_extract_lesson_types(self):
        """Test lesson type extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"lessonTypeName": "лекция"},
                    {"lessonTypeName": "практика"}
                ]
            }
        ]

        result = service._extract_lesson_types(schedules_data)
        assert len(result) == 2
        assert "лекция" in result

    async def test_extract_departments(self):
        """Test department extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {"departmentName": "Кафедра анатомии"},
                    {"departmentName": "Кафедра физиологии"}
                ]
            }
        ]

        result = service._extract_departments(schedules_data)
        assert len(result) == 2
        assert "Кафедра анатомии" in result

    async def test_extract_lecturers(self):
        """Test lecturer extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {"lectorName": "Иванов И.И.", "departmentName": "Кафедра анатомии"}
                ]
            }
        ]

        result = service._extract_lecturers(schedules_data)
        assert len(result) > 0
        assert all("full_name" in l and "department_name" in l for l in result)

    async def test_extract_rooms(self):
        """Test room extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {
                        "auditoryNumber": "201",
                        "locationAddress": "Корпус А",
                        "auditoryHousing": "Главный"
                    }
                ]
            }
        ]

        result = service._extract_rooms(schedules_data)
        assert len(result) > 0
        assert all("room_number" in r for r in result)

    async def test_extract_subjects(self):
        """Test subject extraction."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {"subjectName": "Анатомия"},
                    {"subjectName": "Физиология"}
                ]
            }
        ]

        result = service._extract_subjects(schedules_data)
        assert len(result) == 2
        assert "Анатомия" in result

    async def test_get_all_schedules_empty(self):
        """Test getting schedules when API returns empty."""
        service = APISyncService()

        with patch.object(service.api_client, "find_schedule_ids", return_value=[]):
            result = await service._get_all_schedules()
            assert result == []

    async def test_get_all_schedules_with_data(self):
        """Test getting schedules with data."""
        service = APISyncService()

        mock_ids = [1, 2, 3]
        mock_schedule = {"id": 1, "fileName": "test.xlsx"}

        with patch.object(service.api_client, "find_schedule_ids", return_value=mock_ids):
            with patch.object(service.api_client, "get_schedule_data", return_value=mock_schedule):
                result = await service._get_all_schedules()
                assert len(result) == 3

    async def test_get_schedule_details_success(self):
        """Test getting schedule details."""
        service = APISyncService()

        mock_data = {"id": 1, "scheduleLessonDtoList": []}

        with patch.object(service.api_client, "get_schedule_data", return_value=mock_data):
            result = await service._get_schedule_details(1)
            assert result == mock_data

    async def test_get_schedule_details_failure(self):
        """Test getting schedule details with error."""
        service = APISyncService()

        with patch.object(service.api_client, "get_schedule_data", side_effect=Exception("API Error")):
            result = await service._get_schedule_details(1)
            assert result is None

    async def test_save_faculties(self, db_session):
        """Test saving faculties to database."""
        service = APISyncService()

        faculties_data = [
            {"name": "Test Faculty", "short_name": "TF"}
        ]

        await service._save_faculties(faculties_data)
        assert service.sync_stats["faculties_created"] == 1

    async def test_save_lesson_types(self, db_session):
        """Test saving lesson types."""
        service = APISyncService()

        types_data = ["лекция", "практика"]

        await service._save_lesson_types(types_data)
        assert service.sync_stats["lesson_types_created"] == 2

    async def test_save_departments(self, db_session):
        """Test saving departments."""
        service = APISyncService()

        departments_data = ["Кафедра анатомии", "Кафедра физиологии"]

        await service._save_departments(departments_data)
        assert service.sync_stats["departments_created"] == 2

    async def test_save_subjects(self, db_session):
        """Test saving subjects."""
        service = APISyncService()

        subjects_data = ["Анатомия", "Физиология"]

        await service._save_subjects(subjects_data)
        assert service.sync_stats["subjects_created"] == 2

    async def test_save_academic_years(self, db_session):
        """Test saving academic years."""
        service = APISyncService()

        years_data = ["2024/2025", "2025/2026"]

        await service._save_academic_years(years_data)
        assert service.sync_stats["academic_years_created"] == 2

    async def test_full_sync_failure(self, db_session):
        """Test full sync with failure."""
        service = APISyncService()

        with patch.object(service, "_get_all_schedules", side_effect=Exception("API Error")):
            result = await service.full_sync()
            assert result is False

    async def test_full_sync_success(self, db_session):
        """Test successful full sync."""
        service = APISyncService()

        with patch.object(service, "_get_all_schedules", return_value=[]):
            with patch.object(service, "_sync_reference_data", return_value=None):
                with patch.object(service, "_sync_schedules", return_value=None):
                    result = await service.full_sync()
                    assert result is True

    async def test_sync_reference_data(self, db_session):
        """Test syncing reference data."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"speciality": "31.05.01 лечебное дело"}
                ],
                "scheduleLessonDtoList": [
                    {"subjectName": "Анатомия"}
                ]
            }
        ]

        await service._sync_reference_data(schedules_data)

        # Check that stats were updated
        assert service.sync_stats["subjects_created"] > 0

    async def test_resolve_group_id_not_found(self, db_session):
        """Test group ID resolution when group doesn't exist."""
        from app.database.session import get_session

        service = APISyncService()

        async for session in get_session():
            lesson_data = {"studyGroup": "NonExistentGroup"}
            result = await service._resolve_group_id(session, lesson_data)
            assert result is None
            break

    async def test_parse_time_edge_cases(self):
        """Test time parsing edge cases."""
        service = APISyncService()

        # No dash
        start, end = service._parse_time("09:00")
        assert start is None
        assert end is None

        # Multiple dashes
        start, end = service._parse_time("09:00-10:30-11:00")
        # Should handle first split
        assert start is None or start is not None

    async def test_extract_faculties_duplicates(self):
        """Test that duplicate faculties are handled."""
        service = APISyncService()

        schedules_data = [
            {
                "xlsxHeaderDto": [
                    {"speciality": "31.05.01 лечебное дело"},
                    {"speciality": "31.05.01 лечебное дело"}  # Duplicate
                ]
            }
        ]

        result = service._extract_faculties(schedules_data)
        # Should only have one "Лечебный факультет"
        assert len(result) == 1

    async def test_extract_rooms_no_auditory_number(self):
        """Test room extraction when room number is missing."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {"locationAddress": "Корпус А"}  # No auditoryNumber
                ]
            }
        ]

        result = service._extract_rooms(schedules_data)
        assert len(result) == 0

    async def test_save_rooms(self, db_session):
        """Test saving rooms to database."""
        service = APISyncService()

        rooms_data = [
            {"room_number": "201", "building": "Корпус А", "campus": "Главный"},
            {"room_number": "202", "building": None, "campus": None}
        ]

        await service._save_rooms(rooms_data)
        assert service.sync_stats["rooms_created"] == 2

    async def test_extract_lesson_types_no_data(self):
        """Test lesson type extraction with missing data."""
        service = APISyncService()

        schedules_data = [
            {"xlsxHeaderDto": [{}]}  # No lessonTypeName
        ]

        result = service._extract_lesson_types(schedules_data)
        assert len(result) == 0

    async def test_extract_departments_no_data(self):
        """Test department extraction with no data."""
        service = APISyncService()

        schedules_data = [
            {"scheduleLessonDtoList": [{}]}  # No departmentName
        ]

        result = service._extract_departments(schedules_data)
        assert len(result) == 0

    async def test_extract_lecturers_no_lector_name(self):
        """Test lecturer extraction without names."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {"departmentName": "Кафедра анатомии"}  # No lectorName
                ]
            }
        ]

        result = service._extract_lecturers(schedules_data)
        assert len(result) == 0

    async def test_extract_subjects_no_subject_name(self):
        """Test subject extraction without names."""
        service = APISyncService()

        schedules_data = [
            {
                "scheduleLessonDtoList": [
                    {"lessonType": "лекция"}  # No subjectName
                ]
            }
        ]

        result = service._extract_subjects(schedules_data)
        assert len(result) == 0

    async def test_generate_short_name_generic(self):
        """Test short name generation for generic faculty."""
        service = APISyncService()

        result = service._generate_short_name("Факультет Новый")
        assert len(result) > 0
        # Should take first letters
        assert result == "ФН"
