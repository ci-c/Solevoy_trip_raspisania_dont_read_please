"""
Сервис для работы с группами и факультетами.
"""

from typing import List, Optional, Dict, Any
from loguru import logger

from app.database.connection import DatabaseConnection


class GroupService:
    """Сервис для работы с группами, факультетами и академической структурой."""

    def __init__(self, db_manager: Optional[DatabaseConnection] = None):
        self.db = db_manager or DatabaseConnection()

    async def get_available_faculties(self) -> List[str]:
        """Получить список названий доступных факультетов."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute("""
                SELECT DISTINCT name FROM faculties 
                WHERE is_active = 1
                ORDER BY name
            """)

            rows = await cursor.fetchall()
            if rows:
                return [row[0] for row in rows]

            # Возвращаем стандартные факультеты СЗГМУ если в БД пусто
            return [
                "Медико-профилактический факультет",
                "Лечебный факультет",
                "Стоматологический факультет",
                "Медико-биологический факультет",
                "Факультет постдипломного образования",
            ]

    async def get_groups_by_faculty(self, faculty_name: str) -> List[Dict[str, Any]]:
        """Получить группы по названию факультета."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT g.id, g.number, g.course, g.stream, g.is_active,
                       f.name as faculty_name
                FROM groups g
                JOIN faculties f ON g.faculty_id = f.id
                WHERE f.name = ? AND g.is_active = 1
                ORDER BY g.course, g.number
            """,
                (faculty_name,),
            )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_active_groups(self) -> List[Dict[str, Any]]:
        """Получить все активные группы."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute("""
                SELECT id, number, faculty_id, course, stream, last_sync
                FROM groups 
                WHERE is_active = 1
                ORDER BY number
            """)

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Получить группу по ID."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT g.id, g.number, g.faculty_id, g.course, g.stream, 
                       g.is_active, g.last_sync, f.name as faculty_name
                FROM groups g
                LEFT JOIN faculties f ON g.faculty_id = f.id
                WHERE g.id = ?
            """,
                (group_id,),
            )

            row = await cursor.fetchone()
            return dict(row) if row else None

    async def find_or_create_group(self, group_number: str) -> Optional[Dict[str, Any]]:
        """Найти группу по номеру или создать новую."""
        # Сначала ищем существующую группу
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT id, number, faculty_id, course, stream, is_active
                FROM groups 
                WHERE LOWER(number) = ?
            """,
                (group_number.lower(),),
            )

            row = await cursor.fetchone()
            if row:
                return dict(row)

        # Создаем новую группу
        try:
            async for conn in self.db.get_connection():
                cursor = await conn.execute(
                    """
                    INSERT INTO groups (number, is_active, created_at)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                """,
                    (group_number,),
                )

                group_id = cursor.lastrowid
                await conn.commit()

                logger.info(f"Created new group: {group_number} (ID: {group_id})")

                # Возвращаем созданную группу
                return {
                    "id": group_id,
                    "number": group_number,
                    "faculty_id": None,
                    "course": None,
                    "stream": None,
                    "is_active": True,
                }

        except Exception as e:
            logger.error(f"Error creating group {group_number}: {e}")
            return None

    async def update_group_info(self, group_id: int, info: Dict[str, Any]) -> bool:
        """Обновить информацию о группе."""
        try:
            # Сначала найдем или создадим факультет
            faculty_id = None
            if info.get("faculty"):
                faculty_id = await self._find_or_create_faculty(info["faculty"])

            async for conn in self.db.get_connection():
                await conn.execute(
                    """
                    UPDATE groups SET
                        faculty_id = ?,
                        course = ?,
                        stream = ?,
                        speciality = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        faculty_id,
                        info.get("course"),
                        info.get("stream"),
                        info.get("speciality"),
                        group_id,
                    ),
                )

                await conn.commit()
                logger.info(f"Updated group {group_id} info")
                return True

        except Exception as e:
            logger.error(f"Error updating group {group_id}: {e}")
            return False

    async def update_group_last_sync(self, group_id: int) -> None:
        """Обновить время последней синхронизации группы."""
        async for conn in self.db.get_connection():
            await conn.execute(
                """
                UPDATE groups SET
                    last_sync = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (group_id,),
            )

            await conn.commit()

    async def _find_or_create_faculty(self, faculty_name: str) -> int:
        """Найти или создать факультет по названию."""
        async for conn in self.db.get_connection():
            # Ищем существующий
            cursor = await conn.execute(
                """
                SELECT id FROM faculties WHERE name = ?
            """,
                (faculty_name,),
            )

            row = await cursor.fetchone()
            if row:
                return row[0]

            # Создаем новый
            cursor = await conn.execute(
                """
                INSERT INTO faculties (name, is_active, created_at)
                VALUES (?, 1, CURRENT_TIMESTAMP)
            """,
                (faculty_name,),
            )

            faculty_id = cursor.lastrowid
            await conn.commit()

            logger.info(f"Created new faculty: {faculty_name} (ID: {faculty_id})")
            return faculty_id

    async def get_faculty_by_id(self, faculty_id: int) -> Optional[Dict[str, Any]]:
        """Получить факультет по ID."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT id, name, short_name, code, description, 
                       is_active, created_at, updated_at
                FROM faculties 
                WHERE id = ?
            """,
                (faculty_id,),
            )

            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_faculties(self) -> List[Dict[str, Any]]:
        """Получить все факультеты."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute("""
                SELECT id, name, short_name, code, description, 
                       is_active, created_at, updated_at
                FROM faculties
                ORDER BY name
            """)

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
