"""
Асинхронный сервис для синхронизации данных с API СЗГМУ.
"""

import asyncio
import time
from datetime import datetime, time as dt_time
from typing import List, Dict, Any, Optional, Set
from loguru import logger

from app.database.session import get_session
from app.database.models import (
    Faculty, Speciality, AcademicYear, Semester, LessonType, 
    Department, Lecturer, Classroom, Subject, Schedule, Lesson,
    APISyncLog
)
from app.schedule.api_client import APIClient


class APISyncService:
    """Сервис для синхронизации данных с API СЗГМУ."""

    def __init__(self):
        self.api_client = APIClient()
        self.sync_stats = {
            "faculties_created": 0,
            "specialities_created": 0,
            "academic_years_created": 0,
            "semesters_created": 0,
            "lesson_types_created": 0,
            "departments_created": 0,
            "lecturers_created": 0,
            "classrooms_created": 0,
            "subjects_created": 0,
            "schedules_created": 0,
            "schedules_updated": 0,
            "lessons_created": 0,
            "lessons_updated": 0,
        }

    async def full_sync(self) -> bool:
        """Полная синхронизация всех данных."""
        start_time = time.time()
        logger.info("Starting full API synchronization...")
        
        try:
            # 1. Синхронизируем справочники
            await self._sync_reference_data()
            
            # 2. Синхронизируем расписания
            await self._sync_schedules()
            
            # 3. Логируем результат
            duration = time.time() - start_time
            await self._log_sync_result("full", "success", duration)
            
            logger.info(f"Full synchronization completed in {duration:.2f}s")
            logger.info(f"Sync stats: {self.sync_stats}")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            await self._log_sync_result("full", "error", duration, str(e))
            logger.error(f"Full synchronization failed: {e}")
            return False

    async def _sync_reference_data(self) -> None:
        """Синхронизация справочных данных."""
        logger.info("Syncing reference data...")
        
        # Получаем все расписания для извлечения справочников
        schedules_data = await self._get_all_schedules()
        
        # Извлекаем уникальные данные
        faculties_data = self._extract_faculties(schedules_data)
        specialities_data = self._extract_specialities(schedules_data)
        academic_years_data = self._extract_academic_years(schedules_data)
        semesters_data = self._extract_semesters(schedules_data)
        lesson_types_data = self._extract_lesson_types(schedules_data)
        departments_data = self._extract_departments(schedules_data)
        lecturers_data = self._extract_lecturers(schedules_data)
        classrooms_data = self._extract_classrooms(schedules_data)
        subjects_data = self._extract_subjects(schedules_data)
        
        # Сохраняем в БД
        await self._save_faculties(faculties_data)
        await self._save_specialities(specialities_data)
        await self._save_academic_years(academic_years_data)
        await self._save_semesters(semesters_data)
        await self._save_lesson_types(lesson_types_data)
        await self._save_departments(departments_data)
        await self._save_lecturers(lecturers_data)
        await self._save_classrooms(classrooms_data)
        await self._save_subjects(subjects_data)

    async def _sync_schedules(self) -> None:
        """Синхронизация расписаний и занятий."""
        logger.info("Syncing schedules and lessons...")
        
        schedules_data = await self._get_all_schedules()
        
        for schedule_data in schedules_data:
            # Сохраняем расписание
            schedule_id = await self._save_schedule(schedule_data)
            
            if schedule_id:
                # Получаем детали расписания
                schedule_details = await self._get_schedule_details(schedule_data["id"])
                if schedule_details:
                    # Сохраняем занятия
                    await self._save_lessons(schedule_id, schedule_details)

    async def _get_all_schedules(self) -> List[Dict[str, Any]]:
        """Получить все расписания из API."""
        try:
            loop = asyncio.get_event_loop()
            schedules = await loop.run_in_executor(
                None, self.api_client._find_schedule_ids_sync
            )
            
            all_schedules = []
            for schedule_id in schedules:
                schedule_data = await loop.run_in_executor(
                    None, self.api_client._get_schedule_data_sync, schedule_id
                )
                if schedule_data:
                    all_schedules.append(schedule_data)
            
            logger.info(f"Retrieved {len(all_schedules)} schedules from API")
            return all_schedules
            
        except Exception as e:
            logger.error(f"Error getting schedules from API: {e}")
            return []

    async def _get_schedule_details(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """Получить детали расписания."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.api_client._get_schedule_data_sync, schedule_id
            )
        except Exception as e:
            logger.error(f"Error getting schedule details for {schedule_id}: {e}")
            return None

    def _extract_faculties(self, schedules_data: List[Dict[str, Any]]) -> Set[Dict[str, str]]:
        """Извлечь уникальные факультеты."""
        faculties = set()
        
        for schedule in schedules_data:
            if "xlsxHeaderDto" in schedule:
                for header in schedule["xlsxHeaderDto"]:
                    if "speciality" in header:
                        speciality = header["speciality"]
                        faculty_name = self._extract_faculty_from_speciality(speciality)
                        if faculty_name:
                            faculties.add((faculty_name, self._generate_short_name(faculty_name)))
        
        return [{"name": name, "short_name": short_name} for name, short_name in faculties]

    def _extract_specialities(self, schedules_data: List[Dict[str, Any]]) -> Set[Dict[str, str]]:
        """Извлечь уникальные специальности."""
        specialities = set()
        
        for schedule in schedules_data:
            if "xlsxHeaderDto" in schedule:
                for header in schedule["xlsxHeaderDto"]:
                    if "speciality" in header:
                        speciality = header["speciality"]
                        code = self._extract_speciality_code(speciality)
                        name = self._extract_speciality_name(speciality)
                        faculty_name = self._extract_faculty_from_speciality(speciality)
                        specialities.add((code, name, faculty_name))
        
        return [{"code": code, "name": name, "faculty_name": faculty_name} 
                for code, name, faculty_name in specialities]

    def _extract_academic_years(self, schedules_data: List[Dict[str, Any]]) -> Set[str]:
        """Извлечь уникальные учебные годы."""
        years = set()
        
        for schedule in schedules_data:
            if "xlsxHeaderDto" in schedule:
                for header in schedule["xlsxHeaderDto"]:
                    if "academicYear" in header:
                        years.add(header["academicYear"])
        
        return list(years)

    def _extract_semesters(self, schedules_data: List[Dict[str, Any]]) -> Set[Dict[str, str]]:
        """Извлечь уникальные семестры."""
        semesters = set()
        
        for schedule in schedules_data:
            if "xlsxHeaderDto" in schedule:
                for header in schedule["xlsxHeaderDto"]:
                    if "semesterType" in header and "academicYear" in header:
                        semesters.add((header["semesterType"], header["academicYear"]))
        
        return [{"name": name, "academic_year": year} for name, year in semesters]

    def _extract_lesson_types(self, schedules_data: List[Dict[str, Any]]) -> Set[str]:
        """Извлечь уникальные типы занятий."""
        types = set()
        
        for schedule in schedules_data:
            if "xlsxHeaderDto" in schedule:
                for header in schedule["xlsxHeaderDto"]:
                    if "lessonTypeName" in header:
                        types.add(header["lessonTypeName"])
        
        return list(types)

    def _extract_departments(self, schedules_data: List[Dict[str, Any]]) -> Set[str]:
        """Извлечь уникальные кафедры."""
        departments = set()
        
        for schedule in schedules_data:
            if "scheduleLessonDtoList" in schedule:
                for lesson in schedule["scheduleLessonDtoList"]:
                    if "departmentName" in lesson and lesson["departmentName"]:
                        departments.add(lesson["departmentName"])
        
        return list(departments)

    def _extract_lecturers(self, schedules_data: List[Dict[str, Any]]) -> Set[Dict[str, str]]:
        """Извлечь уникальных преподавателей."""
        lecturers = set()
        
        for schedule in schedules_data:
            if "scheduleLessonDtoList" in schedule:
                for lesson in schedule["scheduleLessonDtoList"]:
                    if "lectorName" in lesson and lesson["lectorName"]:
                        department = lesson.get("departmentName", "")
                        lecturers.add((lesson["lectorName"], department))
        
        return [{"name": name, "department_name": dept} for name, dept in lecturers]

    def _extract_classrooms(self, schedules_data: List[Dict[str, Any]]) -> Set[Dict[str, str]]:
        """Извлечь уникальные аудитории."""
        classrooms = set()
        
        for schedule in schedules_data:
            if "scheduleLessonDtoList" in schedule:
                for lesson in schedule["scheduleLessonDtoList"]:
                    if "auditoryNumber" in lesson and lesson["auditoryNumber"]:
                        building = lesson.get("locationAddress", "")
                        classrooms.add((lesson["auditoryNumber"], building))
        
        return [{"number": number, "building": building} for number, building in classrooms]

    def _extract_subjects(self, schedules_data: List[Dict[str, Any]]) -> Set[str]:
        """Извлечь уникальные предметы."""
        subjects = set()
        
        for schedule in schedules_data:
            if "scheduleLessonDtoList" in schedule:
                for lesson in schedule["scheduleLessonDtoList"]:
                    if "subjectName" in lesson and lesson["subjectName"]:
                        subjects.add(lesson["subjectName"])
        
        return list(subjects)

    # Методы сохранения в БД
    async def _save_faculties(self, faculties_data: List[Dict[str, str]]) -> None:
        """Сохранить факультеты."""
        async for session in get_session():
            for faculty_data in faculties_data:
                faculty = Faculty(
                    name=faculty_data["name"],
                    short_name=faculty_data["short_name"],
                    description=f"Факультет {faculty_data['name']}"
                )
                session.add(faculty)
                self.sync_stats["faculties_created"] += 1
            
            await session.commit()

    async def _save_specialities(self, specialities_data: List[Dict[str, str]]) -> None:
        """Сохранить специальности."""
        async for session in get_session():
            for spec_data in specialities_data:
                # Находим факультет
                from sqlalchemy import select
                faculty_result = await session.execute(
                    select(Faculty).filter(Faculty.name == spec_data["faculty_name"])
                )
                faculty = faculty_result.scalar_one_or_none()
                
                if faculty:
                    # Проверяем, существует ли уже такая специальность
                    existing_spec = await session.execute(
                        select(Speciality).filter(Speciality.code == spec_data["code"])
                    )
                    existing_spec = existing_spec.scalar_one_or_none()
                    
                    if not existing_spec:
                        speciality = Speciality(
                            code=spec_data["code"],
                            name=spec_data["name"],
                            faculty_id=faculty.id
                        )
                        session.add(speciality)
                    else:
                        # Обновляем существующую
                        existing_spec.name = spec_data["name"]
                        existing_spec.faculty_id = faculty.id
                    self.sync_stats["specialities_created"] += 1
            
            await session.commit()

    async def _save_academic_years(self, years_data: List[str]) -> None:
        """Сохранить учебные годы."""
        async for session in get_session():
            for year_name in years_data:
                year = AcademicYear(
                    name=year_name,
                    is_current=year_name == "2025/2026"  # Текущий год
                )
                session.add(year)
                self.sync_stats["academic_years_created"] += 1
            
            await session.commit()

    async def _save_semesters(self, semesters_data: List[Dict[str, str]]) -> None:
        """Сохранить семестры."""
        async for session in get_session():
            for sem_data in semesters_data:
                # Находим учебный год
                from sqlalchemy import select
                year_result = await session.execute(
                    select(AcademicYear).filter(AcademicYear.name == sem_data["academic_year"])
                )
                year = year_result.scalar_one_or_none()
                
                if year:
                    semester = Semester(
                        name=sem_data["name"],
                        academic_year_id=year.id,
                        is_current=sem_data["name"] == "осенний" and year.is_current
                    )
                    session.add(semester)
                    self.sync_stats["semesters_created"] += 1
            
            await session.commit()

    async def _save_lesson_types(self, types_data: List[str]) -> None:
        """Сохранить типы занятий."""
        async for session in get_session():
            for type_name in types_data:
                lesson_type = LessonType(name=type_name)
                session.add(lesson_type)
                self.sync_stats["lesson_types_created"] += 1
            
            await session.commit()

    async def _save_departments(self, departments_data: List[str]) -> None:
        """Сохранить кафедры."""
        async for session in get_session():
            for dept_name in departments_data:
                department = Department(name=dept_name)
                session.add(department)
                self.sync_stats["departments_created"] += 1
            
            await session.commit()

    async def _save_lecturers(self, lecturers_data: List[Dict[str, str]]) -> None:
        """Сохранить преподавателей."""
        async for session in get_session():
            for lect_data in lecturers_data:
                # Находим кафедру
                from sqlalchemy import select
                dept_result = await session.execute(
                    select(Department).filter(Department.name == lect_data["department_name"])
                )
                department = dept_result.scalar_one_or_none()
                
                lecturer = Lecturer(
                    name=lect_data["name"],
                    department_id=department.id if department else None
                )
                session.add(lecturer)
                self.sync_stats["lecturers_created"] += 1
            
            await session.commit()

    async def _save_classrooms(self, classrooms_data: List[Dict[str, str]]) -> None:
        """Сохранить аудитории."""
        async for session in get_session():
            for room_data in classrooms_data:
                classroom = Classroom(
                    number=room_data["number"],
                    building=room_data["building"] or None
                )
                session.add(classroom)
                self.sync_stats["classrooms_created"] += 1
            
            await session.commit()

    async def _save_subjects(self, subjects_data: List[str]) -> None:
        """Сохранить предметы."""
        async for session in get_session():
            for subject_name in subjects_data:
                subject = Subject(name=subject_name)
                session.add(subject)
                self.sync_stats["subjects_created"] += 1
            
            await session.commit()

    async def _save_schedule(self, schedule_data: Dict[str, Any]) -> Optional[int]:
        """Сохранить расписание."""
        try:
            async for session in get_session():
                # Находим связанные записи
                from sqlalchemy import select
                speciality_result = await session.execute(
                    select(Speciality).filter(
                        Speciality.name == schedule_data.get("speciality", "")
                    )
                )
                speciality = speciality_result.scalar_one_or_none()
                
                if not speciality:
                    logger.warning(f"Speciality not found for schedule {schedule_data.get('id')}")
                    return None
                
                # Находим учебный год и семестр
                year_result = await session.execute(
                    select(AcademicYear).filter(
                        AcademicYear.name == schedule_data.get("academicYear", "")
                    )
                )
                year = year_result.scalar_one_or_none()
                
                semester_result = await session.execute(
                    select(Semester).filter(
                        Semester.name == schedule_data.get("semester", "")
                    )
                )
                semester = semester_result.scalar_one_or_none()
                
                if not year or not semester:
                    logger.warning(f"Academic year or semester not found for schedule {schedule_data.get('id')}")
                    return None
                
                # Создаем или обновляем расписание
                existing_result = await session.execute(
                    select(Schedule).filter(
                        Schedule.external_id == schedule_data.get("id")
                    )
                )
                existing = existing_result.scalar_one_or_none()
                
                if existing:
                    # Обновляем существующее
                    existing.file_name = schedule_data.get("fileName", "")
                    existing.form_type = schedule_data.get("formType", 1)
                    existing.status = schedule_data.get("statusId", "DRAFT")
                    existing.is_uploaded_from_excel = schedule_data.get("isUploadedFromExcel", False)
                    existing.update_time = datetime.now()
                    self.sync_stats["schedules_updated"] += 1
                    schedule_id = existing.id
                else:
                    # Создаем новое
                    schedule = Schedule(
                        external_id=schedule_data.get("id"),
                        file_name=schedule_data.get("fileName", ""),
                        form_type=schedule_data.get("formType", 1),
                        status=schedule_data.get("statusId", "DRAFT"),
                        is_uploaded_from_excel=schedule_data.get("isUploadedFromExcel", False),
                        update_time=datetime.now(),
                        academic_year_id=year.id,
                        semester_id=semester.id,
                        speciality_id=speciality.id
                    )
                    session.add(schedule)
                    self.sync_stats["schedules_created"] += 1
                    await session.flush()
                    schedule_id = schedule.id
                
                await session.commit()
                return schedule_id
                
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            return None

    async def _save_lessons(self, schedule_id: int, schedule_details: Dict[str, Any]) -> None:
        """Сохранить занятия."""
        if "scheduleLessonDtoList" not in schedule_details:
            return
        
        async for session in get_session():
            for lesson_data in schedule_details["scheduleLessonDtoList"]:
                # Находим связанные записи
                from sqlalchemy import select
                subject_result = await session.execute(
                    select(Subject).filter(
                        Subject.name == lesson_data.get("subjectName", "")
                    )
                )
                subject = subject_result.scalar_one_or_none()
                
                lesson_type_result = await session.execute(
                    select(LessonType).filter(
                        LessonType.name == lesson_data.get("lessonType", "")
                    )
                )
                lesson_type = lesson_type_result.scalar_one_or_none()
                
                lecturer_result = await session.execute(
                    select(Lecturer).filter(
                        Lecturer.name == lesson_data.get("lectorName", "")
                    )
                )
                lecturer = lecturer_result.scalar_one_or_none()
                
                classroom_result = await session.execute(
                    select(Classroom).filter(
                        Classroom.number == lesson_data.get("auditoryNumber", "")
                    )
                )
                classroom = classroom_result.scalar_one_or_none()
                
                department_result = await session.execute(
                    select(Department).filter(
                        Department.name == lesson_data.get("departmentName", "")
                    )
                )
                department = department_result.scalar_one_or_none()
                
                if not subject or not lesson_type:
                    continue
                
                # Парсим время
                start_time, end_time = self._parse_time(lesson_data.get("pairTime", ""))
                
                # Создаем или обновляем занятие
                existing_result = await session.execute(
                    select(Lesson).filter(
                        Lesson.external_id == lesson_data.get("id")
                    )
                )
                existing = existing_result.scalar_one_or_none()
                
                if existing:
                    # Обновляем существующее
                    existing.day_name = lesson_data.get("dayName", "")
                    existing.week_number = lesson_data.get("weekNumber", 1)
                    existing.pair_time = lesson_data.get("pairTime", "")
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.lecturer_id = lecturer.id if lecturer else None
                    existing.classroom_id = classroom.id if classroom else None
                    existing.department_id = department.id if department else None
                    existing.subgroup = lesson_data.get("subgroup", "")
                    existing.study_group = lesson_data.get("studyGroup", "")
                    self.sync_stats["lessons_updated"] += 1
                else:
                    # Создаем новое
                    lesson = Lesson(
                        external_id=lesson_data.get("id"),
                        day_name=lesson_data.get("dayName", ""),
                        week_number=lesson_data.get("weekNumber", 1),
                        pair_time=lesson_data.get("pairTime", ""),
                        start_time=start_time,
                        end_time=end_time,
                        schedule_id=schedule_id,
                        subject_id=subject.id,
                        lesson_type_id=lesson_type.id,
                        lecturer_id=lecturer.id if lecturer else None,
                        classroom_id=classroom.id if classroom else None,
                        department_id=department.id if department else None,
                        subgroup=lesson_data.get("subgroup", ""),
                        study_group=lesson_data.get("studyGroup", "")
                    )
                    session.add(lesson)
                    self.sync_stats["lessons_created"] += 1
            
            await session.commit()

    def _parse_time(self, time_str: str) -> tuple[Optional[dt_time], Optional[dt_time]]:
        """Парсить время из строки типа '9:00-10:30'."""
        try:
            if "-" in time_str:
                start_str, end_str = time_str.split("-", 1)
                start_time = dt_time.fromisoformat(start_str.strip())
                end_time = dt_time.fromisoformat(end_str.strip())
                return start_time, end_time
        except Exception:
            pass
        return None, None

    def _extract_faculty_from_speciality(self, speciality: str) -> str:
        """Извлечь название факультета из специальности."""
        if "лечебное дело" in speciality.lower():
            return "Лечебный факультет"
        elif "педиатрия" in speciality.lower():
            return "Педиатрический факультет"
        elif "медико-профилактическое дело" in speciality.lower():
            return "Медико-профилактический факультет"
        elif "стоматология" in speciality.lower():
            return "Стоматологический факультет"
        elif "фармация" in speciality.lower():
            return "Фармацевтический факультет"
        elif "сестринское дело" in speciality.lower():
            return "Факультет сестринского дела"
        elif "медицинская кибернетика" in speciality.lower():
            return "Факультет медицинской кибернетики"
        elif "управление сестринской деятельностью" in speciality.lower():
            return "Факультет управления сестринской деятельностью"
        else:
            return "Неизвестный факультет"

    def _extract_speciality_code(self, speciality: str) -> str:
        """Извлечь код специальности."""
        # Ищем паттерн типа "31.05.01"
        import re
        match = re.search(r'\d{2}\.\d{2}\.\d{2}', speciality)
        return match.group(0) if match else ""

    def _extract_speciality_name(self, speciality: str) -> str:
        """Извлечь название специальности."""
        # Убираем код и лишние слова
        import re
        name = re.sub(r'\d{2}\.\d{2}\.\d{2}', '', speciality)
        name = re.sub(r'форма обучения: очная', '', name)
        name = re.sub(r'уровень магистратуры', '', name)
        return name.strip()

    def _generate_short_name(self, full_name: str) -> str:
        """Генерировать сокращенное название факультета."""
        if "лечебный" in full_name.lower():
            return "ЛФ"
        elif "педиатрический" in full_name.lower():
            return "ПФ"
        elif "медико-профилактический" in full_name.lower():
            return "МПФ"
        elif "стоматологический" in full_name.lower():
            return "СФ"
        elif "фармацевтический" in full_name.lower():
            return "ФФ"
        elif "сестринского дела" in full_name.lower():
            return "ФСД"
        elif "медицинской кибернетики" in full_name.lower():
            return "ФМК"
        elif "управления сестринской деятельностью" in full_name.lower():
            return "ФУСД"
        else:
            words = full_name.split()
            return "".join([word[0].upper() for word in words[:2]])

    async def _log_sync_result(self, sync_type: str, status: str, duration: float, error: str = None) -> None:
        """Логировать результат синхронизации."""
        async for session in get_session():
            log = APISyncLog(
                sync_type=sync_type,
                status=status,
                records_processed=sum(self.sync_stats.values()),
                records_created=sum(v for k, v in self.sync_stats.items() if "created" in k),
                records_updated=sum(v for k, v in self.sync_stats.items() if "updated" in k),
                error_message=error,
                duration_seconds=duration
            )
            session.add(log)
            await session.commit()
