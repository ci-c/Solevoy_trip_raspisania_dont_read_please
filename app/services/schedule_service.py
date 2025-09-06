"""
Сервис для работы с расписанием.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from loguru import logger

from app.database.connection import DatabaseConnection
from app.models.education import Schedule, LessonType


class ScheduleService:
    """Сервис для работы с расписанием."""

    def __init__(self, db_manager: Optional[DatabaseConnection] = None):
        self.db = db_manager or DatabaseConnection()

    async def get_group_schedule(
        self, group_id: int, start_date: date, end_date: date
    ) -> List[Schedule]:
        """Получить расписание группы на период."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    s.id, s.group_id, s.date, s.week_number, s.day_of_week,
                    s.lesson_number, s.subject_name, s.lesson_type, s.teacher_name,
                    s.room_number, s.building, s.start_time, s.end_time,
                    s.is_cancelled, s.notes, s.created_at, s.updated_at
                FROM schedules s
                WHERE s.group_id = ? 
                  AND s.date BETWEEN ? AND ?
                  AND s.is_cancelled = FALSE
                ORDER BY s.date, s.lesson_number
            """,
                (group_id, start_date, end_date),
            )

            rows = await cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]

    async def get_user_schedule(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[Schedule]:
        """Получить персональное расписание пользователя."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    s.id, s.group_id, s.date, s.week_number, s.day_of_week,
                    s.lesson_number, s.subject_name, s.lesson_type, s.teacher_name,
                    s.room_number, s.building, s.start_time, s.end_time,
                    s.is_cancelled, s.notes, s.created_at, s.updated_at
                FROM schedules s
                JOIN student_profiles sp ON s.group_id = sp.group_id
                WHERE sp.user_id = ? 
                  AND s.date BETWEEN ? AND ?
                  AND s.is_cancelled = FALSE
                ORDER BY s.date, s.lesson_number
            """,
                (user_id, start_date, end_date),
            )

            rows = await cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]

    async def create_schedule_entry(self, schedule: Schedule) -> Schedule:
        """Создать запись расписания."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                INSERT INTO schedules (
                    group_id, date, week_number, day_of_week, lesson_number,
                    subject_name, lesson_type, teacher_name, room_number, building,
                    start_time, end_time, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    schedule.group_id,
                    schedule.date,
                    schedule.week_number,
                    schedule.day_of_week,
                    schedule.lesson_number,
                    schedule.subject_name,
                    schedule.lesson_type,
                    schedule.teacher_name,
                    schedule.room_number,
                    schedule.building,
                    schedule.start_time,
                    schedule.end_time,
                    schedule.notes,
                ),
            )

            schedule_id = cursor.lastrowid
            await conn.commit()
            logger.info(f"Created schedule entry {schedule_id}")

            return await self.get_schedule_by_id(schedule_id)

    async def get_schedule_by_id(self, schedule_id: int) -> Optional[Schedule]:
        """Получить расписание по ID."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    id, group_id, date, week_number, day_of_week, lesson_number,
                    subject_name, lesson_type, teacher_name, room_number, building,
                    start_time, end_time, is_cancelled, notes, created_at, updated_at
                FROM schedules 
                WHERE id = ?
            """,
                (schedule_id,),
            )

            row = await cursor.fetchone()
            return Schedule(**dict(row)) if row else None

    async def cancel_lesson(self, schedule_id: int, reason: str) -> bool:
        """Отменить занятие."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                UPDATE schedules 
                SET is_cancelled = TRUE, 
                    notes = COALESCE(notes || ' | ', '') || ?
                WHERE id = ?
            """,
                (f"Отменено: {reason}", schedule_id),
            )

            await conn.commit()
            logger.info(f"Cancelled lesson {schedule_id}: {reason}")
            return cursor.rowcount > 0

    async def get_lessons_by_subject(
        self, group_id: int, subject_name: str, semester_start: date, semester_end: date
    ) -> List[Schedule]:
        """Получить все занятия по предмету."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    id, group_id, date, week_number, day_of_week, lesson_number,
                    subject_name, lesson_type, teacher_name, room_number, building,
                    start_time, end_time, is_cancelled, notes, created_at, updated_at
                FROM schedules 
                WHERE group_id = ? 
                  AND subject_name = ?
                  AND date BETWEEN ? AND ?
                ORDER BY date, lesson_number
            """,
                (group_id, subject_name, semester_start, semester_end),
            )

            rows = await cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]

    async def get_teacher_schedule(
        self, teacher_name: str, start_date: date, end_date: date
    ) -> List[Schedule]:
        """Получить расписание преподавателя."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    s.id, s.group_id, s.date, s.week_number, s.day_of_week,
                    s.lesson_number, s.subject_name, s.lesson_type, s.teacher_name,
                    s.room_number, s.building, s.start_time, s.end_time,
                    s.is_cancelled, s.notes, s.created_at, s.updated_at,
                    g.number as group_number
                FROM schedules s
                JOIN groups g ON s.group_id = g.id
                WHERE s.teacher_name LIKE ? 
                  AND s.date BETWEEN ? AND ?
                  AND s.is_cancelled = FALSE
                ORDER BY s.date, s.lesson_number
            """,
                (f"%{teacher_name}%", start_date, end_date),
            )

            rows = await cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]

    async def bulk_import_schedule(self, schedules: List[Dict[str, Any]]) -> int:
        """Массовый импорт расписания."""
        imported_count = 0

        async for conn in self.db.get_connection():
            for schedule_data in schedules:
                try:
                    await conn.execute(
                        """
                        INSERT OR REPLACE INTO schedules (
                            group_id, date, week_number, day_of_week, lesson_number,
                            subject_name, lesson_type, teacher_name, room_number, 
                            building, start_time, end_time, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            schedule_data.get("group_id"),
                            schedule_data.get("date"),
                            schedule_data.get("week_number"),
                            schedule_data.get("day_of_week"),
                            schedule_data.get("lesson_number"),
                            schedule_data.get("subject_name"),
                            schedule_data.get("lesson_type"),
                            schedule_data.get("teacher_name"),
                            schedule_data.get("room_number"),
                            schedule_data.get("building"),
                            schedule_data.get("start_time"),
                            schedule_data.get("end_time"),
                            schedule_data.get("notes"),
                        ),
                    )
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing schedule entry: {e}")
                    continue

            await conn.commit()
            logger.info(f"Bulk imported {imported_count} schedule entries")

        return imported_count

    async def get_schedule_statistics(self, group_id: int) -> Dict[str, Any]:
        """Получить статистику по расписанию группы."""
        async for conn in self.db.get_connection():
            # Общее количество занятий
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as total_lessons
                FROM schedules 
                WHERE group_id = ? AND is_cancelled = FALSE
            """,
                (group_id,),
            )
            total_lessons = (await cursor.fetchone())[0]

            # По типам занятий
            cursor = await conn.execute(
                """
                SELECT lesson_type, COUNT(*) as count
                FROM schedules 
                WHERE group_id = ? AND is_cancelled = FALSE
                GROUP BY lesson_type
            """,
                (group_id,),
            )
            lessons_by_type = dict(await cursor.fetchall())

            # По предметам
            cursor = await conn.execute(
                """
                SELECT subject_name, COUNT(*) as count
                FROM schedules 
                WHERE group_id = ? AND is_cancelled = FALSE
                GROUP BY subject_name
                ORDER BY count DESC
                LIMIT 10
            """,
                (group_id,),
            )
            top_subjects = dict(await cursor.fetchall())

            return {
                "total_lessons": total_lessons,
                "lessons_by_type": lessons_by_type,
                "top_subjects": top_subjects,
            }

    async def search_lessons(
        self,
        query: str,
        group_id: Optional[int] = None,
        lesson_type: Optional[LessonType] = None,
    ) -> List[Schedule]:
        """Поиск занятий по тексту."""
        conditions = [
            "(subject_name LIKE ? OR teacher_name LIKE ? OR room_number LIKE ?)"
        ]
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if group_id:
            conditions.append("group_id = ?")
            params.append(group_id)

        if lesson_type:
            conditions.append("lesson_type = ?")
            params.append(lesson_type)

        conditions.append("is_cancelled = FALSE")

        where_clause = " AND ".join(conditions)

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                f"""
                SELECT 
                    id, group_id, date, week_number, day_of_week, lesson_number,
                    subject_name, lesson_type, teacher_name, room_number, building,
                    start_time, end_time, is_cancelled, notes, created_at, updated_at
                FROM schedules 
                WHERE {where_clause}
                ORDER BY date DESC, lesson_number
                LIMIT 50
            """,
                params,
            )

            rows = await cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]
