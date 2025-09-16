"""
Сервис расчета оценок и коэффициентов согласно регламентам СЗГМУ.
"""

from datetime import date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from app.database.session import get_session
from app.database.models import User
from sqlalchemy import select


@dataclass
class Grade:
    """Оценка студента."""
    id: int
    subject: str
    grade: int  # 5, 4, 3, 2
    control_point: str  # "контрольная", "тест", "собеседование"
    date: date
    is_excused: bool = False  # Уважительная причина


@dataclass
class Attendance:
    """Посещаемость занятия."""
    id: int
    subject: str
    lesson_type: str  # "lecture", "seminar"
    date: date
    is_present: bool
    is_excused: bool = False  # Уважительная причина
    reason: Optional[str] = None


@dataclass
class SubjectStats:
    """Статистика по предмету."""
    subject: str
    tsb: float  # Текущий средний балл
    knl: float  # Коэффициент непосещаемости лекций
    kns: float  # Коэффициент непосещаемости семинаров
    osb: float  # Общий средний балл = ТСБ + КНЛ + КНС
    total_lessons: int
    attended_lessons: int
    excused_absences: int
    unexcused_absences: int


class GradeCalculatorService:
    """Сервис расчета оценок и коэффициентов."""

    def __init__(self):
        self.excused_reasons = {
            "болезнь": True,
            "регистрация брака": True,
            "смерть родственников": True,
            "донорство": True,
            "олимпиады": True,
            "вызовы в органы": True,
            "медосмотры": True
        }

    async def calculate_tsb(self, user_id: int, subject: str) -> float:
        """Рассчитать текущий средний балл по предмету."""
        try:
            # Получаем все оценки по предмету
            grades = await self._get_grades(user_id, subject)
            
            if not grades:
                return 0.0
            
            # Исключаем оценки с уважительной причиной (Нб)
            valid_grades = [g for g in grades if g.grade != 0 and not g.is_excused]
            
            if not valid_grades:
                return 0.0
            
            # Рассчитываем средний балл
            total = sum(g.grade for g in valid_grades)
            return round(total / len(valid_grades), 2)
            
        except Exception as e:
            logger.error(f"Error calculating TSB for user {user_id}, subject {subject}: {e}")
            return 0.0

    async def calculate_knl(self, user_id: int, subject: str) -> float:
        """Рассчитать коэффициент непосещаемости лекций."""
        try:
            # Получаем посещаемость лекций
            attendance = await self._get_attendance(user_id, subject, "lecture")
            
            if not attendance:
                return 0.0
            
            # Исключаем уважительные пропуски
            total_lessons = len(attendance)
            unexcused_absences = sum(1 for a in attendance if not a.is_present and not a.is_excused)
            
            if total_lessons == 0:
                return 0.0
            
            # КНЛ = -1 * (количество неуважительных пропусков / общее количество лекций)
            knl = -1 * (unexcused_absences / total_lessons)
            return round(knl, 3)
            
        except Exception as e:
            logger.error(f"Error calculating KNL for user {user_id}, subject {subject}: {e}")
            return 0.0

    async def calculate_kns(self, user_id: int, subject: str) -> float:
        """Рассчитать коэффициент непосещаемости семинаров."""
        try:
            # Получаем посещаемость семинаров
            attendance = await self._get_attendance(user_id, subject, "seminar")
            
            if not attendance:
                return 0.0
            
            # Исключаем уважительные пропуски
            total_lessons = len(attendance)
            unexcused_absences = sum(1 for a in attendance if not a.is_present and not a.is_excused)
            
            if total_lessons == 0:
                return 0.0
            
            # КНС = -1 * (количество неуважительных пропусков / общее количество семинаров)
            kns = -1 * (unexcused_absences / total_lessons)
            return round(kns, 3)
            
        except Exception as e:
            logger.error(f"Error calculating KNS for user {user_id}, subject {subject}: {e}")
            return 0.0

    async def calculate_osb(self, user_id: int, subject: str) -> float:
        """Рассчитать общий средний балл = ТСБ + КНЛ + КНС."""
        try:
            tsb = await self.calculate_tsb(user_id, subject)
            knl = await self.calculate_knl(user_id, subject)
            kns = await self.calculate_kns(user_id, subject)
            
            osb = tsb + knl + kns
            return round(osb, 3)
            
        except Exception as e:
            logger.error(f"Error calculating OSB for user {user_id}, subject {subject}: {e}")
            return 0.0

    async def get_subject_stats(self, user_id: int, subject: str) -> SubjectStats:
        """Получить полную статистику по предмету."""
        try:
            # Получаем все данные
            await self._get_grades(user_id, subject)
            lecture_attendance = await self._get_attendance(user_id, subject, "lecture")
            seminar_attendance = await self._get_attendance(user_id, subject, "seminar")
            
            # Рассчитываем показатели
            tsb = await self.calculate_tsb(user_id, subject)
            knl = await self.calculate_knl(user_id, subject)
            kns = await self.calculate_kns(user_id, subject)
            osb = tsb + knl + kns
            
            # Статистика посещаемости
            total_lessons = len(lecture_attendance) + len(seminar_attendance)
            attended_lessons = sum(1 for a in lecture_attendance + seminar_attendance if a.is_present)
            excused_absences = sum(1 for a in lecture_attendance + seminar_attendance if not a.is_present and a.is_excused)
            unexcused_absences = sum(1 for a in lecture_attendance + seminar_attendance if not a.is_present and not a.is_excused)
            
            return SubjectStats(
                subject=subject,
                tsb=tsb,
                knl=knl,
                kns=kns,
                osb=osb,
                total_lessons=total_lessons,
                attended_lessons=attended_lessons,
                excused_absences=excused_absences,
                unexcused_absences=unexcused_absences
            )
            
        except Exception as e:
            logger.error(f"Error getting subject stats for user {user_id}, subject {subject}: {e}")
            return SubjectStats(
                subject=subject,
                tsb=0.0,
                knl=0.0,
                kns=0.0,
                osb=0.0,
                total_lessons=0,
                attended_lessons=0,
                excused_absences=0,
                unexcused_absences=0
            )

    async def add_grade(
        self, 
        user_id: int, 
        subject: str, 
        grade: int, 
        control_point: str,
        date: date,
        is_excused: bool = False
    ) -> bool:
        """Добавить оценку."""
        try:
            # Валидация оценки
            if grade not in [2, 3, 4, 5]:
                logger.warning(f"Invalid grade {grade} for user {user_id}")
                return False
            
            # TODO: Сохранить в базу данных
            # Пока только логируем
            logger.info(f"Added grade {grade} for user {user_id}, subject {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding grade: {e}")
            return False

    async def add_attendance(
        self,
        user_id: int,
        subject: str,
        lesson_type: str,
        date: date,
        is_present: bool,
        is_excused: bool = False,
        reason: Optional[str] = None
    ) -> bool:
        """Добавить запись о посещаемости."""
        try:
            # Валидация типа занятия
            if lesson_type not in ["lecture", "seminar"]:
                logger.warning(f"Invalid lesson type {lesson_type}")
                return False
            
            # Проверяем уважительность причины
            if is_excused and reason:
                is_excused = self._is_excused_reason(reason)
            
            # TODO: Сохранить в базу данных
            # Пока только логируем
            logger.info(f"Added attendance for user {user_id}, subject {subject}: present={is_present}, excused={is_excused}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding attendance: {e}")
            return False

    def _is_excused_reason(self, reason: str) -> bool:
        """Проверить, является ли причина уважительной."""
        reason_lower = reason.lower()
        return any(excused_reason in reason_lower for excused_reason in self.excused_reasons.keys())

    async def _get_grades(self, user_id: int, subject: str) -> List[Grade]:
        """Получить оценки пользователя по предмету."""
        # TODO: Реализовать получение из базы данных
        # Пока возвращаем заглушку
        return []

    async def _get_attendance(self, user_id: int, subject: str, lesson_type: str) -> List[Attendance]:
        """Получить посещаемость пользователя по предмету и типу занятия."""
        # TODO: Реализовать получение из базы данных
        # Пока возвращаем заглушку
        return []

    async def get_user_subjects(self, user_id: int) -> List[str]:
        """Получить список предметов пользователя."""
        try:
            # Получаем группу пользователя
            async for session in get_session():
                result = await session.execute(
                    select(User)
                    .where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user or not user.group_id:
                    return []
                
                # TODO: Получить предметы из расписания группы
                # Пока возвращаем заглушку
                return ["Анатомия", "Физиология", "Химия", "Биология"]
                
        except Exception as e:
            logger.error(f"Error getting user subjects: {e}")
            return []

    async def get_user_overall_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить общую статистику пользователя."""
        try:
            subjects = await self.get_user_subjects(user_id)
            
            if not subjects:
                return {
                    "total_subjects": 0,
                    "average_osb": 0.0,
                    "total_lessons": 0,
                    "attendance_rate": 0.0
                }
            
            total_osb = 0.0
            total_lessons = 0
            total_attended = 0
            
            for subject in subjects:
                stats = await self.get_subject_stats(user_id, subject)
                total_osb += stats.osb
                total_lessons += stats.total_lessons
                total_attended += stats.attended_lessons
            
            average_osb = total_osb / len(subjects) if subjects else 0.0
            attendance_rate = (total_attended / total_lessons * 100) if total_lessons > 0 else 0.0
            
            return {
                "total_subjects": len(subjects),
                "average_osb": round(average_osb, 3),
                "total_lessons": total_lessons,
                "attendance_rate": round(attendance_rate, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting user overall stats: {e}")
            return {
                "total_subjects": 0,
                "average_osb": 0.0,
                "total_lessons": 0,
                "attendance_rate": 0.0
            }
