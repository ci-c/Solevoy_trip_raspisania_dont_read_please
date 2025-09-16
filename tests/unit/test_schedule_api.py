"""
Тесты для Schedule API.

Критически важные функции:
- Поиск расписаний по фильтрам
- Парсинг данных занятий из внешнего API
- Обработка ошибок и тайм-аутов
- Кэширование результатов
"""

import pytest
from unittest.mock import patch, MagicMock

from app.schedule.api import search_schedules, get_available_filters, find_schedule_ids, get_schedule_data


@pytest.mark.asyncio
@pytest.mark.unit
class TestScheduleAPI:
    """Тесты для Schedule API."""

    @patch('app.schedule.api.requests.post')
    def test_find_schedule_ids_success(self, mock_post):
        """Тест успешного поиска ID расписаний."""
        # Мокируем успешный ответ API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [
                {"id": 123}, 
                {"id": 456}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = find_schedule_ids(
            group_stream=["а"],
            speciality=["31.05.01 лечебное дело"],
            course_number=["1"],
            academic_year=["2024/2025"]
        )

        assert result == [123, 456]
        mock_post.assert_called_once()

    @patch('app.schedule.api.requests.post')
    def test_find_schedule_ids_api_error(self, mock_post):
        """Тест обработки ошибки API при поиске ID."""
        mock_post.side_effect = Exception("API Error")

        result = find_schedule_ids(group_stream=["а"])

        assert result == []

    @patch('app.schedule.api.requests.get')  
    def test_get_schedule_data_success(self, mock_get):
        """Тест успешного получения данных расписания."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "fileName": "test_schedule.xlsx",
            "scheduleLessonDtoList": [
                {
                    "subject": "Анатомия",
                    "teacher": "Иванов И.И.",
                    "room": "101",
                    "timeStart": "09:00",
                    "timeEnd": "10:35"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_schedule_data(schedule_id=123)

        assert result is not None
        assert result["fileName"] == "test_schedule.xlsx"
        assert len(result["scheduleLessonDtoList"]) == 1

    @patch('app.schedule.api.requests.get')
    def test_get_schedule_data_timeout(self, mock_get):
        """Тест обработки тайм-аута при получении данных."""
        mock_get.side_effect = Exception("Timeout")

        result = get_schedule_data(schedule_id=123)

        assert result is None

    async def test_get_available_filters_returns_static_data(self):
        """Тест получения доступных фильтров (статические данные)."""
        filters = await get_available_filters()
        
        assert "Курс" in filters
        assert "Специальность" in filters
        assert "Поток" in filters
        assert isinstance(filters["Курс"], list)
        assert len(filters["Курс"]) > 0

    @patch('app.schedule.api.find_schedule_ids')
    @patch('app.schedule.api.get_schedule_data')
    async def test_search_schedules_success(self, mock_get_data, mock_find_ids):
        """Тест успешного поиска расписаний."""
        # Мокируем поиск ID
        mock_find_ids.return_value = [123, 456]
        
        # Мокируем получение данных
        mock_schedule_data = {
            "fileName": "test.xlsx",
            "scheduleLessonDtoList": [
                {
                    "subject": "Анатомия",
                    "teacher": "Петров П.П.",
                    "group": "101а",
                    "speciality": "31.05.01 лечебное дело",
                    "courseNumber": "1",
                    "groupStream": "а",
                    "semester": "осенний",
                    "academicYear": "2024/2025"
                }
            ]
        }
        mock_get_data.return_value = mock_schedule_data

        filters = {
            "Курс": ["1"],
            "Специальность": ["31.05.01 лечебное дело"],
            "Поток": ["а"]
        }

        result = await search_schedules(filters)

        assert len(result) == 2  # Два расписания найдено
        assert result[0]["id"] == 123
        assert "display_name" in result[0]
        assert "data" in result[0]

    @patch('app.schedule.api.find_schedule_ids')  
    async def test_search_schedules_no_results(self, mock_find_ids):
        """Тест поиска без результатов."""
        mock_find_ids.return_value = []

        filters = {"Курс": ["99"]}  # Несуществующий курс

        result = await search_schedules(filters)

        assert result == []

    async def test_search_schedules_with_group_filter(self):
        """Тест поиска с фильтром по группе."""
        with patch('app.schedule.api.find_schedule_ids') as mock_find_ids:
            mock_find_ids.return_value = []

            filters = {"Группа": ["101а"]}

            await search_schedules(filters)

            # Проверяем что курс был автоматически извлечен из номера группы
            mock_find_ids.assert_called_once()
            call_args = mock_find_ids.call_args[1]
            assert call_args["course_number"] == ["1"]  # Из "101а" извлечен курс "1"

    @pytest.mark.parametrize("filters,expected_course", [
        ({"Группа": ["101а"]}, ["1"]),
        ({"Группа": ["205б"]}, ["2"]),  
        ({"Группа": ["348в"]}, ["3"]),
        ({"Группа": ["abc"]}, []),  # Невалидный номер группы
    ])
    async def test_course_extraction_from_group(self, filters, expected_course):
        """Тест автоматического извлечения курса из номера группы."""
        with patch('app.schedule.api.find_schedule_ids') as mock_find_ids:
            mock_find_ids.return_value = []

            await search_schedules(filters)

            if expected_course:
                call_args = mock_find_ids.call_args[1]
                assert call_args["course_number"] == expected_course
            else:
                # Для невалидных номеров групп курс не должен устанавливаться
                call_args = mock_find_ids.call_args[1]
                assert call_args.get("course_number", []) == []