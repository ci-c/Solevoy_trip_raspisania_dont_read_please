"""
Улучшенный API клиент для работы с расписаниями СЗГМУ.
"""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from loguru import logger
import requests


class APIClient:
    """Асинхронный API клиент для СЗГМУ."""

    def __init__(self):
        self.base_url = "https://frsview.szgmu.ru/api/xlsxSchedule"
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "SZGMU-Schedule-Bot/1.0"}
        )

    def _find_schedule_ids_sync(
        self,
        group_stream: Optional[List[str]] = None,
        speciality: Optional[List[str]] = None,
        course_number: Optional[List[str]] = None,
        academic_year: Optional[List[str]] = None,
        lesson_type: Optional[List[str]] = None,
        semester: Optional[List[str]] = None,
    ) -> List[int]:
        """Синхронный поиск ID расписаний."""
        url = f"{self.base_url}/findAll/0"

        payload = {
            "groupStream": group_stream or [],
            "speciality": speciality or [],
            "courseNumber": course_number or [],
            "academicYear": academic_year or [],
            "lessonType": lesson_type or [],
            "semester": semester or [],
        }

        logger.debug(f"API request payload: {payload}")

        try:
            response = self.session.post(url, data=json.dumps(payload), timeout=15)
            response.raise_for_status()
            data = response.json()

            if "content" in data:
                schedule_ids = [item["id"] for item in data["content"]]
                logger.info(f"Found {len(schedule_ids)} schedule IDs")
                return schedule_ids
            else:
                logger.warning("API response missing 'content' key")
                return []

        except requests.exceptions.Timeout:
            logger.error("Schedule IDs request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []

    def _get_schedule_data_sync(self, schedule_id: int) -> Optional[Dict]:
        """Синхронное получение данных расписания."""
        url = f"{self.base_url}/findById?xlsxScheduleId={schedule_id}"

        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            # Базовая валидация данных
            if not data.get("scheduleLessonDtoList"):
                logger.warning(f"Schedule {schedule_id} has no lessons")
                return None

            logger.debug(
                f"Loaded schedule {schedule_id} with {len(data['scheduleLessonDtoList'])} lessons"
            )
            return data

        except requests.exceptions.Timeout:
            logger.error(f"Schedule data request timed out for ID {schedule_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error for schedule {schedule_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for schedule {schedule_id}: {e}")
            return None

    async def find_schedule_ids(
        self,
        group_stream: Optional[List[str]] = None,
        speciality: Optional[List[str]] = None,
        course_number: Optional[List[str]] = None,
        academic_year: Optional[List[str]] = None,
        lesson_type: Optional[List[str]] = None,
        semester: Optional[List[str]] = None,
    ) -> List[int]:
        """Асинхронный поиск ID расписаний."""
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=2) as executor:
            try:
                schedule_ids = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor,
                        self._find_schedule_ids_sync,
                        group_stream,
                        speciality,
                        course_number,
                        academic_year,
                        lesson_type,
                        semester,
                    ),
                    timeout=20.0,
                )
                return schedule_ids

            except asyncio.TimeoutError:
                logger.error("Async schedule IDs search timed out")
                return []

    async def get_schedule_data(self, schedule_id: int) -> Optional[Dict]:
        """Асинхронное получение данных расписания."""
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=2) as executor:
            try:
                schedule_data = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor, self._get_schedule_data_sync, schedule_id
                    ),
                    timeout=25.0,
                )
                return schedule_data

            except asyncio.TimeoutError:
                logger.error(
                    f"Async schedule data request timed out for ID {schedule_id}"
                )
                return None

    async def search_schedules(self, filters: Dict[str, List[str]]) -> List[Dict]:
        """Поиск расписаний с улучшенной обработкой ошибок."""
        logger.info(f"Starting schedule search with filters: {filters}")

        try:
            # Извлекаем параметры поиска
            course_number = filters.get("Курс", [])
            speciality = filters.get("Специальность", [])
            group_stream = filters.get("Поток", [])
            semester = filters.get("Семестр", [])
            academic_year = filters.get("Учебный год", [])
            group = filters.get("Группа", [])

            # Автоматически извлекаем курс из номера группы
            if group and not course_number:
                for group_num in group:
                    if group_num and group_num[0].isdigit():
                        course_number = [group_num[0]]
                        logger.info(
                            f"Extracted course {course_number[0]} from group {group_num}"
                        )
                        break

            # Поиск ID расписаний
            schedule_ids = await self.find_schedule_ids(
                group_stream=group_stream,
                speciality=speciality,
                course_number=course_number,
                academic_year=academic_year,
                semester=semester,
            )

            if not schedule_ids:
                logger.warning("No schedule IDs found")
                return []

            # Ограничиваем количество для производительности
            max_schedules = min(3, len(schedule_ids))
            results = []

            # Обрабатываем расписания параллельно
            tasks = [
                self.get_schedule_data(schedule_id)
                for schedule_id in schedule_ids[:max_schedules]
            ]

            schedule_data_list = await asyncio.gather(*tasks, return_exceptions=True)

            for i, (schedule_id, schedule_data) in enumerate(
                zip(schedule_ids[:max_schedules], schedule_data_list)
            ):
                if isinstance(schedule_data, Exception):
                    logger.error(
                        f"Error loading schedule {schedule_id}: {schedule_data}"
                    )
                    continue

                if not schedule_data:
                    continue

                # Фильтрация по группе
                if group:
                    group_found = self._check_group_in_schedule(schedule_data, group)
                    if not group_found:
                        logger.debug(
                            f"Schedule {schedule_id} doesn't contain requested group"
                        )
                        continue

                # Формируем результат
                display_name = self._create_display_name(schedule_data, schedule_id)

                results.append(
                    {
                        "id": schedule_id,
                        "display_name": display_name,
                        "data": schedule_data,
                    }
                )

                logger.info(f"Processed schedule {schedule_id}: {display_name}")

            logger.info(f"Returning {len(results)} schedules")
            return results

        except Exception as e:
            logger.error(f"Critical error in search_schedules: {e}")
            return []

    def _check_group_in_schedule(self, schedule_data: Dict, groups: List[str]) -> bool:
        """Проверить содержит ли расписание указанную группу."""
        lessons = schedule_data.get("scheduleLessonDtoList", [])

        for lesson in lessons[:20]:  # Проверяем первые 20 занятий
            lesson_group = lesson.get("group", "").lower()
            if any(g.lower() in lesson_group for g in groups):
                return True

        return False

    def _create_display_name(self, schedule_data: Dict, schedule_id: int) -> str:
        """Создать отображаемое имя расписания."""
        lessons = schedule_data.get("scheduleLessonDtoList", [])

        if lessons:
            first_lesson = lessons[0]
            speciality = first_lesson.get("speciality", "Unknown")[:30]
            course_num = first_lesson.get("courseNumber", "Unknown")
            stream = first_lesson.get("groupStream", "Unknown")
            semester = first_lesson.get("semester", "Unknown")
            year = first_lesson.get("academicYear", "Unknown")

            return (
                f"{speciality} - {course_num} курс, {stream} поток, {semester} {year}"
            )
        else:
            file_name = schedule_data.get("fileName", f"Schedule {schedule_id}")
            return file_name[:50]

    def close(self):
        """Закрыть сессию."""
        if self.session:
            self.session.close()

    def __del__(self):
        """Деструктор для очистки ресурсов."""
        try:
            self.close()
        except Exception:
            pass
