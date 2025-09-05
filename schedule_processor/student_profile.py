"""Модуль для работы с профилями студентов."""

from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
import json


@dataclass
class StudentProfile:
    """Профиль студента с персональными данными."""
    
    # Персональные данные
    full_name: str                    # ФИО полностью
    telegram_user_id: int            # ID пользователя в Telegram
    
    # Учебная информация  
    specialty: str                    # Специальность (31.05.01 лечебное дело)
    course: int                      # Курс (1-6)
    stream: str                      # Поток (а, б, в, г)  
    group: str                       # Группа (например, 201)
    subgroup: str                    # Подгруппа (201а)
    academic_year: str               # Учебный год (2024/2025)
    semester: str                    # Семестр (осенний/весенний)
    
    # Настройки уведомлений
    notifications_enabled: bool = True
    remind_before_class: int = 30    # минут до занятия
    daily_schedule_time: str = "20:00"  # время ежедневного напоминания
    
    # Дополнительные данные
    preferred_format: str = "xlsx"   # Предпочитаемый формат файлов
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StudentProfileManager:
    """Менеджер для работы с профилями студентов."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def get_profile_file(self, user_id: int) -> Path:
        """Получить путь к файлу профиля."""
        return self.storage_path / f"profile_{user_id}.json"
    
    def load_profile(self, user_id: int) -> Optional[StudentProfile]:
        """Загрузить профиль студента."""
        profile_file = self.get_profile_file(user_id)
        
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return StudentProfile(**data)
        except Exception:
            return None
    
    def save_profile(self, profile: StudentProfile) -> bool:
        """Сохранить профиль студента."""
        profile_file = self.get_profile_file(profile.telegram_user_id)
        
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def delete_profile(self, user_id: int) -> bool:
        """Удалить профиль студента."""
        profile_file = self.get_profile_file(user_id)
        
        try:
            if profile_file.exists():
                profile_file.unlink()
            return True
        except Exception:
            return False
    
    def get_group_display_name(self, profile: StudentProfile) -> str:
        """Получить красивое отображение группы."""
        return f"{profile.subgroup} ({profile.course} курс, {profile.specialty[:20]})"
    
    def is_profile_complete(self, profile: StudentProfile) -> bool:
        """Проверить, заполнен ли профиль полностью."""
        required_fields = [
            profile.full_name, profile.specialty, profile.course,
            profile.stream, profile.group, profile.subgroup
        ]
        return all(field for field in required_fields)