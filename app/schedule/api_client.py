"""Асинхронный HTTP‑клиент для работы с расписаниями СЗГМУ."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class APIClient:
    """Асинхронный клиент для API `xlsxSchedule`."""

    def __init__(self, timeout: float = 20.0) -> None:
        self.base_url = "https://frsview.szgmu.ru/api/xlsxSchedule"
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": "SZGMU-Schedule-Bot/2.0",
        }
        self._timeout = httpx.Timeout(timeout)

    async def _post_json(
        self, client: httpx.AsyncClient, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = await client.post(
            f"{self.base_url}{endpoint}", json=payload, headers=self._headers
        )
        response.raise_for_status()
        return response.json()

    async def _get_json(
        self, client: httpx.AsyncClient, endpoint: str
    ) -> Dict[str, Any]:
        response = await client.get(
            f"{self.base_url}{endpoint}", headers=self._headers
        )
        response.raise_for_status()
        return response.json()

    async def find_schedule_ids(
        self,
        group_stream: Optional[List[str]] = None,
        speciality: Optional[List[str]] = None,
        course_number: Optional[List[str]] = None,
        academic_year: Optional[List[str]] = None,
        lesson_type: Optional[List[str]] = None,
        semester: Optional[List[str]] = None,
    ) -> List[int]:
        payload: Dict[str, Any] = {
            "groupStream": group_stream or [],
            "speciality": speciality or [],
            "courseNumber": course_number or [],
            "academicYear": academic_year or [],
            "lessonType": lesson_type or [],
            "semester": semester or [],
        }

        schedule_ids: List[int] = []
        page = 0
        total_elements: Optional[int] = None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            while True:
                try:
                    data = await self._post_json(
                        client, f"/findAll/{page}", payload
                    )
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "Schedule list request returned %s on page %s",
                        exc.response.status_code,
                        page,
                    )
                    break
                except httpx.RequestError as exc:
                    logger.error(f"Schedule list request error: {exc}")
                    break

                content = data.get("content", [])
                if not content:
                    if page == 0:
                        logger.info("API returned empty content for first page")
                    break

                page_ids = [item.get("id") for item in content if item.get("id")]
                schedule_ids.extend(page_ids)

                if total_elements is None:
                    total_elements = data.get("totalElements", len(schedule_ids))

                if len(schedule_ids) >= total_elements:
                    break

                page += 1

        logger.info(f"Collected {len(schedule_ids)} schedule IDs")
        return schedule_ids

    async def get_schedule_data(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                data = await self._get_json(
                    client, f"/findById?xlsxScheduleId={schedule_id}"
                )
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Schedule data request returned %s for id %s",
                    exc.response.status_code,
                    schedule_id,
                )
                return None
            except httpx.RequestError as exc:
                logger.error(
                    f"Schedule data request error for id {schedule_id}: {exc}"
                )
                return None

        lessons = data.get("scheduleLessonDtoList")
        if not lessons:
            logger.warning(f"Schedule {schedule_id} has no lessons")
            return None

        logger.debug(
            "Loaded schedule %s with %s lessons", schedule_id, len(lessons)
        )
        return data

    async def search_schedules(self, filters: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        logger.info(f"Starting schedule search with filters: {filters}")

        course_number = filters.get("Курс", [])
        speciality = filters.get("Специальность", [])
        group_stream = filters.get("Поток", [])
        semester = filters.get("Семестр", [])
        academic_year = filters.get("Учебный год", [])
        group = filters.get("Группа", [])

        if group and not course_number:
            for group_num in group:
                if group_num and group_num[0].isdigit():
                    course_number = [group_num[0]]
                    logger.info(
                        "Extracted course %s from group %s",
                        course_number[0],
                        group_num,
                    )
                    break

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

        max_schedules = min(3, len(schedule_ids))
        tasks = [self.get_schedule_data(schedule_id) for schedule_id in schedule_ids[:max_schedules]]
        schedule_data_list = await asyncio.gather(*tasks, return_exceptions=True)

        results: List[Dict[str, Any]] = []
        for schedule_id, data in zip(schedule_ids, schedule_data_list):
            if isinstance(data, Exception):
                logger.error(f"Error in schedule task for ID {schedule_id}: {data}")
                continue
            if not data:
                continue
            results.append(data)

        logger.info(f"Collected {len(results)} schedules")
        return results
