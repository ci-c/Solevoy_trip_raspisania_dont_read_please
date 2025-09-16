"""
Реальный сервис для работы с расписанием через SZGMU API.
"""

import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from app.database.session import get_session
from app.database.models import Schedule, Group
from app.utils.secrets import get_api_base_url


class RealScheduleService:
    """Реальный сервис для работы с расписанием."""

    def __init__(self):
        self.api_base_url = get_api_base_url()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'SZGMU-Schedule-Bot/2.0',
                'Accept': 'application/json',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def search_groups(self, query: str) -> List[Dict[str, Any]]:
        """Поиск групп через API."""
        if not self.session:
            raise RuntimeError("Service not initialized. Use async with.")

        try:
            url = f"{self.api_base_url}/groups/search"
            params = {"q": query, "limit": 10}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("groups", [])
                else:
                    logger.warning(f"API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching groups: {e}")
            return []

    async def get_group_schedule(self, group_id: str, week: int = None) -> List[Dict[str, Any]]:
        """Получить расписание группы."""
        if not self.session:
            raise RuntimeError("Service not initialized. Use async with.")

        try:
            url = f"{self.api_base_url}/groups/{group_id}/schedule"
            params = {}
            if week:
                params["week"] = week
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("schedule", [])
                else:
                    logger.warning(f"API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting group schedule: {e}")
            return []

    async def get_teacher_schedule(self, teacher_id: str, week: int = None) -> List[Dict[str, Any]]:
        """Получить расписание преподавателя."""
        if not self.session:
            raise RuntimeError("Service not initialized. Use async with.")

        try:
            url = f"{self.api_base_url}/teachers/{teacher_id}/schedule"
            params = {}
            if week:
                params["week"] = week
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("schedule", [])
                else:
                    logger.warning(f"API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting teacher schedule: {e}")
            return []

    async def get_room_schedule(self, room_id: str, week: int = None) -> List[Dict[str, Any]]:
        """Получить расписание аудитории."""
        if not self.session:
            raise RuntimeError("Service not initialized. Use async with.")

        try:
            url = f"{self.api_base_url}/rooms/{room_id}/schedule"
            params = {}
            if week:
                params["week"] = week
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("schedule", [])
                else:
                    logger.warning(f"API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting room schedule: {e}")
            return []

    async def save_schedule_to_db(self, group_id: str, schedule_data: List[Dict[str, Any]]) -> bool:
        """Сохранить расписание в базу данных."""
        try:
            async for session in get_session():
                # Находим или создаем группу
                group = await session.get(Group, group_id)
                if not group:
                    group = Group(
                        id=group_id,
                        number=group_id,
                        faculty="Unknown",
                        course=1,
                        stream="а"
                    )
                    session.add(group)
                    await session.commit()

                # Сохраняем расписание
                for lesson_data in schedule_data:
                    schedule = Schedule(
                        group_id=group_id,
                        subject_name=lesson_data.get("subject", ""),
                        teacher_name=lesson_data.get("teacher", ""),
                        room_number=lesson_data.get("room", ""),
                        start_time=lesson_data.get("start_time", ""),
                        end_time=lesson_data.get("end_time", ""),
                        day_of_week=lesson_data.get("day", 1),
                        week_number=lesson_data.get("week", 1),
                        lesson_type=lesson_data.get("type", "lecture"),
                        date=lesson_data.get("date", datetime.now().date())
                    )
                    session.add(schedule)

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving schedule to DB: {e}")
            return False

    async def get_schedule_from_db(self, group_id: str, week: int = None) -> List[Dict[str, Any]]:
        """Получить расписание из базы данных."""
        try:
            async for session in get_session():
                query = session.query(Schedule).filter(Schedule.group_id == group_id)
                
                if week:
                    query = query.filter(Schedule.week_number == week)
                
                schedules = await session.execute(query)
                results = []
                
                for schedule in schedules.scalars():
                    results.append({
                        "subject": schedule.subject_name,
                        "teacher": schedule.teacher_name,
                        "room": schedule.room_number,
                        "start_time": schedule.start_time,
                        "end_time": schedule.end_time,
                        "day": schedule.day_of_week,
                        "week": schedule.week_number,
                        "type": schedule.lesson_type,
                        "date": schedule.date.isoformat() if schedule.date else None
                    })
                
                return results
        except Exception as e:
            logger.error(f"Error getting schedule from DB: {e}")
            return []

    async def sync_schedule(self, group_id: str) -> bool:
        """Синхронизировать расписание с API."""
        try:
            async with self as service:
                # Получаем данные с API
                api_schedule = await service.get_group_schedule(group_id)
                
                if api_schedule:
                    # Сохраняем в БД
                    success = await service.save_schedule_to_db(group_id, api_schedule)
                    if success:
                        logger.info(f"Successfully synced schedule for group {group_id}")
                        return True
                
                return False
        except Exception as e:
            logger.error(f"Error syncing schedule for group {group_id}: {e}")
            return False

    def format_schedule_for_display(self, schedule_data: List[Dict[str, Any]]) -> str:
        """Форматировать расписание для отображения в боте."""
        if not schedule_data:
            return "📅 Расписание не найдено."

        # Группируем по дням недели
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        grouped_schedule = {i: [] for i in range(1, 8)}
        
        for lesson in schedule_data:
            day = lesson.get("day", 1)
            if 1 <= day <= 7:
                grouped_schedule[day].append(lesson)

        result = "📅 **Расписание занятий**\n\n"
        
        for day_num in range(1, 8):
            if grouped_schedule[day_num]:
                result += f"**{days[day_num-1]}**\n"
                
                # Сортируем по времени
                sorted_lessons = sorted(
                    grouped_schedule[day_num], 
                    key=lambda x: x.get("start_time", "00:00")
                )
                
                for lesson in sorted_lessons:
                    start_time = lesson.get("start_time", "")
                    end_time = lesson.get("end_time", "")
                    subject = lesson.get("subject", "Неизвестно")
                    teacher = lesson.get("teacher", "")
                    room = lesson.get("room", "")
                    lesson_type = lesson.get("type", "лекция")
                    
                    # Эмодзи для типа занятия
                    type_emoji = {
                        "лекция": "📚",
                        "практика": "🔬", 
                        "семинар": "💬",
                        "лабораторная": "🧪"
                    }.get(lesson_type.lower(), "📖")
                    
                    result += f"🕐 {start_time}-{end_time}\n"
                    result += f"{type_emoji} {subject}\n"
                    if teacher:
                        result += f"👨‍🏫 {teacher}\n"
                    if room:
                        result += f"🏢 {room}\n"
                    result += "\n"
                
                result += "\n"
        
        return result
