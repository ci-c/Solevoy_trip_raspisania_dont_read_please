"""Модуль для генерации заявлений на пропуски по системе СЗГМУ."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import date
from pathlib import Path
from .student_profile import StudentProfile
from .yaml_config import get_config


@dataclass 
class AbsenceRequest:
    """Запрос на создание заявления о пропуске."""
    student_profile: StudentProfile
    absence_dates: List[date]
    reason: str                    # Причина пропуска
    reason_code: str              # Код причины (illness, family, etc.)
    subjects: List[str]           # Список дисциплин для пропуска
    additional_info: Optional[str] = None  # Дополнительная информация


@dataclass
class GeneratedApplication:
    """Сгенерированное заявление."""
    filename: str
    content: str
    document_type: str           # discipline_application или explanatory_note
    recipient: str               # Кому адресовано


class ApplicationGenerator:
    """Генератор заявлений по системе СЗГМУ."""
    
    def __init__(self, templates_path: Path):
        self.templates_path = Path(templates_path)
        self.config = get_config()
    
    def generate_applications(self, request: AbsenceRequest) -> List[GeneratedApplication]:
        """
        Генерирует все необходимые заявления согласно системе СЗГМУ:
        - Отдельное заявление для каждой дисциплины
        - Одну объяснительную записку в дирекцию
        """
        applications = []
        
        # 1. Заявления по дисциплинам
        for subject in request.subjects:
            app = self._generate_discipline_application(request, subject)
            applications.append(app)
        
        # 2. Объяснительная записка в дирекцию
        explanatory = self._generate_explanatory_note(request)
        applications.append(explanatory)
        
        return applications
    
    def _generate_discipline_application(
        self, 
        request: AbsenceRequest, 
        subject: str
    ) -> GeneratedApplication:
        """Генерирует заявление по конкретной дисциплине."""
        
        # Получаем конфигурацию заявлений
        app_config = self.config.get_applications_config()
        discipline_config = app_config.get('document_types', {}).get('discipline_application', {})
        
        # Формируем содержимое заявления
        content = self._format_discipline_application(request, subject, discipline_config)
        
        # Формируем имя файла
        safe_subject = self._sanitize_filename(subject)
        filename = f"Заявление_{safe_subject}_{request.student_profile.subgroup}_{date.today().strftime('%Y-%m-%d')}.txt"
        
        return GeneratedApplication(
            filename=filename,
            content=content,
            document_type="discipline_application",
            recipient=discipline_config.get('recipients', 'На кафедру')
        )
    
    def _generate_explanatory_note(self, request: AbsenceRequest) -> GeneratedApplication:
        """Генерирует объяснительную записку в дирекцию."""
        
        app_config = self.config.get_applications_config()
        explanatory_config = app_config.get('document_types', {}).get('explanatory_note', {})
        
        content = self._format_explanatory_note(request, explanatory_config)
        
        filename = f"Объяснительная_{request.student_profile.subgroup}_{date.today().strftime('%Y-%m-%d')}.txt"
        
        return GeneratedApplication(
            filename=filename,
            content=content,
            document_type="explanatory_note", 
            recipient=explanatory_config.get('recipients', 'Дирекция института')
        )
    
    def _format_discipline_application(
        self, 
        request: AbsenceRequest, 
        subject: str,
        config: Dict
    ) -> str:
        """Форматирует текст заявления по дисциплине."""
        
        profile = request.student_profile
        dates_str = self._format_dates(request.absence_dates)
        
        content = f"""
{config.get('recipients', 'Заведующему кафедрой')}
от студента {profile.course} курса
{profile.specialty}
группы {profile.subgroup}
{profile.full_name}

ЗАЯВЛЕНИЕ

Прошу разрешить мне пропустить занятия по дисциплине "{subject}"
{dates_str}
по причине: {request.reason}.

{self._get_additional_info_text(request)}

Дата: {date.today().strftime('%d.%m.%Y')}
Подпись: ________________

ПРИМЕЧАНИЕ: Документ требует печати, подписи студента и личной подачи согласно регламенту СЗГМУ.
        """.strip()
        
        return content
    
    def _format_explanatory_note(self, request: AbsenceRequest, config: Dict) -> str:
        """Форматирует объяснительную записку."""
        
        profile = request.student_profile
        dates_str = self._format_dates(request.absence_dates)
        subjects_str = ", ".join(request.subjects)
        
        content = f"""
{config.get('recipients', 'В дирекцию института')}
от студента {profile.course} курса
{profile.specialty}
группы {profile.subgroup}
{profile.full_name}

ОБЪЯСНИТЕЛЬНАЯ ЗАПИСКА

Объясняю причины своего отсутствия на занятиях:
{dates_str}

Пропущенные дисциплины: {subjects_str}

Причина отсутствия: {request.reason}

{self._get_additional_info_text(request)}

С правилами отработки пропущенных занятий ознакомлен(а).
Обязуюсь отработать пропущенные занятия в установленный срок (в течение месяца).

Дата: {date.today().strftime('%d.%m.%Y')}
Подпись: ________________

ПРИМЕЧАНИЕ: Документ требует печати, подписи студента и личной подачи в дирекцию института.
        """.strip()
        
        return content
    
    def _format_dates(self, dates: List[date]) -> str:
        """Форматирует список дат для документа."""
        if len(dates) == 1:
            return f"{dates[0].strftime('%d.%m.%Y')}"
        elif len(dates) == 2:
            return f"{dates[0].strftime('%d.%m.%Y')} и {dates[1].strftime('%d.%m.%Y')}"
        else:
            # Группируем по непрерывным периодам
            sorted_dates = sorted(dates)
            if self._is_continuous_period(sorted_dates):
                return f"с {sorted_dates[0].strftime('%d.%m.%Y')} по {sorted_dates[-1].strftime('%d.%m.%Y')}"
            else:
                return ", ".join(d.strftime('%d.%m.%Y') for d in sorted_dates)
    
    def _is_continuous_period(self, dates: List[date]) -> bool:
        """Проверяет, являются ли даты непрерывным периодом."""
        if len(dates) <= 1:
            return True
        
        sorted_dates = sorted(dates)
        for i in range(1, len(sorted_dates)):
            diff = (sorted_dates[i] - sorted_dates[i-1]).days
            if diff > 1:
                return False
        return True
    
    def _get_additional_info_text(self, request: AbsenceRequest) -> str:
        """Получает дополнительную информацию для документа."""
        if request.additional_info:
            return f"Дополнительная информация: {request.additional_info}"
        
        # Получаем информацию о требованиях к документам
        app_config = self.config.get_applications_config()
        reason_config = app_config.get('absence_reasons', {}).get(request.reason_code, {})
        
        if reason_config.get('requires_medical_docs'):
            return "Справка о болезни будет предоставлена дополнительно."
        
        return ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """Очищает имя файла от недопустимых символов."""
        import re
        # Заменяем недопустимые символы на подчеркивания
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Убираем множественные подчеркивания
        sanitized = re.sub(r'_{2,}', '_', sanitized)
        # Обрезаем до разумной длины
        return sanitized[:50]
    
    def get_available_reasons(self) -> Dict[str, Dict]:
        """Получает доступные причины пропусков."""
        app_config = self.config.get_applications_config()
        return app_config.get('absence_reasons', {})
    
    def get_document_requirements(self) -> Dict[str, str]:
        """Получает требования к документообороту."""
        szgmu_config = self.config.get('academic_szgmu', {})
        workflow = szgmu_config.get('document_workflow', {})
        
        return {
            'format': workflow.get('document_format', 'Печатный, с подписью студента'),
            'delivery': workflow.get('delivery_method', 'Лично в дирекцию'),
            'discipline_recipient': workflow.get('discipline_application_recipient', 'На кафедру'),
            'explanatory_recipient': workflow.get('explanatory_note_recipient', 'Дирекция института')
        }