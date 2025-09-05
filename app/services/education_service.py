"""
Сервис для работы с образовательными сущностями.
"""

from typing import List, Optional
from loguru import logger

from ..database.connection import get_db
from ..models.education import Speciality, StudyGroup, Teacher, Room


class EducationService:
    """Асинхронный сервис для управления образовательными данными."""

    async def create_or_update_speciality(self, speciality: Speciality) -> Speciality:
        """Создать или обновить специальность."""
        async with get_db() as conn:
            # Проверяем существует ли специальность с таким кодом
            cursor = await conn.execute("""
                SELECT id FROM specialities WHERE code = ?
            """, (speciality.code,))
            
            existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующую
                await conn.execute("""
                    UPDATE specialities 
                    SET name = ?, full_name = ?, faculty = ?, degree_type = ?, study_years = ?
                    WHERE code = ?
                """, (speciality.name, speciality.full_name, speciality.faculty,
                      speciality.degree_type.value, speciality.study_years, speciality.code))
                speciality.id = existing[0]
            else:
                # Создаем новую
                cursor = await conn.execute("""
                    INSERT INTO specialities (code, name, full_name, faculty, degree_type, study_years)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (speciality.code, speciality.name, speciality.full_name, 
                      speciality.faculty, speciality.degree_type.value, speciality.study_years))
                speciality.id = cursor.lastrowid
            
            await conn.commit()
            
        logger.info(f"Created/updated speciality {speciality.code}: {speciality.name}")
        return speciality
    
    async def get_speciality_by_code(self, code: str) -> Optional[Speciality]:
        """Получить специальность по коду."""
        async with get_db() as conn:
            cursor = await conn.execute("""
                SELECT * FROM specialities WHERE code = ?
            """, (code,))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            speciality_dict = {
                "id": row[0],
                "code": row[1],
                "name": row[2],
                "full_name": row[3],
                "faculty": row[4],
                "degree_type": row[5],
                "study_years": row[6],
                "created_at": row[7]
            }
            
            return Speciality(**speciality_dict)
    
    async def get_all_specialities(self) -> List[Speciality]:
        """Получить все специальности."""
        async with get_db() as conn:
            cursor = await conn.execute("""
                SELECT * FROM specialities ORDER BY name
            """)
            
            rows = await cursor.fetchall()
            specialities = []
            
            for row in rows:
                speciality_dict = {
                    "id": row[0],
                    "code": row[1],
                    "name": row[2],
                    "full_name": row[3],
                    "faculty": row[4],
                    "degree_type": row[5],
                    "study_years": row[6],
                    "created_at": row[7]
                }
                specialities.append(Speciality(**speciality_dict))
            
            return specialities
    
    async def create_or_update_group(self, group: StudyGroup) -> StudyGroup:
        """Создать или обновить группу."""
        async with get_db() as conn:
            # Проверяем существует ли группа
            cursor = await conn.execute("""
                SELECT id FROM study_groups 
                WHERE number = ? AND academic_year = ?
            """, (group.number, group.academic_year))
            
            existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующую
                await conn.execute("""
                    UPDATE study_groups 
                    SET course = ?, stream = ?, speciality_id = ?, current_semester = ?, is_active = ?
                    WHERE id = ?
                """, (group.course, group.stream, group.speciality_id, 
                      group.current_semester.value if group.current_semester else None,
                      group.is_active, existing[0]))
                group.id = existing[0]
            else:
                # Создаем новую
                cursor = await conn.execute("""
                    INSERT INTO study_groups 
                    (number, course, stream, speciality_id, current_semester, academic_year, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (group.number, group.course, group.stream, group.speciality_id,
                      group.current_semester.value if group.current_semester else None,
                      group.academic_year, group.is_active))
                group.id = cursor.lastrowid
            
            await conn.commit()
            
        logger.info(f"Created/updated group {group.number}")
        return group
    
    async def find_groups_by_number(self, number: str) -> List[StudyGroup]:
        """Найти группы по номеру."""
        async with get_db() as conn:
            cursor = await conn.execute("""
                SELECT * FROM study_groups 
                WHERE number LIKE ? AND is_active = 1
                ORDER BY academic_year DESC
            """, (f"%{number}%",))
            
            rows = await cursor.fetchall()
            groups = []
            
            for row in rows:
                group_dict = {
                    "id": row[0],
                    "number": row[1],
                    "course": row[2],
                    "stream": row[3],
                    "speciality_id": row[4],
                    "current_semester": row[5],
                    "academic_year": row[6],
                    "is_active": bool(row[7]),
                    "created_at": row[8]
                }
                groups.append(StudyGroup(**group_dict))
            
            return groups
    
    async def create_or_update_teacher(self, teacher: Teacher) -> Teacher:
        """Создать или обновить преподавателя."""
        async with get_db() as conn:
            # Проверяем существует ли преподаватель с таким именем
            cursor = await conn.execute("""
                SELECT id FROM teachers WHERE full_name = ?
            """, (teacher.full_name,))
            
            existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующего
                await conn.execute("""
                    UPDATE teachers 
                    SET short_name = ?, department = ?, position = ?, email = ?
                    WHERE id = ?
                """, (teacher.short_name, teacher.department, teacher.position,
                      teacher.email, existing[0]))
                teacher.id = existing[0]
            else:
                # Создаем нового
                cursor = await conn.execute("""
                    INSERT INTO teachers (full_name, short_name, department, position, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (teacher.full_name, teacher.short_name, teacher.department,
                      teacher.position, teacher.email))
                teacher.id = cursor.lastrowid
            
            await conn.commit()
            
        return teacher
    
    async def find_teacher_by_name(self, name: str) -> Optional[Teacher]:
        """Найти преподавателя по имени."""
        async with get_db() as conn:
            cursor = await conn.execute("""
                SELECT * FROM teachers 
                WHERE full_name LIKE ? OR short_name LIKE ?
                LIMIT 1
            """, (f"%{name}%", f"%{name}%"))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            teacher_dict = {
                "id": row[0],
                "full_name": row[1],
                "short_name": row[2],
                "department": row[3],
                "position": row[4],
                "email": row[5],
                "created_at": row[6]
            }
            
            return Teacher(**teacher_dict)
    
    async def create_or_update_room(self, room: Room) -> Room:
        """Создать или обновить аудиторию."""
        async with get_db() as conn:
            # Проверяем существует ли аудитория
            cursor = await conn.execute("""
                SELECT id FROM rooms 
                WHERE number = ? AND (building = ? OR building IS NULL)
            """, (room.number, room.building))
            
            existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующую
                await conn.execute("""
                    UPDATE rooms 
                    SET building = ?, floor = ?, capacity = ?, equipment = ?, room_type = ?
                    WHERE id = ?
                """, (room.building, room.floor, room.capacity, room.equipment,
                      room.room_type, existing[0]))
                room.id = existing[0]
            else:
                # Создаем новую
                cursor = await conn.execute("""
                    INSERT INTO rooms (number, building, floor, capacity, equipment, room_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (room.number, room.building, room.floor, room.capacity,
                      room.equipment, room.room_type))
                room.id = cursor.lastrowid
            
            await conn.commit()
            
        return room
    
    async def find_room_by_number(self, number: str) -> Optional[Room]:
        """Найти аудиторию по номеру."""
        async with get_db() as conn:
            cursor = await conn.execute("""
                SELECT * FROM rooms WHERE number = ? LIMIT 1
            """, (number,))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            room_dict = {
                "id": row[0],
                "number": row[1],
                "building": row[2],
                "floor": row[3],
                "capacity": row[4],
                "equipment": row[5],
                "room_type": row[6],
                "created_at": row[7]
            }
            
            return Room(**room_dict)