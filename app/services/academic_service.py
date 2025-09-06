"""
Сервис для работы с академическими данными (оценки, посещаемость).
"""

from typing import List, Optional, Dict, Any
from datetime import date
from loguru import logger

from app.database.connection import DatabaseConnection
from app.models.education import Grade, GradeType, AttendanceRecord


class AcademicService:
    """Сервис для работы с академическими данными."""

    def __init__(self, db_manager: Optional[DatabaseConnection] = None):
        self.db = db_manager or DatabaseConnection()

    # =============== ОЦЕНКИ ===============

    async def create_grade(self, grade: Grade) -> Grade:
        """Создать запись об оценке."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                INSERT INTO grades (
                    student_id, subject_name, grade_type, grade_value,
                    max_grade, date_recorded, semester, teacher_name, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    grade.student_id,
                    grade.subject_name,
                    grade.grade_type,
                    grade.grade_value,
                    grade.max_grade,
                    grade.date_recorded,
                    grade.semester,
                    grade.teacher_name,
                    grade.notes,
                ),
            )

            grade_id = cursor.lastrowid
            await conn.commit()
            logger.info(f"Created grade {grade_id} for student {grade.student_id}")

            return await self.get_grade_by_id(grade_id)

    async def get_grade_by_id(self, grade_id: int) -> Optional[Grade]:
        """Получить оценку по ID."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    id, student_id, subject_name, grade_type, grade_value,
                    max_grade, date_recorded, semester, teacher_name, notes,
                    created_at, updated_at
                FROM grades 
                WHERE id = ?
            """,
                (grade_id,),
            )

            row = await cursor.fetchone()
            return Grade(**dict(row)) if row else None

    async def get_student_grades(
        self,
        student_id: int,
        subject_name: Optional[str] = None,
        grade_type: Optional[GradeType] = None,
        semester: Optional[str] = None,
    ) -> List[Grade]:
        """Получить оценки студента."""
        conditions = ["student_id = ?"]
        params = [student_id]

        if subject_name:
            conditions.append("subject_name = ?")
            params.append(subject_name)

        if grade_type:
            conditions.append("grade_type = ?")
            params.append(grade_type)

        if semester:
            conditions.append("semester = ?")
            params.append(semester)

        where_clause = " AND ".join(conditions)

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                f"""
                SELECT 
                    id, student_id, subject_name, grade_type, grade_value,
                    max_grade, date_recorded, semester, teacher_name, notes,
                    created_at, updated_at
                FROM grades 
                WHERE {where_clause}
                ORDER BY date_recorded DESC, subject_name
            """,
                params,
            )

            rows = await cursor.fetchall()
            return [Grade(**dict(row)) for row in rows]

    async def get_grade_statistics(
        self, student_id: int, semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получить статистику по оценкам студента."""
        conditions = ["student_id = ?"]
        params = [student_id]

        if semester:
            conditions.append("semester = ?")
            params.append(semester)

        where_clause = " AND ".join(conditions)

        async for conn in self.db.get_connection():
            # Общая статистика
            cursor = await conn.execute(
                f"""
                SELECT 
                    COUNT(*) as total_grades,
                    AVG(CAST(grade_value as REAL)) as avg_grade,
                    MIN(CAST(grade_value as REAL)) as min_grade,
                    MAX(CAST(grade_value as REAL)) as max_grade
                FROM grades 
                WHERE {where_clause} AND grade_value NOT IN ('зачет', 'незачет')
            """,
                params,
            )
            general_stats = dict(await cursor.fetchone())

            # По типам оценок
            cursor = await conn.execute(
                f"""
                SELECT grade_type, COUNT(*) as count, AVG(CAST(grade_value as REAL)) as avg_grade
                FROM grades 
                WHERE {where_clause} AND grade_value NOT IN ('зачет', 'незачет')
                GROUP BY grade_type
            """,
                params,
            )
            by_type = {
                row[0]: {"count": row[1], "avg_grade": row[2]}
                for row in await cursor.fetchall()
            }

            # По предметам
            cursor = await conn.execute(
                f"""
                SELECT subject_name, COUNT(*) as count, AVG(CAST(grade_value as REAL)) as avg_grade
                FROM grades 
                WHERE {where_clause} AND grade_value NOT IN ('зачет', 'незачет')
                GROUP BY subject_name
                ORDER BY avg_grade DESC
            """,
                params,
            )
            by_subject = {
                row[0]: {"count": row[1], "avg_grade": row[2]}
                for row in await cursor.fetchall()
            }

            return {
                "general": general_stats,
                "by_type": by_type,
                "by_subject": by_subject,
            }

    async def calculate_gpa(
        self, student_id: int, semester: Optional[str] = None
    ) -> Optional[float]:
        """Вычислить средний балл студента."""
        conditions = ["student_id = ?", "grade_value NOT IN ('зачет', 'незачет')"]
        params = [student_id]

        if semester:
            conditions.append("semester = ?")
            params.append(semester)

        where_clause = " AND ".join(conditions)

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                f"""
                SELECT AVG(CAST(grade_value as REAL)) as gpa
                FROM grades 
                WHERE {where_clause}
            """,
                params,
            )

            result = await cursor.fetchone()
            return result[0] if result and result[0] else None

    # =============== ПОСЕЩАЕМОСТЬ ===============

    async def record_attendance(self, attendance: AttendanceRecord) -> AttendanceRecord:
        """Записать посещаемость."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                INSERT INTO attendance (
                    student_id, schedule_id, status, notes, recorded_by
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    attendance.student_id,
                    attendance.schedule_id,
                    attendance.status,
                    attendance.notes,
                    attendance.recorded_by,
                ),
            )

            attendance_id = cursor.lastrowid
            await conn.commit()
            logger.info(
                f"Recorded attendance {attendance_id} for student {attendance.student_id}"
            )

            return await self.get_attendance_by_id(attendance_id)

    async def get_attendance_by_id(
        self, attendance_id: int
    ) -> Optional[AttendanceRecord]:
        """Получить запись посещаемости по ID."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT 
                    id, student_id, schedule_id, status, notes, recorded_by,
                    created_at, updated_at
                FROM attendance 
                WHERE id = ?
            """,
                (attendance_id,),
            )

            row = await cursor.fetchone()
            return AttendanceRecord(**dict(row)) if row else None

    async def get_student_attendance(
        self,
        student_id: int,
        subject_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[AttendanceRecord]:
        """Получить записи посещаемости студента."""
        conditions = ["a.student_id = ?"]
        params = [student_id]

        joins = ["JOIN schedules s ON a.schedule_id = s.id"]

        if subject_name:
            conditions.append("s.subject_name = ?")
            params.append(subject_name)

        if start_date:
            conditions.append("s.date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("s.date <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions)
        join_clause = " ".join(joins)

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                f"""
                SELECT 
                    a.id, a.student_id, a.schedule_id, a.status, a.notes, 
                    a.recorded_by, a.created_at, a.updated_at,
                    s.subject_name, s.date, s.lesson_type
                FROM attendance a
                {join_clause}
                WHERE {where_clause}
                ORDER BY s.date DESC
            """,
                params,
            )

            rows = await cursor.fetchall()
            return [AttendanceRecord(**dict(row)) for row in rows]

    async def get_attendance_statistics(
        self, student_id: int, subject_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получить статистику посещаемости."""
        conditions = ["a.student_id = ?"]
        params = [student_id]

        if subject_name:
            conditions.append("s.subject_name = ?")
            params.append(subject_name)

        where_clause = " AND ".join(conditions)

        async for conn in self.db.get_connection():
            # Общая статистика
            cursor = await conn.execute(
                f"""
                SELECT 
                    COUNT(*) as total_lessons,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as attended,
                    SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as missed,
                    SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late
                FROM attendance a
                JOIN schedules s ON a.schedule_id = s.id
                WHERE {where_clause}
            """,
                params,
            )

            row = await cursor.fetchone()
            total, attended, missed, late = row

            attendance_rate = (attended / total * 100) if total > 0 else 0

            # По предметам
            cursor = await conn.execute(
                """
                SELECT 
                    s.subject_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as attended,
                    SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as missed
                FROM attendance a
                JOIN schedules s ON a.schedule_id = s.id
                WHERE a.student_id = ?
                GROUP BY s.subject_name
            """,
                [student_id],
            )

            by_subject = {}
            for row in await cursor.fetchall():
                subject, total, attended, missed = row
                rate = (attended / total * 100) if total > 0 else 0
                by_subject[subject] = {
                    "total": total,
                    "attended": attended,
                    "missed": missed,
                    "attendance_rate": rate,
                }

            return {
                "total_lessons": total,
                "attended": attended,
                "missed": missed,
                "late": late,
                "attendance_rate": attendance_rate,
                "by_subject": by_subject,
            }

    async def bulk_import_grades(self, grades_data: List[Dict[str, Any]]) -> int:
        """Массовый импорт оценок."""
        imported_count = 0

        async for conn in self.db.get_connection():
            for grade_data in grades_data:
                try:
                    await conn.execute(
                        """
                        INSERT OR REPLACE INTO grades (
                            student_id, subject_name, grade_type, grade_value,
                            max_grade, date_recorded, semester, teacher_name, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            grade_data.get("student_id"),
                            grade_data.get("subject_name"),
                            grade_data.get("grade_type"),
                            grade_data.get("grade_value"),
                            grade_data.get("max_grade"),
                            grade_data.get("date_recorded"),
                            grade_data.get("semester"),
                            grade_data.get("teacher_name"),
                            grade_data.get("notes"),
                        ),
                    )
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing grade: {e}")
                    continue

            await conn.commit()
            logger.info(f"Bulk imported {imported_count} grades")

        return imported_count

    async def get_subject_grades_summary(
        self, student_id: int, subject_name: str, semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получить сводку по оценкам по предмету."""
        conditions = ["student_id = ?", "subject_name = ?"]
        params = [student_id, subject_name]

        if semester:
            conditions.append("semester = ?")
            params.append(semester)

        where_clause = " AND ".join(conditions)

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                f"""
                SELECT 
                    grade_type,
                    COUNT(*) as count,
                    GROUP_CONCAT(grade_value, ', ') as grades,
                    AVG(CASE WHEN grade_value NOT IN ('зачет', 'незачет') 
                            THEN CAST(grade_value as REAL) END) as avg_grade
                FROM grades 
                WHERE {where_clause}
                GROUP BY grade_type
                ORDER BY grade_type
            """,
                params,
            )

            grades_by_type = {}
            for row in await cursor.fetchall():
                grade_type, count, grades, avg_grade = row
                grades_by_type[grade_type] = {
                    "count": count,
                    "grades": grades.split(", ") if grades else [],
                    "avg_grade": avg_grade,
                }

            return grades_by_type
