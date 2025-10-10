#!/usr/bin/env python3
"""
Скрипт для создания групп из занятий.
"""

import asyncio
from sqlalchemy import select
from app.database.session import get_session
from app.database.models import ScheduleLesson, Group, Faculty, Speciality, Schedule


async def create_groups_from_lessons():
    """Создать группы из занятий."""
    print("Создание групп из занятий...")

    async for session in get_session():
        # Получаем уникальные группы из занятий
        result = await session.execute(
            select(
                ScheduleLesson.study_group,
                ScheduleLesson.subgroup,
                ScheduleLesson.schedule_id,
            )
            .where(ScheduleLesson.study_group.isnot(None))
            .distinct()
        )

        lessons = result.all()
        print(f"Найдено {len(lessons)} уникальных групп в занятиях")

        groups_created = 0

        for lesson in lessons:
            study_group = lesson.study_group
            subgroup = lesson.subgroup
            schedule_id = lesson.schedule_id

            # Проверяем, существует ли уже группа
            existing_group = await session.execute(
                select(Group).where(Group.name == study_group)
            )

            if existing_group.scalar_one_or_none():
                continue  # Группа уже существует

            # Получаем информацию о расписании
            schedule_result = await session.execute(
                select(Schedule).where(Schedule.id == schedule_id)
            )
            schedule = schedule_result.scalar_one_or_none()

            if not schedule:
                print(f"Расписание {schedule_id} не найдено")
                continue

            # Получаем специальность
            speciality_result = await session.execute(
                select(Speciality).where(Speciality.id == schedule.speciality_id)
            )
            speciality = speciality_result.scalar_one_or_none()

            if not speciality:
                print(f"Специальность для расписания {schedule_id} не найдена")
                continue

            # Получаем факультет
            faculty_result = await session.execute(
                select(Faculty).where(Faculty.id == speciality.faculty_id)
            )
            faculty = faculty_result.scalar_one_or_none()

            if not faculty:
                print(f"Факультет для специальности {speciality.id} не найден")
                continue

            # Извлекаем номер курса из названия группы
            course = 1
            if study_group and study_group[0].isdigit():
                course = int(study_group[0])

            # Создаем группу
            group = Group(
                name=study_group,
                course=course,
                faculty_id=faculty.id,
                speciality_id=speciality.id,
                faculty=faculty.name,  # Legacy поле
                speciality=speciality.name,  # Legacy поле
            )

            session.add(group)
            groups_created += 1

            print(
                f"Создана группа: {study_group} (курс {course}, {faculty.name}, {speciality.name})"
            )

        await session.commit()
        print(f"Создано {groups_created} групп")


if __name__ == "__main__":
    asyncio.run(create_groups_from_lessons())
