"""
Сервис автоматического обновления расписаний из внешних источников.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from app.database.connection import DatabaseConnection
from app.services.schedule_service import ScheduleService
from app.services.group_service import GroupService
from app.schedule.group_search import GroupSearchService
from app.schedule.semester_detector import SemesterDetector


class ScheduleUpdaterService:
    """Сервис для автоматического обновления расписаний в БД."""

    def __init__(self, db_manager: Optional[DatabaseConnection] = None):
        self.db = db_manager or DatabaseConnection()
        self.schedule_service = ScheduleService(self.db)
        self.group_service = GroupService(self.db)
        self.group_search_service = GroupSearchService()
        self.semester_detector = SemesterDetector()

    async def update_all_schedules(self, force: bool = False) -> Dict[str, Any]:
        """
        Обновить расписания всех активных групп.

        Args:
            force: Принудительное обновление даже если недавно обновлялись

        Returns:
            Статистика обновления
        """
        logger.info("Starting schedule update for all groups")

        stats = {
            "total_groups": 0,
            "updated_groups": 0,
            "failed_groups": 0,
            "new_lessons": 0,
            "updated_lessons": 0,
            "errors": [],
        }

        try:
            # Получаем список всех активных групп
            active_groups = await self.group_service.get_active_groups()
            stats["total_groups"] = len(active_groups)

            logger.info(f"Found {len(active_groups)} active groups to update")

            # Определяем период для обновления (текущий семестр)
            semester_info = self.semester_detector.get_current_semester_info()
            start_date = semester_info.start_date
            end_date = semester_info.end_date

            # Обновляем группы пачками для контроля нагрузки
            batch_size = 5
            for i in range(0, len(active_groups), batch_size):
                batch = active_groups[i : i + batch_size]
                batch_tasks = []

                for group in batch:
                    if self._should_update_group(group, force):
                        task = self._update_group_schedule(group, start_date, end_date)
                        batch_tasks.append(task)

                # Выполняем пачку параллельно
                if batch_tasks:
                    batch_results = await asyncio.gather(
                        *batch_tasks, return_exceptions=True
                    )

                    for result in batch_results:
                        if isinstance(result, Exception):
                            stats["failed_groups"] += 1
                            stats["errors"].append(str(result))
                        else:
                            stats["updated_groups"] += 1
                            stats["new_lessons"] += result.get("new_lessons", 0)
                            stats["updated_lessons"] += result.get("updated_lessons", 0)

                # Пауза между пачками для снижения нагрузки
                if i + batch_size < len(active_groups):
                    await asyncio.sleep(2)

            # Обновляем время последнего обновления
            await self._update_last_sync_time()

            logger.info(f"Schedule update completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Critical error in schedule update: {e}")
            stats["errors"].append(f"Critical error: {str(e)}")
            return stats

    async def update_group_schedule(self, group_id: int) -> Dict[str, Any]:
        """
        Обновить расписание конкретной группы.

        Args:
            group_id: ID группы в БД

        Returns:
            Результат обновления
        """
        try:
            group = await self.group_service.get_group_by_id(group_id)
            if not group:
                raise ValueError(f"Group {group_id} not found")

            semester_info = self.semester_detector.get_current_semester_info()
            result = await self._update_group_schedule(
                group, semester_info.start_date, semester_info.end_date
            )

            # Обновляем время последнего обновления группы
            await self.group_service.update_group_last_sync(group_id)

            return result

        except Exception as e:
            logger.error(f"Error updating group {group_id} schedule: {e}")
            raise

    async def _update_group_schedule(
        self, group: Dict[str, Any], start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Обновить расписание одной группы."""
        group_number = group["number"]
        group_id = group["id"]

        logger.info(f"Updating schedule for group {group_number}")

        result = {
            "group_id": group_id,
            "group_number": group_number,
            "new_lessons": 0,
            "updated_lessons": 0,
            "errors": [],
        }

        try:
            # Получаем свежее расписание из внешнего источника
            external_groups = await self.group_search_service.search_group_by_number(
                group_number
            )

            if not external_groups:
                logger.warning(f"No external data found for group {group_number}")
                return result

            external_group = external_groups[0]

            # Получаем расписание на весь семестр
            schedule_data = await self._fetch_full_semester_schedule(
                external_group, start_date, end_date
            )

            if not schedule_data:
                logger.warning(f"No schedule data for group {group_number}")
                return result

            # Сохраняем/обновляем расписание в БД
            for lesson_data in schedule_data:
                lesson_data["group_id"] = group_id

                existing_lesson = await self._find_existing_lesson(lesson_data)

                if existing_lesson:
                    # Обновляем существующее занятие если изменилось
                    if self._lesson_changed(existing_lesson, lesson_data):
                        await self._update_lesson(existing_lesson["id"], lesson_data)
                        result["updated_lessons"] += 1
                else:
                    # Создаем новое занятие
                    await self._create_lesson(lesson_data)
                    result["new_lessons"] += 1

            logger.info(
                f"Group {group_number} updated: "
                f"+{result['new_lessons']} new, ~{result['updated_lessons']} updated"
            )

            return result

        except Exception as e:
            error_msg = f"Error updating group {group_number}: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            raise

    async def _fetch_full_semester_schedule(
        self, external_group: Any, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Получить полное расписание группы на семестр."""
        schedule_data = []

        # Получаем расписание по неделям
        semester_info = self.semester_detector.get_current_semester_info()

        for week_num in range(1, semester_info.total_weeks + 1):
            try:
                # Здесь должен быть вызов API для получения расписания на неделю
                # Пока используем заглушку на основе существующих данных
                week_schedule = await self._get_week_schedule(external_group, week_num)

                if week_schedule:
                    schedule_data.extend(week_schedule)

                # Небольшая пауза между запросами
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning(f"Error fetching week {week_num}: {e}")
                continue

        return schedule_data

    async def _get_week_schedule(
        self, external_group: Any, week_number: int
    ) -> List[Dict[str, Any]]:
        """Получить расписание группы на конкретную неделю."""
        # Заглушка - нужно интегрировать с реальным API
        # Возвращаем пустой список, так как это требует интеграции с API СЗГМУ
        return []

    async def _find_existing_lesson(
        self, lesson_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Найти существующее занятие в БД."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM schedules
                WHERE group_id = ? 
                  AND date = ? 
                  AND lesson_number = ?
                  AND subject_name = ?
            """,
                (
                    lesson_data["group_id"],
                    lesson_data["date"],
                    lesson_data["lesson_number"],
                    lesson_data["subject_name"],
                ),
            )

            row = await cursor.fetchone()
            return dict(row) if row else None

    async def _create_lesson(self, lesson_data: Dict[str, Any]) -> None:
        """Создать новое занятие в БД."""
        async for conn in self.db.get_connection():
            await conn.execute(
                """
                INSERT INTO schedules (
                    group_id, date, week_number, day_of_week, lesson_number,
                    subject_name, lesson_type, teacher_name, room_number, 
                    building, start_time, end_time, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    lesson_data["group_id"],
                    lesson_data["date"],
                    lesson_data.get("week_number"),
                    lesson_data.get("day_of_week"),
                    lesson_data["lesson_number"],
                    lesson_data["subject_name"],
                    lesson_data.get("lesson_type"),
                    lesson_data.get("teacher_name"),
                    lesson_data.get("room_number"),
                    lesson_data.get("building"),
                    lesson_data.get("start_time"),
                    lesson_data.get("end_time"),
                    lesson_data.get("notes"),
                ),
            )

            await conn.commit()

    async def _update_lesson(self, lesson_id: int, lesson_data: Dict[str, Any]) -> None:
        """Обновить существующее занятие."""
        async for conn in self.db.get_connection():
            await conn.execute(
                """
                UPDATE schedules SET
                    lesson_type = ?, teacher_name = ?, room_number = ?,
                    building = ?, start_time = ?, end_time = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (
                    lesson_data.get("lesson_type"),
                    lesson_data.get("teacher_name"),
                    lesson_data.get("room_number"),
                    lesson_data.get("building"),
                    lesson_data.get("start_time"),
                    lesson_data.get("end_time"),
                    lesson_data.get("notes"),
                    lesson_id,
                ),
            )

            await conn.commit()

    def _should_update_group(self, group: Dict[str, Any], force: bool) -> bool:
        """Определить нужно ли обновлять группу."""
        if force:
            return True

        last_sync = group.get("last_sync")
        if not last_sync:
            return True

        # Обновляем если прошло больше 6 часов
        last_sync_dt = datetime.fromisoformat(last_sync)
        return datetime.now() - last_sync_dt > timedelta(hours=6)

    def _lesson_changed(
        self, existing: Dict[str, Any], new_data: Dict[str, Any]
    ) -> bool:
        """Проверить изменилось ли занятие."""
        fields_to_check = [
            "lesson_type",
            "teacher_name",
            "room_number",
            "building",
            "start_time",
            "end_time",
        ]

        for field in fields_to_check:
            if existing.get(field) != new_data.get(field):
                return True

        return False

    async def _update_last_sync_time(self) -> None:
        """Обновить время последней синхронизации."""
        async for conn in self.db.get_connection():
            await conn.execute(
                """
                INSERT OR REPLACE INTO system_settings (key, value)
                VALUES ('last_schedule_sync', ?)
            """,
                (datetime.now().isoformat(),),
            )

            await conn.commit()

    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Получить статистику синхронизации."""
        async for conn in self.db.get_connection():
            # Время последней синхронизации
            cursor = await conn.execute("""
                SELECT value FROM system_settings 
                WHERE key = 'last_schedule_sync'
            """)
            last_sync_row = await cursor.fetchone()
            last_sync = last_sync_row[0] if last_sync_row else None

            # Статистика по группам
            cursor = await conn.execute("""
                SELECT COUNT(*) as total_groups,
                       COUNT(CASE WHEN last_sync IS NOT NULL THEN 1 END) as synced_groups
                FROM groups 
                WHERE is_active = 1
            """)
            groups_stats = await cursor.fetchone()

            # Общее количество занятий
            cursor = await conn.execute("""
                SELECT COUNT(*) as total_lessons,
                       COUNT(CASE WHEN DATE(created_at) = DATE('now') THEN 1 END) as today_lessons
                FROM schedules
            """)
            lessons_stats = await cursor.fetchone()

            return {
                "last_sync": last_sync,
                "total_groups": groups_stats[0],
                "synced_groups": groups_stats[1],
                "total_lessons": lessons_stats[0],
                "lessons_added_today": lessons_stats[1],
            }
