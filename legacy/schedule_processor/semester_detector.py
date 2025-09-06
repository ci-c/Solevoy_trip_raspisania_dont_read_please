"""
Модуль для автоматического определения текущего семестра и учебного года.
"""

from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class SemesterInfo:
    """Информация о семестре."""
    name: str  # "осенний" или "весенний"
    year: str  # "2024/2025"
    start_date: date
    end_date: date
    current_week: int


class SemesterDetector:
    """Детектор текущего семестра и учебного года."""
    
    def get_current_semester_info(self) -> SemesterInfo:
        """Получить информацию о текущем семестре."""
        now = datetime.now()
        
        # Осенний семестр: сентябрь-январь
        if 9 <= now.month <= 12:
            return self._get_autumn_semester_info(now.year)
        elif now.month == 1:
            return self._get_autumn_semester_info(now.year - 1)
        
        # Весенний семестр: февраль-июнь
        elif 2 <= now.month <= 6:
            return self._get_spring_semester_info(now.year)
        
        # Каникулы: июль-август - показываем следующий семестр
        else:
            return self._get_next_semester_during_vacation(now)
    
    def _get_autumn_semester_info(self, start_year: int) -> SemesterInfo:
        """Информация об осеннем семестре."""
        year_str = f"{start_year}/{start_year + 1}"
        
        # Начало - первый понедельник сентября
        start_date = self._get_first_monday_of_month(start_year, 9)
        
        # Конец - конец декабря
        end_date = date(start_year, 12, 31)
        
        current_week = self._calculate_current_week(start_date)
        
        return SemesterInfo(
            name="осенний",
            year=year_str,
            start_date=start_date,
            end_date=end_date,
            current_week=current_week
        )
    
    def _get_spring_semester_info(self, year: int) -> SemesterInfo:
        """Информация о весеннем семестре."""
        year_str = f"{year - 1}/{year}"
        
        # Начало - первый понедельник февраля
        start_date = self._get_first_monday_of_month(year, 2)
        
        # Конец - конец июня
        end_date = date(year, 6, 30)
        
        current_week = self._calculate_current_week(start_date)
        
        return SemesterInfo(
            name="весенний",
            year=year_str,
            start_date=start_date,
            end_date=end_date,
            current_week=current_week
        )
    
    def _get_next_semester_during_vacation(self, now: datetime) -> SemesterInfo:
        """Получить информацию о следующем семестре во время каникул."""
        # Во время летних каникул показываем осенний семестр
        return self._get_autumn_semester_info(now.year)
    
    def _get_first_monday_of_month(self, year: int, month: int) -> date:
        """Найти первый понедельник месяца."""
        # Начинаем с первого числа
        first_day = date(year, month, 1)
        
        # Если первое число не понедельник, ищем ближайший понедельник
        days_until_monday = (7 - first_day.weekday()) % 7
        if first_day.weekday() != 0:  # 0 = понедельник
            days_until_monday = 7 - first_day.weekday()
        
        return date(year, month, 1 + days_until_monday)
    
    def _calculate_current_week(self, semester_start: date) -> int:
        """Вычислить номер текущей учебной недели."""
        today = date.today()
        
        if today < semester_start:
            return 1
        
        days_passed = (today - semester_start).days
        week_number = (days_passed // 7) + 1
        
        # Ограничиваем 20 неделями (максимум для семестра)
        return min(week_number, 20)
    
    def is_current_semester(self, semester_name: str, academic_year: str) -> bool:
        """Проверить, является ли семестр текущим."""
        current = self.get_current_semester_info()
        return current.name == semester_name and current.year == academic_year
    
    def get_semester_display_text(self) -> str:
        """Получить текст для отображения текущего семестра."""
        info = self.get_current_semester_info()
        
        return f"{info.name.title()} семестр {info.year} | Неделя {info.current_week}"
    
    def get_priority_filters(self) -> dict:
        """Получить приоритетные фильтры для поиска актуальных расписаний."""
        info = self.get_current_semester_info()
        
        return {
            "semester": info.name,
            "academicYear": info.year
        }