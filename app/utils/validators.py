# Copyright (c) 2024 SZGMU Bot Project

"""Система валидации данных для предотвращения runtime ошибок."""

from typing import Any, TypeVar, Generic, Callable
from dataclasses import dataclass
from enum import Enum
import re

T = TypeVar("T")


class ValidationError(Exception):
    """Ошибка валидации данных."""

    pass


class ValidationLevel(Enum):
    """Уровни валидации."""

    STRICT = "strict"  # Строгая валидация
    NORMAL = "normal"  # Обычная валидация
    LENIENT = "lenient"  # Мягкая валидация


@dataclass
class ValidationResult(Generic[T]):
    """Результат валидации."""

    is_valid: bool
    data: T | None
    errors: list[str]
    warnings: list[str]


class BaseValidator(Generic[T]):
    """Базовый валидатор."""

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self, data: Any) -> ValidationResult[T]:
        """Валидировать данные."""
        self.errors.clear()
        self.warnings.clear()

        try:
            validated_data = self._validate_impl(data)
            return ValidationResult(
                is_valid=len(self.errors) == 0,
                data=validated_data,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
            )
        except Exception as e:
            self.errors.append(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                data=None,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
            )

    def _validate_impl(self, data: Any) -> T:
        """Реализация валидации (переопределить в наследниках)."""
        raise NotImplementedError


class StringValidator(BaseValidator[str]):
    """Валидатор строк."""

    def __init__(
        self,
        min_length: int = 0,
        max_length: int | None = None,
        pattern: str | None = None,
        allow_empty: bool = True,
        level: ValidationLevel = ValidationLevel.NORMAL,
    ):
        super().__init__(level)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.allow_empty = allow_empty

    def _validate_impl(self, data: Any) -> str:
        if not isinstance(data, str):
            if self.level == ValidationLevel.STRICT:
                raise ValidationError(f"Expected string, got {type(data).__name__}")
            data = str(data)
            self.warnings.append(f"Converted {type(data).__name__} to string")

        if not self.allow_empty and not data.strip():
            raise ValidationError("Empty string not allowed")

        if len(data) < self.min_length:
            raise ValidationError(f"String too short: {len(data)} < {self.min_length}")

        if self.max_length and len(data) > self.max_length:
            if self.level == ValidationLevel.STRICT:
                raise ValidationError(
                    f"String too long: {len(data)} > {self.max_length}"
                )
            data = data[: self.max_length]
            self.warnings.append(f"String truncated to {self.max_length} characters")

        if self.pattern and not self.pattern.match(data):
            raise ValidationError(
                f"String doesn't match pattern: {self.pattern.pattern}"
            )

        return data


class IntegerValidator(BaseValidator[int]):
    """Валидатор целых чисел."""

    def __init__(
        self,
        min_value: int | None = None,
        max_value: int | None = None,
        level: ValidationLevel = ValidationLevel.NORMAL,
    ):
        super().__init__(level)
        self.min_value = min_value
        self.max_value = max_value

    def _validate_impl(self, data: Any) -> int:
        if isinstance(data, str):
            try:
                data = int(data)
            except ValueError:
                raise ValidationError(f"Cannot convert '{data}' to integer")
        elif not isinstance(data, int):
            if self.level == ValidationLevel.STRICT:
                raise ValidationError(f"Expected integer, got {type(data).__name__}")
            try:
                data = int(data)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Cannot convert {type(data).__name__} to integer"
                )

        if self.min_value is not None and data < self.min_value:
            raise ValidationError(f"Value too small: {data} < {self.min_value}")

        if self.max_value is not None and data > self.max_value:
            raise ValidationError(f"Value too large: {data} > {self.max_value}")

        return data


class DictValidator(BaseValidator[dict[str, Any]]):
    """Валидатор словарей."""

    def __init__(
        self,
        required_keys: set[str] | None = None,
        optional_keys: set[str] | None = None,
        key_validators: dict[str, BaseValidator] | None = None,
        level: ValidationLevel = ValidationLevel.NORMAL,
    ):
        super().__init__(level)
        self.required_keys = required_keys or set()
        self.optional_keys = optional_keys or set()
        self.key_validators = key_validators or {}

    def _validate_impl(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict, got {type(data).__name__}")

        # Проверяем обязательные ключи
        missing_keys = self.required_keys - set(data.keys())
        if missing_keys:
            raise ValidationError(f"Missing required keys: {missing_keys}")

        # Валидируем значения
        validated_data = {}
        for key, value in data.items():
            if key in self.key_validators:
                validator = self.key_validators[key]
                result = validator.validate(value)
                if not result.is_valid:
                    raise ValidationError(
                        f"Validation failed for key '{key}': {result.errors}"
                    )
                validated_data[key] = result.data
            else:
                validated_data[key] = value

        return validated_data


class GroupDataValidator(DictValidator):
    """Валидатор данных группы."""

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        super().__init__(
            required_keys={"id", "name", "faculty", "speciality", "course"},
            key_validators={
                "id": StringValidator(min_length=1, pattern=r"^\d+$"),
                "name": StringValidator(min_length=1, max_length=50),
                "faculty": StringValidator(min_length=1, max_length=100),
                "speciality": StringValidator(min_length=1, max_length=100),
                "course": StringValidator(min_length=1, max_length=2, pattern=r"^\d+$"),
            },
            level=level,
        )


class UserDataValidator(DictValidator):
    """Валидатор данных пользователя."""

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        super().__init__(
            required_keys={"telegram_id"},
            optional_keys={"group_id", "subscription_type"},
            key_validators={
                "telegram_id": IntegerValidator(min_value=1),
                "group_id": IntegerValidator(min_value=1),
                "subscription_type": StringValidator(
                    pattern=r"^(free|standard|premium)$"
                ),
            },
            level=level,
        )


def safe_execute(
    func: Callable[..., T],
    *args,
    default: T | None = None,
    error_message: str = "Operation failed",
    **kwargs,
) -> T | None:
    """Безопасное выполнение функции с обработкой ошибок."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        from app.utils.logger import logger

        logger.error(f"{error_message}: {e}")
        return default


def validate_group_data(data: Any) -> ValidationResult[dict[str, str]]:
    """Валидировать данные группы."""
    validator = GroupDataValidator()
    return validator.validate(data)


def validate_user_data(data: Any) -> ValidationResult[dict[str, Any]]:
    """Валидировать данные пользователя."""
    validator = UserDataValidator()
    return validator.validate(data)
