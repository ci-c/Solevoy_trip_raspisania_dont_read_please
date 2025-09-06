"""Модуль для ведения студенческого дневника (оценки, ДЗ, пропуски)."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime
from pathlib import Path
import json
from enum import Enum


class GradeType(Enum):
    """Типы оценок."""
    EXAM = "exam"           # Экзамен
    TEST = "test"           # Зачет
    CONTROL = "control"     # Контрольная
    LAB = "lab"             # Лабораторная
    ORAL = "oral"           # Устный ответ
    ESSAY = "essay"         # Реферат
    HOMEWORK = "homework"   # Домашнее задание


@dataclass
class Grade:
    """Оценка по предмету."""
    subject: str                    # Название предмета
    grade: int                     # Оценка (2-5)
    grade_type: GradeType          # Тип работы
    date: date                     # Дата получения оценки
    teacher: Optional[str] = None  # Преподаватель
    notes: Optional[str] = None    # Заметки


@dataclass
class Homework:
    """Домашнее задание."""
    subject: str                   # Предмет
    description: str               # Описание задания
    due_date: date                # Дата сдачи
    created_date: date            # Дата создания записи
    completed: bool = False       # Выполнено ли
    completed_date: Optional[date] = None  # Дата выполнения
    notes: Optional[str] = None   # Заметки


@dataclass
class Absence:
    """Пропуск занятия."""
    subject: str                  # Предмет
    lesson_type: str             # Тип занятия (лекция/семинар)
    absence_date: date           # Дата пропуска
    reason: Optional[str] = None # Причина пропуска
    excused: bool = False        # Уважительная причина
    made_up: bool = False        # Отработано ли
    makeup_date: Optional[date] = None  # Дата отработки
    affects_knl: bool = False    # Влияет ли на КНЛ
    affects_kns: bool = False    # Влияет ли на КНС


@dataclass
class SubjectStats:
    """Статистика по предмету."""
    subject: str
    grades: List[Grade]
    homeworks: List[Homework]
    absences: List[Absence]
    
    @property
    def average_grade(self) -> float:
        """Средний балл по предмету."""
        if not self.grades:
            return 0.0
        return sum(g.grade for g in self.grades) / len(self.grades)
    
    @property
    def pending_homework_count(self) -> int:
        """Количество невыполненных ДЗ."""
        return sum(1 for hw in self.homeworks if not hw.completed)
    
    @property
    def total_absences(self) -> int:
        """Общее количество пропусков."""
        return len(self.absences)
    
    @property
    def unexcused_absences(self) -> int:
        """Количество неуважительных пропусков."""
        return sum(1 for a in self.absences if not a.excused)


class StudentDiary:
    """Студенческий дневник."""
    
    def __init__(self, user_id: int, storage_path: Path):
        self.user_id = user_id
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.grades: List[Grade] = []
        self.homeworks: List[Homework] = []
        self.absences: List[Absence] = []
        self.load_data()
    
    def get_diary_file(self) -> Path:
        """Получить путь к файлу дневника."""
        return self.storage_path / f"diary_{self.user_id}.json"
    
    def load_data(self) -> None:
        """Загрузить данные из файла."""
        diary_file = self.get_diary_file()
        
        if not diary_file.exists():
            return
        
        try:
            with open(diary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загрузка оценок
            self.grades = [
                Grade(
                    subject=g['subject'],
                    grade=g['grade'],
                    grade_type=GradeType(g['grade_type']),
                    date=datetime.fromisoformat(g['date']).date(),
                    teacher=g.get('teacher'),
                    notes=g.get('notes')
                )
                for g in data.get('grades', [])
            ]
            
            # Загрузка ДЗ
            self.homeworks = [
                Homework(
                    subject=hw['subject'],
                    description=hw['description'],
                    due_date=datetime.fromisoformat(hw['due_date']).date(),
                    created_date=datetime.fromisoformat(hw['created_date']).date(),
                    completed=hw.get('completed', False),
                    completed_date=datetime.fromisoformat(hw['completed_date']).date() if hw.get('completed_date') else None,
                    notes=hw.get('notes')
                )
                for hw in data.get('homeworks', [])
            ]
            
            # Загрузка пропусков
            self.absences = [
                Absence(
                    subject=a['subject'],
                    lesson_type=a['lesson_type'],
                    absence_date=datetime.fromisoformat(a['absence_date']).date(),
                    reason=a.get('reason'),
                    excused=a.get('excused', False),
                    made_up=a.get('made_up', False),
                    makeup_date=datetime.fromisoformat(a['makeup_date']).date() if a.get('makeup_date') else None,
                    affects_knl=a.get('affects_knl', False),
                    affects_kns=a.get('affects_kns', False)
                )
                for a in data.get('absences', [])
            ]
            
        except Exception:
            # Если ошибка загрузки, начинаем с пустых данных
            self.grades = []
            self.homeworks = []
            self.absences = []
    
    def save_data(self) -> bool:
        """Сохранить данные в файл."""
        diary_file = self.get_diary_file()
        
        try:
            data = {
                'grades': [
                    {
                        'subject': g.subject,
                        'grade': g.grade,
                        'grade_type': g.grade_type.value,
                        'date': g.date.isoformat(),
                        'teacher': g.teacher,
                        'notes': g.notes
                    }
                    for g in self.grades
                ],
                'homeworks': [
                    {
                        'subject': hw.subject,
                        'description': hw.description,
                        'due_date': hw.due_date.isoformat(),
                        'created_date': hw.created_date.isoformat(),
                        'completed': hw.completed,
                        'completed_date': hw.completed_date.isoformat() if hw.completed_date else None,
                        'notes': hw.notes
                    }
                    for hw in self.homeworks
                ],
                'absences': [
                    {
                        'subject': a.subject,
                        'lesson_type': a.lesson_type,
                        'absence_date': a.absence_date.isoformat(),
                        'reason': a.reason,
                        'excused': a.excused,
                        'made_up': a.made_up,
                        'makeup_date': a.makeup_date.isoformat() if a.makeup_date else None,
                        'affects_knl': a.affects_knl,
                        'affects_kns': a.affects_kns
                    }
                    for a in self.absences
                ]
            }
            
            with open(diary_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
            
        except Exception:
            return False
    
    def add_grade(self, grade: Grade) -> bool:
        """Добавить оценку."""
        self.grades.append(grade)
        return self.save_data()
    
    def add_homework(self, homework: Homework) -> bool:
        """Добавить ДЗ."""
        self.homeworks.append(homework)
        return self.save_data()
    
    def add_absence(self, absence: Absence) -> bool:
        """Добавить пропуск."""
        self.absences.append(absence)
        return self.save_data()
    
    def get_subject_stats(self, subject: str) -> SubjectStats:
        """Получить статистику по предмету."""
        subject_grades = [g for g in self.grades if g.subject == subject]
        subject_homeworks = [hw for hw in self.homeworks if hw.subject == subject]
        subject_absences = [a for a in self.absences if a.subject == subject]
        
        return SubjectStats(
            subject=subject,
            grades=subject_grades,
            homeworks=subject_homeworks,
            absences=subject_absences
        )
    
    def get_all_subjects(self) -> List[str]:
        """Получить список всех предметов."""
        subjects = set()
        subjects.update(g.subject for g in self.grades)
        subjects.update(hw.subject for hw in self.homeworks)
        subjects.update(a.subject for a in self.absences)
        return sorted(subjects)
    
    def get_pending_homeworks(self) -> List[Homework]:
        """Получить невыполненные ДЗ."""
        return [hw for hw in self.homeworks if not hw.completed]
    
    def get_overdue_homeworks(self) -> List[Homework]:
        """Получить просроченные ДЗ."""
        today = date.today()
        return [hw for hw in self.homeworks if not hw.completed and hw.due_date < today]
    
    def get_upcoming_homeworks(self, days: int = 7) -> List[Homework]:
        """Получить ДЗ на ближайшие дни."""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=days)
        return [
            hw for hw in self.homeworks 
            if not hw.completed and hw.due_date <= future_date
        ]