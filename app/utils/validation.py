"""Утилиты для валидации пользовательского ввода."""

import re

from loguru import logger


class ValidationError(Exception):
    """Ошибка валидации."""



class InputValidator:
    """Валидатор пользовательского ввода."""

    # Регулярные выражения для валидации
    TELEGRAM_USERNAME_PATTERN = re.compile(r"^@?[a-zA-Z0-9_]{5,32}$")
    GROUP_NUMBER_PATTERN = re.compile(r"^[0-9]{1,3}[а-яА-Я]?$")
    STUDENT_ID_PATTERN = re.compile(r"^[0-9]{6,8}$")
    PHONE_PATTERN = re.compile(r"^\+?[1-9][0-9]{10,14}$")

    # Максимальные длины
    MAX_MESSAGE_LENGTH = 4096
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500

    @classmethod
    def validate_telegram_username(cls, username: str) -> bool:
        """Валидация Telegram username."""
        if not username:
            return False
        return bool(cls.TELEGRAM_USERNAME_PATTERN.match(username))

    @classmethod
    def validate_group_number(cls, group_number: str) -> bool:
        """Валидация номера группы."""
        if not group_number:
            return False
        return bool(cls.GROUP_NUMBER_PATTERN.match(group_number))

    @classmethod
    def validate_student_id(cls, student_id: str) -> bool:
        """Валидация студенческого билета."""
        if not student_id:
            return False
        return bool(cls.STUDENT_ID_PATTERN.match(student_id))

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Валидация номера телефона."""
        if not phone:
            return False
        return bool(cls.PHONE_PATTERN.match(phone))

    @classmethod
    def validate_message_length(cls, message: str) -> bool:
        """Валидация длины сообщения."""
        return len(message) <= cls.MAX_MESSAGE_LENGTH

    @classmethod
    def validate_name(cls, name: str) -> bool:
        """Валидация имени."""
        if not name or len(name.strip()) == 0:
            return False
        return len(name.strip()) <= cls.MAX_NAME_LENGTH

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Санитизация пользовательского ввода."""
        if not text:
            return ""

        # Удаляем потенциально опасные символы
        sanitized = re.sub(r'[<>"\']', "", text)

        # Ограничиваем длину
        if len(sanitized) > cls.MAX_MESSAGE_LENGTH:
            sanitized = sanitized[: cls.MAX_MESSAGE_LENGTH]

        return sanitized.strip()

    @classmethod
    def validate_search_query(cls, query: str) -> bool:
        """Валидация поискового запроса."""
        if not query or len(query.strip()) < 2:
            return False

        # Проверяем на подозрительные паттерны
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"data:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
        ]

        query_lower = query.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_lower):
                logger.warning(f"Suspicious search query detected: {query}")
                return False

        return True

    @classmethod
    def validate_filters(cls, filters: dict[str, str]) -> bool:
        """Валидация фильтров поиска."""
        if not isinstance(filters, dict):
            return False

        # Разрешенные ключи фильтров
        allowed_keys = {
            "course",
            "speciality",
            "stream",
            "semester",
            "group_number",
            "teacher",
            "subject",
            "room",
        }

        for key in filters:
            if key not in allowed_keys:
                logger.warning(f"Unknown filter key: {key}")
                return False

        return True


def validate_user_input(input_type: str, value: str, required: bool = True) -> str:
    """Валидация пользовательского ввода.

    Args:
        input_type: Тип ввода (username, group_number, etc.)
        value: Значение для валидации
        required: Обязательное ли поле

    Returns:
        Санитизированное значение

    Raises:
        ValidationError: При ошибке валидации

    """
    if not value and required:
        msg = f"Поле {input_type} обязательно для заполнения"
        raise ValidationError(msg)

    if not value and not required:
        return ""

    # Для поисковых запросов проверяем на подозрительные паттерны ДО санитизации
    if input_type == "search_query":
        if not InputValidator.validate_search_query(value):
            msg = "Некорректный поисковый запрос"
            raise ValidationError(msg)

    # Санитизация
    sanitized_value = InputValidator.sanitize_input(value)

    # Валидация по типу
    if input_type == "username":
        if not InputValidator.validate_telegram_username(sanitized_value):
            msg = "Некорректный формат username"
            raise ValidationError(msg)

    elif input_type == "group_number":
        if not InputValidator.validate_group_number(sanitized_value):
            msg = "Некорректный формат номера группы"
            raise ValidationError(msg)

    elif input_type == "student_id":
        if not InputValidator.validate_student_id(sanitized_value):
            msg = "Некорректный формат студенческого билета"
            raise ValidationError(msg)

    elif input_type == "phone":
        if not InputValidator.validate_phone(sanitized_value):
            msg = "Некорректный формат номера телефона"
            raise ValidationError(msg)

    elif input_type == "name":
        if not InputValidator.validate_name(sanitized_value):
            msg = "Некорректный формат имени"
            raise ValidationError(msg)

    # search_query is already validated before sanitization
    # so we don't need to validate it again here

    return sanitized_value


def validate_message(message: str) -> str:
    """Валидация сообщения пользователя."""
    if not message:
        msg = "Сообщение не может быть пустым"
        raise ValidationError(msg)

    if not InputValidator.validate_message_length(message):
        msg = "Сообщение слишком длинное"
        raise ValidationError(msg)

    return InputValidator.sanitize_input(message)
