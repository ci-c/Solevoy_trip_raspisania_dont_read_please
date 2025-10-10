"""
Модуль для расчета академических показателей СЗГМУ.
Расчет ОСБ, ТСБ, КНЛ, КНС согласно новым регламентам.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path


@dataclass
class Grade:
    """Оценка за контрольную точку."""

    subject: str
    grade: int  # 2, 3, 4, 5
    date: date
    control_point_name: str


@dataclass
class Attendance:
    """Запись о посещаемости."""

    subject: str
    date: date
    lesson_type: str  # "lecture" or "seminar"
    is_present: bool
    is_excused: bool = False  # Уважительная причина


@dataclass
class SubjectStats:
    """Статистика по предмету."""

    subject_name: str
    grades: List[Grade]
    lecture_attendance: List[Attendance]
    seminar_attendance: List[Attendance]
    tsb: float  # Текущий средний балл
    knl: float  # Коэффициент непосещаемости лекций
    kns: float  # Коэффициент непосещаемости семинаров
    osb: float  # Общий средний балл


class GradeCalculator:
    """Калькулятор академических показателей."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.data_dir = Path(__file__).parent.parent / "user_data" / user_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.grades_file = self.data_dir / "grades.json"
        self.attendance_file = self.data_dir / "attendance.json"

        self._load_data()

    def _load_data(self) -> None:
        """Загрузка данных из файлов."""
        self.grades: List[Grade] = []
        self.attendance: List[Attendance] = []

        # Загрузка оценок
        if self.grades_file.exists():
            try:
                with open(self.grades_file, "r", encoding="utf-8") as f:
                    grades_data = json.load(f)
                    for grade_dict in grades_data:
                        grade = Grade(
                            subject=grade_dict["subject"],
                            grade=grade_dict["grade"],
                            date=date.fromisoformat(grade_dict["date"]),
                            control_point_name=grade_dict["control_point_name"],
                        )
                        self.grades.append(grade)
            except Exception:
                self.grades = []

        # Загрузка посещаемости
        if self.attendance_file.exists():
            try:
                with open(self.attendance_file, "r", encoding="utf-8") as f:
                    attendance_data = json.load(f)
                    for att_dict in attendance_data:
                        attendance = Attendance(
                            subject=att_dict["subject"],
                            date=date.fromisoformat(att_dict["date"]),
                            lesson_type=att_dict["lesson_type"],
                            is_present=att_dict["is_present"],
                            is_excused=att_dict.get("is_excused", False),
                        )
                        self.attendance.append(attendance)
            except Exception:
                self.attendance = []

    def _save_data(self) -> None:
        """Сохранение данных в файлы."""
        # Сохранение оценок
        grades_data = []
        for grade in self.grades:
            grades_data.append(
                {
                    "subject": grade.subject,
                    "grade": grade.grade,
                    "date": grade.date.isoformat(),
                    "control_point_name": grade.control_point_name,
                }
            )

        with open(self.grades_file, "w", encoding="utf-8") as f:
            json.dump(grades_data, f, ensure_ascii=False, indent=2)

        # Сохранение посещаемости
        attendance_data = []
        for att in self.attendance:
            attendance_data.append(
                {
                    "subject": att.subject,
                    "date": att.date.isoformat(),
                    "lesson_type": att.lesson_type,
                    "is_present": att.is_present,
                    "is_excused": att.is_excused,
                }
            )

        with open(self.attendance_file, "w", encoding="utf-8") as f:
            json.dump(attendance_data, f, ensure_ascii=False, indent=2)

    def add_grade(
        self,
        subject: str,
        grade: int,
        control_point_name: str,
        grade_date: Optional[date] = None,
    ) -> None:
        """Добавить оценку."""
        if grade_date is None:
            grade_date = date.today()

        new_grade = Grade(
            subject=subject,
            grade=grade,
            date=grade_date,
            control_point_name=control_point_name,
        )

        self.grades.append(new_grade)
        self._save_data()

    def add_attendance(
        self,
        subject: str,
        lesson_type: str,
        is_present: bool,
        is_excused: bool = False,
        attendance_date: Optional[date] = None,
    ) -> None:
        """Добавить запись о посещаемости."""
        if attendance_date is None:
            attendance_date = date.today()

        new_attendance = Attendance(
            subject=subject,
            date=attendance_date,
            lesson_type=lesson_type,
            is_present=is_present,
            is_excused=is_excused,
        )

        self.attendance.append(new_attendance)
        self._save_data()

    def calculate_tsb(self, subject: str) -> float:
        """Рассчитать текущий средний балл по предмету."""
        subject_grades = [g for g in self.grades if g.subject == subject]

        if not subject_grades:
            return 0.0

        total = sum(g.grade for g in subject_grades)
        return round(total / len(subject_grades), 2)

    def calculate_knl(self, subject: str) -> float:
        """Рассчитать коэффициент непосещаемости лекций."""
        lectures = [
            a
            for a in self.attendance
            if a.subject == subject and a.lesson_type == "lecture"
        ]

        if not lectures:
            return 0.0

        # Считаем только пропуски без уважительной причины
        unexcused_absences = len(
            [a for a in lectures if not a.is_present and not a.is_excused]
        )
        total_lectures = len(lectures)

        # КНЛ от 0 (идеальная посещаемость) до -1 (100% пропусков)
        absence_ratio = unexcused_absences / total_lectures
        return round(-absence_ratio, 2)

    def calculate_kns(self, subject: str) -> float:
        """Рассчитать коэффициент непосещаемости семинаров."""
        seminars = [
            a
            for a in self.attendance
            if a.subject == subject and a.lesson_type == "seminar"
        ]

        if not seminars:
            return 0.0

        # Считаем только пропуски без уважительной причины
        unexcused_absences = len(
            [a for a in seminars if not a.is_present and not a.is_excused]
        )
        total_seminars = len(seminars)

        # КНС от 0 (идеальная посещаемость) до -1 (100% пропусков)
        absence_ratio = unexcused_absences / total_seminars
        return round(-absence_ratio, 2)

    def calculate_osb(self, subject: str) -> float:
        """Рассчитать общий средний балл: ОСБ = ТСБ + КНЛ + КНС."""
        tsb = self.calculate_tsb(subject)
        knl = self.calculate_knl(subject)
        kns = self.calculate_kns(subject)

        osb = tsb + knl + kns
        return round(osb, 2)

    def get_subject_stats(self, subject: str) -> SubjectStats:
        """Получить полную статистику по предмету."""
        subject_grades = [g for g in self.grades if g.subject == subject]
        lectures = [
            a
            for a in self.attendance
            if a.subject == subject and a.lesson_type == "lecture"
        ]
        seminars = [
            a
            for a in self.attendance
            if a.subject == subject and a.lesson_type == "seminar"
        ]

        tsb = self.calculate_tsb(subject)
        knl = self.calculate_knl(subject)
        kns = self.calculate_kns(subject)
        osb = self.calculate_osb(subject)

        return SubjectStats(
            subject_name=subject,
            grades=subject_grades,
            lecture_attendance=lectures,
            seminar_attendance=seminars,
            tsb=tsb,
            knl=knl,
            kns=kns,
            osb=osb,
        )

    def get_all_subjects(self) -> List[str]:
        """Получить список всех предметов."""
        subjects = set()

        for grade in self.grades:
            subjects.add(grade.subject)

        for att in self.attendance:
            subjects.add(att.subject)

        return sorted(list(subjects))

    def get_overall_stats(self) -> Dict[str, float]:
        """Получить общую статистику по всем предметам."""
        subjects = self.get_all_subjects()

        if not subjects:
            return {
                "average_tsb": 0.0,
                "average_knl": 0.0,
                "average_kns": 0.0,
                "average_osb": 0.0,
                "total_grades": 0,
                "total_subjects": 0,
            }

        total_tsb = sum(self.calculate_tsb(subject) for subject in subjects)
        total_knl = sum(self.calculate_knl(subject) for subject in subjects)
        total_kns = sum(self.calculate_kns(subject) for subject in subjects)
        total_osb = sum(self.calculate_osb(subject) for subject in subjects)

        return {
            "average_tsb": round(total_tsb / len(subjects), 2),
            "average_knl": round(total_knl / len(subjects), 2),
            "average_kns": round(total_kns / len(subjects), 2),
            "average_osb": round(total_osb / len(subjects), 2),
            "total_grades": len(self.grades),
            "total_subjects": len(subjects),
        }

    def format_subject_report(self, subject: str) -> str:
        """Форматированный отчет по предмету."""
        stats = self.get_subject_stats(subject)

        report = f"📚 **{subject}**\n\n"
        report += "📊 **Показатели:**\n"
        report += f"• ТСБ (средний балл): {stats.tsb}\n"
        report += f"• КНЛ (лекции): {stats.knl}\n"
        report += f"• КНС (семинары): {stats.kns}\n"
        report += f"• **ОСБ (общий балл): {stats.osb}**\n\n"

        if stats.grades:
            report += f"🎯 **Оценки ({len(stats.grades)}):**\n"
            for grade in sorted(stats.grades, key=lambda x: x.date, reverse=True)[:5]:
                report += f"• {grade.control_point_name}: {grade.grade} ({grade.date.strftime('%d.%m')})\n"
            if len(stats.grades) > 5:
                report += f"• ... еще {len(stats.grades) - 5} оценок\n"
            report += "\n"

        lecture_count = len(stats.lecture_attendance)
        seminar_count = len(stats.seminar_attendance)

        if lecture_count > 0:
            present_lectures = len(
                [a for a in stats.lecture_attendance if a.is_present]
            )
            report += f"🎓 **Лекции:** {present_lectures}/{lecture_count} посещено\n"

        if seminar_count > 0:
            present_seminars = len(
                [a for a in stats.seminar_attendance if a.is_present]
            )
            report += f"📝 **Семинары:** {present_seminars}/{seminar_count} посещено\n"

        return report
