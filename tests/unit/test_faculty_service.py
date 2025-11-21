"""Comprehensive tests for FacultyService."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.database.models import Faculty
from app.services.faculty_service import FacultyService


@pytest.mark.asyncio
@pytest.mark.unit
class TestFacultyService:
    """Tests for FacultyService."""

    async def test_init(self):
        """Test FacultyService initialization."""
        service = FacultyService()
        assert service is not None

    async def test_load_faculties_from_api_success(self):
        """Test successful faculty loading from API."""
        service = FacultyService()

        mock_response = {
            "content": [
                {
                    "xlsxHeaderDto": [
                        {"speciality": "31.05.01 лечебное дело"},
                        {"speciality": "31.05.02 педиатрия"}
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json = MagicMock(return_value=mock_response)
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.load_faculties_from_api()

            assert len(result) > 0
            assert all("name" in faculty for faculty in result)
            assert all("short_name" in faculty for faculty in result)

    async def test_load_faculties_from_api_http_error(self):
        """Test faculty loading with HTTP error."""
        service = FacultyService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.load_faculties_from_api()

            assert result == []

    async def test_load_faculties_from_api_request_error(self):
        """Test faculty loading with request error."""
        service = FacultyService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.load_faculties_from_api()

            assert result == []

    async def test_load_faculties_from_api_missing_content(self):
        """Test faculty loading when API response missing content."""
        service = FacultyService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json.return_value = {}
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.load_faculties_from_api()

            assert result == []

    async def test_extract_faculty_from_speciality_lechebnoe(self):
        """Test faculty extraction for лечебное дело."""
        service = FacultyService()
        result = service._extract_faculty_from_speciality("31.05.01 лечебное дело")
        assert result == "Лечебный факультет"

    async def test_extract_faculty_from_speciality_pediatriya(self):
        """Test faculty extraction for педиатрия."""
        service = FacultyService()
        result = service._extract_faculty_from_speciality("31.05.02 педиатрия")
        assert result == "Педиатрический факультет"

    async def test_extract_faculty_from_speciality_stomatology(self):
        """Test faculty extraction for стоматология."""
        service = FacultyService()
        result = service._extract_faculty_from_speciality("31.05.03 стоматология")
        assert result == "Стоматологический факультет"

    async def test_extract_faculty_from_speciality_pharmacy(self):
        """Test faculty extraction for фармация."""
        service = FacultyService()
        result = service._extract_faculty_from_speciality("33.05.01 фармация")
        assert result == "Фармацевтический факультет"

    async def test_extract_faculty_from_speciality_unknown(self):
        """Test faculty extraction for unknown speciality."""
        service = FacultyService()
        result = service._extract_faculty_from_speciality("Неизвестная специальность")
        assert result == "Неизвестный факультет"

    async def test_generate_short_name_lechebniy(self):
        """Test short name generation for Лечебный факультет."""
        service = FacultyService()
        result = service._generate_short_name("Лечебный факультет")
        assert result == "ЛФ"

    async def test_generate_short_name_pediatricheskiy(self):
        """Test short name generation for Педиатрический факультет."""
        service = FacultyService()
        result = service._generate_short_name("Педиатрический факультет")
        assert result == "ПФ"

    async def test_generate_short_name_generic(self):
        """Test short name generation for generic name."""
        service = FacultyService()
        result = service._generate_short_name("Новый факультет")
        assert len(result) > 0

    async def test_save_faculties_to_db_success(self, db_session):
        """Test successful saving of faculties to database."""
        service = FacultyService()

        faculties_data = [
            {
                "name": "Лечебный факультет",
                "short_name": "ЛФ",
                "description": "Факультет Лечебный факультет"
            }
        ]

        result = await service.save_faculties_to_db(faculties_data)
        assert result is True

    async def test_save_faculties_to_db_empty_list(self, db_session):
        """Test saving empty list of faculties."""
        service = FacultyService()
        result = await service.save_faculties_to_db([])
        assert result is True

    async def test_get_faculties_from_db_empty(self, db_session):
        """Test getting faculties from empty database."""
        service = FacultyService()
        result = await service.get_faculties_from_db()
        assert result == []

    async def test_get_faculties_from_db_with_data(self, db_session):
        """Test getting faculties from database with data."""
        service = FacultyService()

        # First save some data
        faculties_data = [
            {
                "name": "Лечебный факультет",
                "short_name": "ЛФ",
                "description": "Факультет Лечебный факультет"
            }
        ]
        await service.save_faculties_to_db(faculties_data)

        # Then retrieve it
        result = await service.get_faculties_from_db()
        assert len(result) > 0
        assert result[0]["name"] == "Лечебный факультет"

    async def test_sync_faculties_success(self, db_session):
        """Test successful faculty synchronization."""
        service = FacultyService()

        mock_response = {
            "content": [
                {
                    "xlsxHeaderDto": [
                        {"speciality": "31.05.01 лечебное дело"}
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json = MagicMock(return_value=mock_response)
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.sync_faculties()
            assert result is True

    async def test_sync_faculties_api_failure(self, db_session):
        """Test faculty sync when API fails."""
        service = FacultyService()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(side_effect=Exception("API Error"))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.sync_faculties()
            assert result is False

    async def test_get_faculty_names_empty(self, db_session):
        """Test getting faculty names from empty database."""
        service = FacultyService()
        result = await service.get_faculty_names()
        assert result == []

    async def test_get_faculty_names_with_data(self, db_session):
        """Test getting faculty names with data in database."""
        service = FacultyService()

        faculties_data = [
            {"name": "Лечебный факультет", "short_name": "ЛФ"},
            {"name": "Педиатрический факультет", "short_name": "ПФ"}
        ]
        await service.save_faculties_to_db(faculties_data)

        result = await service.get_faculty_names()
        assert len(result) == 2
        assert "Лечебный факультет" in result

    async def test_get_faculty_by_name_not_found(self, db_session):
        """Test getting faculty by name when not exists."""
        service = FacultyService()
        result = await service.get_faculty_by_name("Несуществующий факультет")
        assert result is None

    async def test_get_faculty_by_name_found(self, db_session):
        """Test getting faculty by name when exists."""
        service = FacultyService()

        faculties_data = [
            {"name": "Лечебный факультет", "short_name": "ЛФ"}
        ]
        await service.save_faculties_to_db(faculties_data)

        result = await service.get_faculty_by_name("Лечебный факультет")
        assert result is not None
        assert result["name"] == "Лечебный факультет"

    async def test_get_all_faculties_empty(self, db_session):
        """Test getting all faculties from empty database."""
        service = FacultyService()
        result = await service.get_all_faculties()
        assert result == []

    async def test_get_all_faculties_with_data(self, db_session):
        """Test getting all faculties with data."""
        service = FacultyService()

        faculties_data = [
            {"name": "Лечебный факультет", "short_name": "ЛФ"}
        ]
        await service.save_faculties_to_db(faculties_data)

        result = await service.get_all_faculties()
        assert len(result) > 0
        assert isinstance(result[0], Faculty)

    async def test_extract_multiple_faculties(self):
        """Test extracting multiple unique faculties."""
        service = FacultyService()

        mock_response = {
            "content": [
                {
                    "xlsxHeaderDto": [
                        {"speciality": "31.05.01 лечебное дело"},
                        {"speciality": "31.05.02 педиатрия"},
                        {"speciality": "31.05.01 лечебное дело"}  # Duplicate
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.json = MagicMock(return_value=mock_response)
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await service.load_faculties_from_api()

            # Should have 2 unique faculties, not 3
            assert len(result) == 2
